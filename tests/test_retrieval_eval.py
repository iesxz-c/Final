"""retrieval_eval tests: metrics, text builder, hybrid, benchmark loading.

Synthetic fixtures only - never the real 155 corpus, never real judgments."""

import json
import tempfile
import unittest
from pathlib import Path

from src.pipeline import retrieval_eval as E


def _record(eid="v:f0"):
    return {"evidence_id": eid, "video_id": "anomaly/X/x.mp4",
            "start_time": 0.0, "end_time": 2.0,
            "object_evidence": [
                {"class_name": "Person", "confidence": 0.9,
                 "detection_id": "d0", "observation_id": "o0",
                 "timestamp_seconds": 0.0}],
            "generic_action_evidence": [
                {"label": "Running", "confidence": 0.7,
                 "observation_id": "a0", "source_reference": "a0",
                 "top_k": [{"label": "Jogging", "confidence": 0.2}]}],
            "surveillance_event_evidence": [
                {"label": "Fighting", "confidence": 0.8,
                 "observation_id": "e0", "source_reference": "e0",
                 "top_k": [{"label": "Assault", "confidence": 0.1}]}],
            "source_references": ["anomaly/X/x.mp4@t=0.0s-2.0s"],
            "anomaly_score": 0.5}


def _hits(*eids):
    return [E.RetrievalResult(evidence_id=e, rank=i, score=1.0 / i,
                              retrieval_method="lexical")
            for i, e in enumerate(eids, 1)]


class MetricTest(unittest.TestCase):
    def test_recall_at_5_known_answer(self):
        retrieved = ["a", "b", "c", "d", "e", "f"]
        self.assertAlmostEqual(E.recall_at_k(retrieved, ["b", "f", "z"], 5), 1 / 3)

    def test_recall_at_10_known_answer(self):
        retrieved = ["a", "b", "c"]
        self.assertAlmostEqual(E.recall_at_k(retrieved, ["b", "c", "z"], 10), 2 / 3)

    def test_mrr_known_answer(self):
        self.assertAlmostEqual(E.mrr(["a", "b", "c"], ["b", "c"]), 1 / 2)

    def test_first_relevant_determines_mrr(self):
        self.assertEqual(E.mrr(["z", "a", "b"], ["a", "b"]), 1 / 2)
        self.assertEqual(E.mrr(["a", "b"], ["a", "b"]), 1.0)

    def test_no_relevant_result_mrr_zero(self):
        self.assertEqual(E.mrr(["a", "b"], ["z"]), 0.0)
        self.assertEqual(E.mrr([], ["z"]), 0.0)

    def test_fewer_than_k_results(self):
        self.assertAlmostEqual(E.recall_at_k(["a"], ["a", "b"], 10), 1 / 2)

    def test_empty_retrieval(self):
        self.assertEqual(E.recall_at_k([], ["a"], 5), 0.0)
        self.assertEqual(E.mrr([], ["a"]), 0.0)

    def test_duplicate_retrieved_ids(self):
        self.assertEqual(E.mrr(["a", "a", "b"], ["b"]), 1 / 2)
        self.assertAlmostEqual(E.recall_at_k(["a", "a"], ["a", "b"], 5), 1 / 2)

    def test_empty_relevance_set_is_none(self):
        self.assertIsNone(E.recall_at_k(["a"], [], 5))
        self.assertIsNone(E.mrr(["a"], []))
        query = E.evaluate_query(["a"], [])
        self.assertEqual(query, {"recall@5": None, "recall@10": None, "mrr": None})

    def test_benchmark_skips_undefined_in_average(self):
        judgments = [E.Judgment("q1", "a", ("x",)), E.Judgment("q2", "b", ())]
        metrics = E.evaluate_benchmark({"q1": ["x"], "q2": ["y"]}, judgments)
        self.assertEqual(metrics["aggregate"]["recall@5"],
                         {"value": 1.0, "n": 1, "n_queries": 2})
        self.assertEqual(metrics["aggregate"]["mrr"]["n"], 1)


class TextBuilderTest(unittest.TestCase):
    def test_deterministic_record_text(self):
        first = E.build_record_text(_record())
        self.assertEqual(first, E.build_record_text(_record()))
        for token in ("anomaly/X/x.mp4", "Person", "Running", "Jogging",
                      "Fighting", "Assault", "anomaly/X/x.mp4@t=0.0s-2.0s"):
            self.assertIn(token, first)

    def test_no_invented_content(self):
        text = E.build_record_text(_record()).lower()
        for invented in ("suspect", "victim", "guilty", "caused"):
            self.assertNotIn(invented, text)

    def test_empty_record_yields_empty_text(self):
        self.assertEqual(E.build_record_text({}), "")


class LexicalAdapterTest(unittest.TestCase):
    def test_adapter_uses_frozen_3a(self):
        records = [_record("v:f0"), _record("v:f1")]
        results = E.lexical_search(records, "fighting", top_k=10)
        self.assertTrue(all(r.retrieval_method == "lexical" for r in results))
        self.assertEqual([r.rank for r in results], list(range(1, len(results) + 1)))
        self.assertEqual(results[0].evidence_id, "v:f0")

    def test_adapter_top_k_cap(self):
        records = [_record(f"v:f{i}") for i in range(5)]
        self.assertLessEqual(len(E.lexical_search(records, "fighting", top_k=2)), 2)


class HybridTest(unittest.TestCase):
    def test_deterministic_dedup(self):
        fused = E.rrf_fuse([_hits("a", "b"), _hits("b", "c")])
        self.assertEqual(fused, E.rrf_fuse([_hits("a", "b"), _hits("b", "c")]))
        self.assertEqual([r.evidence_id for r in fused], ["b", "a", "c"])
        self.assertEqual([r.rank for r in fused], [1, 2, 3])
        self.assertTrue(all(r.retrieval_method == "hybrid-rrf" for r in fused))

    def test_constant_configurable(self):
        loose = E.rrf_fuse([_hits("a"), _hits("b")], constant=1)
        tight = E.rrf_fuse([_hits("a"), _hits("b")], constant=1000)
        self.assertNotEqual(loose[0].score, tight[0].score)
        self.assertEqual([r.evidence_id for r in loose], ["a", "b"])


class BenchmarkLoadTest(unittest.TestCase):
    def _write(self, directory, payload):
        path = Path(directory) / "bench.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_valid_benchmark(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, {"schema_version": "retrieval_eval/v1",
                                     "queries": [{"query_id": "q1", "query": "fighting",
                                                  "relevant_evidence_ids": ["v:f0"]}]})
            judgments = E.load_benchmark(path, {"v:f0"})
            self.assertEqual(len(judgments), 1)
            self.assertEqual(judgments[0].relevant_evidence_ids, ("v:f0",))

    def test_duplicate_query_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, {"schema_version": "retrieval_eval/v1",
                                     "queries": [
                                         {"query_id": "q1", "query": "a",
                                          "relevant_evidence_ids": ["v:f0"]},
                                         {"query_id": "q1", "query": "b",
                                          "relevant_evidence_ids": ["v:f1"]}]})
            with self.assertRaises(ValueError):
                E.load_benchmark(path)

    def test_duplicate_relevant_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, {"schema_version": "retrieval_eval/v1",
                                     "queries": [{"query_id": "q1", "query": "a",
                                                  "relevant_evidence_ids": ["x", "x"]}]})
            with self.assertRaises(ValueError):
                E.load_benchmark(path)

    def test_unknown_ids_rejected_when_corpus_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, {"schema_version": "retrieval_eval/v1",
                                     "queries": [{"query_id": "q1", "query": "a",
                                                  "relevant_evidence_ids": ["ghost:f0"]}]})
            with self.assertRaises(ValueError):
                E.load_benchmark(path, {"v:f0"})
            self.assertEqual(len(E.load_benchmark(path)), 1)

    def test_empty_query_text_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, {"schema_version": "retrieval_eval/v1",
                                     "queries": [{"query_id": "q1", "query": "  ",
                                                  "relevant_evidence_ids": ["v:f0"]}]})
            with self.assertRaises(ValueError):
                E.load_benchmark(path)

    def test_empty_relevance_rejected_unless_marked(self):
        with tempfile.TemporaryDirectory() as tmp:
            bare = self._write(tmp, {"schema_version": "retrieval_eval/v1",
                                     "queries": [{"query_id": "q1", "query": "a",
                                                  "relevant_evidence_ids": []}]})
            with self.assertRaises(ValueError):
                E.load_benchmark(bare)
            marked = {"schema_version": "retrieval_eval/v1",
                      "queries": [{"query_id": "q1", "query": "a",
                                   "relevant_evidence_ids": [],
                                   "empty_relevance_intended": True}]}
            path = self._write(tmp, marked)
            judgments = E.load_benchmark(path)
            self.assertEqual(len(judgments), 1)
            self.assertTrue(judgments[0].empty_intended)


class AnnotationWorkflowTest(unittest.TestCase):
    def _records(self):
        return [{"evidence_id": "v:f0", "video_id": "v", "start_time": 0.0,
                 "end_time": 2.0, "object_evidence": [], "generic_action_evidence": [],
                 "surveillance_event_evidence": [], "source_references": [],
                 "anomaly_score": 0.1},
                {"evidence_id": "v:f1", "video_id": "v", "start_time": 2.0,
                 "end_time": 4.0, "object_evidence": [], "generic_action_evidence": [],
                 "surveillance_event_evidence": [], "source_references": [],
                 "anomaly_score": 0.2},
                {"evidence_id": "w:f0", "video_id": "w", "start_time": 0.0,
                 "end_time": 2.0, "object_evidence": [], "generic_action_evidence": [],
                 "surveillance_event_evidence": [], "source_references": [],
                 "anomaly_score": 0.3}]

    def test_match_found(self):
        from src.pipeline import annotate_retrieval as ANN

        records = [dict(r, object_evidence=[{"class_name": "Person"}])
                   if r["evidence_id"] == "v:f1" else r
                   for r in self._records()]
        scoped = ANN.scope_records(records, "v", 0.0, 4.0, match="person")
        self.assertEqual([r["evidence_id"] for r in scoped], ["v:f1"])

    def test_match_not_found(self):
        from src.pipeline import annotate_retrieval as ANN

        self.assertEqual(ANN.scope_records(self._records(), "v", 0.0, 4.0,
                                           match="nothing-here"), [])

    def test_match_case_insensitive(self):
        from src.pipeline import annotate_retrieval as ANN

        records = [{"evidence_id": "v:f0", "video_id": "v", "start_time": 0.0,
                    "end_time": 2.0, "object_evidence": [{"class_name": "Person"}],
                    "generic_action_evidence": [], "surveillance_event_evidence": [],
                    "source_references": []}]
        self.assertEqual(len(ANN.scope_records(records, "v", match="person")), 1)
        self.assertEqual(len(ANN.scope_records(records, "v", match="PERSON")), 1)

    def test_match_topk_and_refs(self):
        from src.pipeline import annotate_retrieval as ANN

        records = [{"evidence_id": "v:f0", "video_id": "v", "start_time": 0.0,
                    "end_time": 2.0, "object_evidence": [],
                    "generic_action_evidence": [
                        {"label": "Running", "top_k": [{"label": "Jogging"}]}],
                    "surveillance_event_evidence": [],
                    "source_references": ["v@t=0.0s"]}]
        self.assertEqual(len(ANN.scope_records(records, "v", match="jogging")), 1)
        self.assertEqual(len(ANN.scope_records(records, "v", match="t=0.0s")), 1)

    def test_match_preserves_order_no_ranking(self):
        from src.pipeline import annotate_retrieval as ANN

        records = [dict(r, object_evidence=[{"class_name": "Person"}])
                   for r in self._records()]
        scoped = ANN.scope_records(records, match="person")
        self.assertEqual([r["evidence_id"] for r in scoped], ["v:f0", "v:f1", "w:f0"])
        for record in scoped:
            self.assertNotIn("rank", record)
            self.assertNotIn("similarity", record)

    def test_scope_filter_deterministic(self):
        from src.pipeline import annotate_retrieval as ANN

        scoped = ANN.scope_records(self._records(), "v", 1.0, 3.0)
        self.assertEqual([r["evidence_id"] for r in scoped], ["v:f0", "v:f1"])
        self.assertEqual(ANN.scope_records(self._records(), "v", 1.0, 3.0), scoped)
        self.assertEqual(ANN.scope_records(self._records(), "missing"), [])

    def test_entry_status(self):
        from src.pipeline import annotate_retrieval as ANN

        self.assertEqual(ANN.entry_status({"relevant_evidence_ids": ["x"]}), "complete")
        self.assertEqual(ANN.entry_status({"relevant_evidence_ids": [],
                                           "empty_relevance_intended": True}),
                         "marked-empty")
        self.assertEqual(ANN.entry_status({"relevant_evidence_ids": []}), "incomplete")

    def test_check_reports_incomplete(self):
        import tempfile

        from src.pipeline import annotate_retrieval as ANN

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "b.json"
            path.write_text(json.dumps({"schema_version": "retrieval_eval/v1",
                                        "queries": [
                                            {"query_id": "Q1", "query": "a",
                                             "relevant_evidence_ids": ["v:f0"]},
                                            {"query_id": "Q2", "query": "b",
                                             "relevant_evidence_ids": []}]}),
                            encoding="utf-8")
            report = ANN.check_benchmark(path)
            self.assertEqual((report["complete"], report["incomplete"]), (1, 1))
            self.assertEqual(ANN.main(["--benchmark", str(path), "--check"]), 1)


class AnnotationDisplayTest(unittest.TestCase):
    def _records(self):
        return [
            {"evidence_id": "v:f0", "video_id": "v", "start_time": 0.0,
             "end_time": 2.0,
             "object_evidence": [{"class_name": "Person", "confidence": 0.9}],
             "generic_action_evidence": [{"label": "Running", "confidence": 0.7}],
             "surveillance_event_evidence": [{"label": "Fighting", "confidence": 0.8}],
             "source_references": ["v@t=0.0s-2.0s"], "anomaly_score": 0.5},
            {"evidence_id": "v:f1", "video_id": "v", "start_time": 12.0,
             "end_time": 14.0,
             "object_evidence": [{"class_name": "Car", "confidence": 0.6}],
             "generic_action_evidence": [{"label": "Driving car", "confidence": 0.4}],
             "surveillance_event_evidence": [],
             "source_references": [], "anomaly_score": 0.2},
        ]

    def test_compact_mode(self):
        from src.pipeline import annotate_retrieval as ANN

        line = ANN.format_compact(self._records()[0])
        self.assertIn("v:f0", line)
        self.assertIn("0.0-2.0s", line)
        self.assertIn("Person", line)
        self.assertIn("Running", line)
        self.assertIn("Fighting", line)
        self.assertEqual(len(line.splitlines()), 1)

    def test_ids_only_cli(self):
        import io
        import tempfile
        from contextlib import redirect_stdout

        from src.pipeline import annotate_retrieval as ANN

        with tempfile.TemporaryDirectory() as tmp:
            ev = Path(tmp) / "ev.json"
            ev.write_text(json.dumps(self._records()), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = ANN.main(["--evidence", str(ev), "--video-id", "v",
                                 "--ids-only", "--max-records", "0"])
            self.assertEqual(code, 0)
            lines = [l for l in buf.getvalue().splitlines()
                     if not l.startswith("showing ")]
            self.assertEqual(lines, ["v:f0", "v:f1"])

    def test_multiple_match_terms_or_semantics(self):
        from src.pipeline import annotate_retrieval as ANN

        scoped = ANN.scope_records(self._records(), "v", match="person,car")
        self.assertEqual([r["evidence_id"] for r in scoped], ["v:f0", "v:f1"])
        scoped = ANN.scope_records(self._records(), "v", match="car")
        self.assertEqual([r["evidence_id"] for r in scoped], ["v:f1"])

    def test_incident_summary(self):
        from src.pipeline import annotate_retrieval as ANN

        lines = ANN.summarize_scope(self._records())
        self.assertEqual(lines[0], "scope records: 2")
        self.assertTrue(any(l.startswith("[event] Fighting: n=1") for l in lines))
        self.assertTrue(any("first=0.0 last=2.0" in l for l in lines))
        self.assertTrue(all("relevant" not in l.lower() for l in lines))

    def test_time_buckets_deterministic(self):
        from src.pipeline import annotate_retrieval as ANN

        first = ANN.bucket_records(self._records(), 10.0)
        self.assertEqual(first, ANN.bucket_records(self._records(), 10.0))
        self.assertTrue(first[0].startswith("[0-10s] n=1"))
        self.assertTrue(any(l.startswith("[10-20s] n=1") for l in first))
        self.assertTrue(any("v:f1" in l for l in first))
        with self.assertRaises(ValueError):
            ANN.bucket_records(self._records(), 0)

    def test_no_ranking_fields_added(self):
        from src.pipeline import annotate_retrieval as ANN

        for record in ANN.scope_records(self._records(), "v", match="person,car"):
            self.assertNotIn("rank", record)
            self.assertNotIn("similarity", record)

    def test_summary_modes_ignore_display_cap(self):
        import io
        import tempfile
        from contextlib import redirect_stdout

        from src.pipeline import annotate_retrieval as ANN

        with tempfile.TemporaryDirectory() as tmp:
            ev = Path(tmp) / "ev.json"
            ev.write_text(json.dumps(self._records()), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = ANN.main(["--evidence", str(ev), "--video-id", "v",
                                 "--incident-summary", "--max-records", "1"])
            self.assertEqual(code, 0)
            self.assertIn("scope records: 2", buf.getvalue())
        from src.pipeline import annotate_retrieval as ANN

        for record in ANN.scope_records(self._records(), "v", match="person,car"):
            self.assertNotIn("rank", record)
            self.assertNotIn("score_value", record)

    def test_inspection_never_modifies_benchmark(self):
        import io
        import tempfile
        from contextlib import redirect_stdout

        from src.pipeline import annotate_retrieval as ANN

        with tempfile.TemporaryDirectory() as tmp:
            bench = Path(tmp) / "b.json"
            bench.write_text(json.dumps({"schema_version": "retrieval_eval/v1",
                                         "queries": [
                                             {"query_id": "Q1", "query": "a",
                                              "relevant_evidence_ids": [],
                                              "scope": {"video_id": "v",
                                                        "start_time": None,
                                                        "end_time": None}}]}),
                             encoding="utf-8")
            ev = Path(tmp) / "ev.json"
            ev.write_text(json.dumps(self._records()), encoding="utf-8")
            before = bench.read_bytes()
            buf = io.StringIO()
            with redirect_stdout(buf):
                ANN.main(["--benchmark", str(bench), "--evidence", str(ev),
                          "--query-id", "Q1", "--match", "person",
                          "--compact", "--ids-only"])
            self.assertEqual(bench.read_bytes(), before)
            self.assertIn('"relevant_evidence_ids": []', bench.read_text(encoding="utf-8"))


class JudgmentAssistantTest(unittest.TestCase):
    def _rec(self, eid, label=None, action=None, event=None, start=0.0, end=2.0):
        return {"evidence_id": eid, "video_id": eid.split(":")[0], "start_time": start,
                "end_time": end,
                "object_evidence": [{"class_name": label}] if label else [],
                "generic_action_evidence": [{"label": action}] if action else [],
                "surveillance_event_evidence": [{"label": event}] if event else [],
                "source_references": []}

    def test_positive_object_query(self):
        from src.pipeline import prepare_judgments as J

        rule = "relevant iff 'person' is present in object_evidence class names"
        self.assertTrue(J.rule_matches(rule, self._rec("v:f0", label="person")))
        self.assertFalse(J.rule_matches(rule, self._rec("v:f1", label="car")))

    def test_positive_action_query(self):
        from src.pipeline import prepare_judgments as J

        rule = "relevant iff 'running' is present in generic_action_evidence labels"
        self.assertTrue(J.rule_matches(rule, self._rec("v:f0", action="running")))
        self.assertFalse(J.rule_matches(rule, self._rec("v:f1", action="walking")))

    def test_negative_all_empty_query(self):
        from src.pipeline import prepare_judgments as J

        rule = "relevant iff 'boat' is present in object_evidence class names"
        recs = [self._rec("v:f0", label="car"), self._rec("v:f1", label="person")]
        entry = {"query_id": "Q", "relevance_rule": rule,
                 "scope": {"video_id": "v", "start_time": None, "end_time": None}}
        self.assertEqual(J.candidates_for(entry, recs), [])

    def test_conjunction(self):
        from src.pipeline import prepare_judgments as J

        rule = ("relevant iff 'person' is present in object_evidence class names "
                "AND 'Shooting' is present in surveillance_event_evidence labels")
        both = self._rec("v:f0", label="person", event="Shooting")
        one = self._rec("v:f1", label="person", event="Burglary")
        self.assertTrue(J.rule_matches(rule, both))
        self.assertFalse(J.rule_matches(rule, one))

    def test_disjunction(self):
        from src.pipeline import prepare_judgments as J

        rule = ("relevant iff 'car' is present in object_evidence class names "
                "OR 'motorcycle' is present in object_evidence class names")
        self.assertTrue(J.rule_matches(rule, self._rec("v:f0", label="bus")) is False)
        self.assertTrue(J.rule_matches(rule, self._rec("v:f1", label="car")))
        self.assertTrue(J.rule_matches(rule, self._rec("v:f2", label="motorcycle")))

    def test_temporal_overlap(self):
        from src.pipeline import prepare_judgments as J

        rule = "relevant iff the evidence interval overlaps [80, 88] seconds"
        self.assertTrue(J.rule_matches(rule, self._rec("v:f0", start=79.0, end=81.0)))
        self.assertTrue(J.rule_matches(rule, self._rec("v:f1", start=88.0, end=90.0)))
        self.assertFalse(J.rule_matches(rule, self._rec("v:f2", start=90.0, end=92.0)))
        self.assertFalse(J.rule_matches(rule, self._rec("v:f3", start=0.0, end=79.9)))

    def test_temporal_plus_content(self):
        from src.pipeline import prepare_judgments as J

        rule = ("relevant iff the evidence interval overlaps [90, 110] seconds "
                "AND 'Burglary' is present in surveillance_event_evidence labels")
        good = self._rec("v:f0", event="Burglary", start=95.0, end=97.0)
        wrong_time = self._rec("v:f1", event="Burglary", start=0.0, end=2.0)
        wrong_label = self._rec("v:f2", event="Robbery", start=95.0, end=97.0)
        self.assertTrue(J.rule_matches(rule, good))
        self.assertFalse(J.rule_matches(rule, wrong_time))
        self.assertFalse(J.rule_matches(rule, wrong_label))

    def test_scope_boundaries(self):
        from src.pipeline import prepare_judgments as J

        rule = "relevant iff 'person' is present in object_evidence class names"
        recs = [self._rec("v:f0", label="person", start=0.0, end=2.0),
                self._rec("v:f1", label="person", start=58.0, end=62.0),
                self._rec("w:f0", label="person", start=0.0, end=2.0)]
        entry = {"query_id": "Q", "relevance_rule": rule,
                 "scope": {"video_id": "v", "start_time": 0.0, "end_time": 60.0}}
        self.assertEqual(J.candidates_for(entry, recs), ["v:f0", "v:f1"])

    def test_elided_or_shares_field(self):
        from src.pipeline import prepare_judgments as J

        rule = ("relevant iff 'car' OR 'motorcycle' is present "
                "in object_evidence class names")
        self.assertTrue(J.rule_matches(rule, self._rec("v:f0", label="car")))
        self.assertTrue(J.rule_matches(rule, self._rec("v:f1", label="motorcycle")))
        self.assertFalse(J.rule_matches(rule, self._rec("v:f2", label="bus")))

    def test_cross_field_or(self):
        from src.pipeline import prepare_judgments as J

        rule = ("relevant iff 'Arson' is present in surveillance_event_evidence "
                "labels OR 'extinguishing fire' is present in "
                "generic_action_evidence labels")
        self.assertTrue(J.rule_matches(rule, self._rec("v:f0", event="Arson")))
        self.assertTrue(J.rule_matches(rule, self._rec("v:f1", action="extinguishing fire")))
        self.assertFalse(J.rule_matches(rule, self._rec("v:f2", event="Burglary")))

    def test_bare_label_without_field_fails_closed(self):
        from src.pipeline import prepare_judgments as J

        with self.assertRaises(ValueError):
            J.rule_matches("relevant iff 'car' OR 'bus'",
                           self._rec("v:f0", label="car"))

    def test_unknown_rule_fails_closed(self):
        from src.pipeline import prepare_judgments as J

        with self.assertRaises(ValueError):
            J.rule_matches("relevant iff vibes are good", self._rec("v:f0"))
        with self.assertRaises(ValueError):
            J.rule_matches("do something", self._rec("v:f0"))

    def test_no_mutation_of_benchmark(self):
        import io
        import tempfile
        from contextlib import redirect_stdout

        from src.pipeline import prepare_judgments as J

        with tempfile.TemporaryDirectory() as tmp:
            bench = Path(tmp) / "b.json"
            bench.write_text(json.dumps({"schema_version": "retrieval_eval/v1",
                                         "queries": [
                                             {"query_id": "Q1", "query": "person",
                                              "relevant_evidence_ids": [],
                                              "relevance_rule": "relevant iff 'person' is present in object_evidence class names",
                                              "scope": {"video_id": "v",
                                                        "start_time": None,
                                                        "end_time": None}}]}),
                             encoding="utf-8")
            ev = Path(tmp) / "ev.json"
            ev.write_text(json.dumps([self._rec("v:f0", label="person")]),
                          encoding="utf-8")
            before = bench.read_bytes()
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = J.main(["--benchmark", str(bench), "--evidence", str(ev),
                               "--query-id", "Q1"])
            self.assertEqual(code, 0)
            self.assertIn("v:f0", buf.getvalue())
            self.assertEqual(bench.read_bytes(), before)


class LexicalJudgmentAdapterTest(unittest.TestCase):
    def _rec(self, eid, video=None, start=0.0, end=2.0, obj=None, action=None,
             event=None):
        video = video if video is not None else eid.split(":")[0]
        return {"evidence_id": eid, "video_id": video, "start_time": start,
                "end_time": end,
                "object_evidence": [{"class_name": obj, "confidence": 0.9,
                                     "detection_id": "d", "observation_id": "o",
                                     "timestamp_seconds": start}] if obj else [],
                "generic_action_evidence": [{"label": action, "confidence": 0.7,
                                             "observation_id": "a",
                                             "source_reference": "a",
                                             "top_k": []}] if action else [],
                "surveillance_event_evidence": [{"label": event, "confidence": 0.8,
                                                 "observation_id": "e",
                                                 "source_reference": "e",
                                                 "top_k": []}] if event else [],
                "source_references": [f"{video}@t={start}s-{end}s"],
                "anomaly_score": 0.5}

    def _entry(self, rule, video="v", start=None, end=None):
        return {"query_id": "Q", "query": "q", "relevance_rule": rule,
                "scope": {"video_id": video, "start_time": start, "end_time": end}}

    def test_single_object_term(self):
        recs = [self._rec("v:f0", obj="person"), self._rec("v:f1", obj="car")]
        out = E.lexical_search_for_judgment(
            recs, self._entry("relevant iff 'person' is present in "
                              "object_evidence class names"), top_k=10)
        self.assertEqual([r.evidence_id for r in out], ["v:f0"])
        self.assertEqual(out[0].retrieval_method, "lexical")

    def test_single_action_term(self):
        recs = [self._rec("v:f0", action="running"),
                self._rec("v:f1", action="walking")]
        out = E.lexical_search_for_judgment(
            recs, self._entry("relevant iff 'running' is present in "
                              "generic_action_evidence labels"), top_k=10)
        self.assertEqual([r.evidence_id for r in out], ["v:f0"])

    def test_single_event_term(self):
        recs = [self._rec("v:f0", event="Arson"),
                self._rec("v:f1", event="Burglary")]
        out = E.lexical_search_for_judgment(
            recs, self._entry("relevant iff 'Arson' is present in "
                              "surveillance_event_evidence labels"), top_k=10)
        self.assertEqual([r.evidence_id for r in out], ["v:f0"])

    def test_and_object_event(self):
        recs = [self._rec("v:f0", obj="person", event="Shooting"),
                self._rec("v:f1", obj="person", event="Burglary"),
                self._rec("v:f2", obj="car", event="Shooting")]
        out = E.lexical_search_for_judgment(
            recs, self._entry("relevant iff 'person' is present in "
                              "object_evidence class names AND 'Shooting' is present in "
                              "surveillance_event_evidence labels"), top_k=10)
        self.assertEqual([r.evidence_id for r in out], ["v:f0"])

    def test_or_object_terms(self):
        recs = [self._rec("v:f0", obj="bus"),
                self._rec("v:f1", obj="car"),
                self._rec("v:f2", obj="motorcycle")]
        out = E.lexical_search_for_judgment(
            recs, self._entry("relevant iff 'car' OR 'motorcycle' is present in "
                              "object_evidence class names"), top_k=10)
        self.assertEqual([r.evidence_id for r in out], ["v:f1", "v:f2"])

    def test_temporal_only_returns_empty(self):
        recs = [self._rec("v:f0", start=81.0, end=83.0)]
        out = E.lexical_search_for_judgment(
            recs, self._entry("relevant iff the evidence interval overlaps "
                              "[80, 88] seconds"), top_k=10)
        self.assertEqual(out, [])

    def test_temporal_plus_content_applies_window(self):
        recs = [self._rec("v:f0", event="Burglary", start=95.0, end=97.0),
                self._rec("v:f1", event="Burglary", start=0.0, end=2.0)]
        out = E.lexical_search_for_judgment(
            recs, self._entry("relevant iff the evidence interval overlaps "
                              "[90, 110] seconds AND 'Burglary' is present in "
                              "surveillance_event_evidence labels"), top_k=10)
        self.assertEqual([r.evidence_id for r in out], ["v:f0"])

    def test_scope_video_preserved(self):
        recs = [self._rec("v:f0", video="v", obj="person"),
                self._rec("w:f0", video="w", obj="person")]
        out = E.lexical_search_for_judgment(
            recs, self._entry("relevant iff 'person' is present in "
                              "object_evidence class names", video="v"), top_k=10)
        self.assertEqual([r.evidence_id for r in out], ["v:f0"])

    def test_unknown_rule_raises(self):
        with self.assertRaises(ValueError):
            E.lexical_search_for_judgment(
                [self._rec("v:f0")], self._entry("relevant iff vibes are good"))

    def test_build_lexical_queries_terms(self):
        spec = E.build_lexical_queries(
            "relevant iff 'person' is present in object_evidence class names "
            "AND 'Shooting' is present in surveillance_event_evidence labels")
        self.assertEqual(spec["operator"], "AND")
        self.assertEqual([t[0] for t in spec["terms"]], ["person", "Shooting"])
        self.assertIsNone(spec["window"])
        temporal = E.build_lexical_queries(
            "relevant iff the evidence interval overlaps [80, 88] seconds")
        self.assertEqual(temporal["terms"], [])
        self.assertEqual(temporal["window"], (80.0, 88.0))


class ComparisonTest(unittest.TestCase):
    def _results(self, values, nulls=()):
        per = {}
        for i in range(1, 4):
            q = f"Q{i:02d}"
            if q in nulls:
                per[q] = {"recall@5": None, "recall@10": None, "mrr": None}
            else:
                per[q] = {"recall@5": values[0], "recall@10": values[1],
                          "mrr": values[2]}
        agg = {}
        for j, metric in enumerate(("recall@5", "recall@10", "mrr")):
            scored = [q for q in per if q not in nulls]
            agg[metric] = {"value": values[j], "n": len(scored), "n_queries": 3}
        return {"aggregate": agg, "per_query": per}

    def _bench(self):
        return {"queries": [{"query_id": f"Q{i:02d}"} for i in range(1, 4)]}

    def test_comparability_and_winners(self):
        from src.pipeline import compare_retrieval as C

        lex = self._results((0.5, 0.6, 1.0), nulls={"Q03"})
        vec = self._results((0.7, 0.6, 0.5), nulls={"Q03"})
        info = C.verify_comparable(lex, vec, self._bench())
        self.assertEqual(info, {"queries": 3, "positive": 2, "empty": 1})
        artifact = C.build_artifact(lex, vec, self._bench())
        self.assertEqual(artifact["vector_minus_lexical"],
                         {"recall@5": 0.2, "recall@10": 0.0, "mrr": -0.5})
        self.assertEqual(artifact["per_query"]["Q01"]["winner"],
                         {"recall@5": "vector", "recall@10": "tie", "mrr": "lexical"})
        self.assertEqual(artifact["per_query"]["Q03"]["winner"],
                         {"recall@5": "n/a", "recall@10": "n/a", "mrr": "n/a"})

    def test_mismatched_partitions_rejected(self):
        from src.pipeline import compare_retrieval as C

        lex = self._results((0.5, 0.6, 1.0), nulls={"Q03"})
        vec = self._results((0.7, 0.6, 0.5))
        with self.assertRaises(ValueError):
            C.verify_comparable(lex, vec, self._bench())

    def test_expected_values_check(self):
        from src.pipeline import compare_retrieval as C

        artifact = {"lexical": {"aggregate": {
            "recall@5": {"value": 0.4315}, "recall@10": {"value": 0.6045},
            "mrr": {"value": 0.8182}}},
            "vector": {"aggregate": {
                "recall@5": {"value": 0.4743}, "recall@10": {"value": 0.6917},
                "mrr": {"value": 0.8565}}}}
        self.assertEqual(C.verify_expected(artifact), [])
        artifact["vector"]["aggregate"]["mrr"]["value"] = 0.5
        self.assertEqual(len(C.verify_expected(artifact)), 1)

    def test_hybrid_artifact(self):
        from src.pipeline import compare_retrieval as C

        def _res(values):
            per = {f"Q{i:02d}": {"recall@5": values[0], "recall@10": values[1],
                                 "mrr": values[2]} for i in (1, 2)}
            agg = {m: {"value": v, "n": 2, "n_queries": 2}
                   for m, v in zip(("recall@5", "recall@10", "mrr"), values)}
            return {"aggregate": agg, "per_query": per,
                    "latency_seconds": {"mean": 0.1}}

        bench = {"queries": [{"query_id": "Q01"}, {"query_id": "Q02"}]}
        artifact = C.build_hybrid_artifact(_res((0.5, 0.6, 1.0)),
                                           _res((0.7, 0.6, 0.5)),
                                           _res((0.6, 0.8, 1.0)), bench)
        self.assertEqual(artifact["pairwise_differences"]["hybrid_minus_lexical"],
                         {"recall@5": 0.1, "recall@10": 0.2, "mrr": 0.0})
        self.assertEqual(artifact["fusion"]["constant"], 60)
        self.assertIn("RRF", C.render_hybrid_markdown(artifact))


class HybridAdapterTest(unittest.TestCase):
    def _rec(self, eid, obj=None, event=None):
        return {"evidence_id": eid, "video_id": "v", "start_time": 0.0,
                "end_time": 2.0,
                "object_evidence": [{"class_name": obj, "confidence": 0.9,
                                     "detection_id": "d", "observation_id": "o",
                                     "timestamp_seconds": 0.0}] if obj else [],
                "generic_action_evidence": [],
                "surveillance_event_evidence": [{"label": event, "confidence": 0.8,
                                                 "observation_id": "e",
                                                 "source_reference": "e",
                                                 "top_k": []}] if event else [],
                "source_references": [], "anomaly_score": 0.5}

    class _FakeRetriever:
        def __init__(self, order):
            self.order = order

        def search(self, query, top_k=10):
            return [E.RetrievalResult(evidence_id=e, rank=i, score=1.0 / i,
                                      retrieval_method="vector")
                    for i, e in enumerate(self.order[:max(0, top_k)], 1)]

    def _entry(self, rule):
        return {"query_id": "Q", "query": "q", "relevance_rule": rule,
                "scope": {"video_id": "v", "start_time": None, "end_time": None}}

    def test_rrf_score_calculation(self):
        fused = E.rrf_fuse([[E.RetrievalResult("a", 1, 0.9, "lexical"),
                             E.RetrievalResult("b", 2, 0.1, "lexical")],
                            [E.RetrievalResult("b", 1, 0.9, "vector")]])
        by_id = {r.evidence_id: r for r in fused}
        self.assertAlmostEqual(by_id["a"].score, 1 / 61)
        self.assertAlmostEqual(by_id["b"].score, 1 / 62 + 1 / 61)
        self.assertEqual([r.evidence_id for r in fused], ["b", "a"])

    def test_fusion_combines_branches(self):
        recs = [self._rec("v:f0", obj="person", event="Shooting"),
                self._rec("v:f1", obj="person", event="Burglary")]
        retr = self._FakeRetriever(["v:f1", "v:f0"])
        out = E.hybrid_search_for_judgment(
            recs, self._entry("relevant iff 'person' is present in "
                              "object_evidence class names"), retr, top_k=10)
        self.assertEqual({r.evidence_id for r in out}, {"v:f0", "v:f1"})
        self.assertTrue(all(r.retrieval_method == "hybrid" for r in out))
        self.assertEqual([r.rank for r in out], [1, 2])

    def test_missing_branch_result(self):
        recs = [self._rec("v:f0", obj="person")]
        retr = self._FakeRetriever([])
        out = E.hybrid_search_for_judgment(
            recs, self._entry("relevant iff 'person' is present in "
                              "object_evidence class names"), retr, top_k=10)
        self.assertEqual([r.evidence_id for r in out], ["v:f0"])

    def test_top_k_and_scope(self):
        recs = [self._rec("v:f0", obj="person"), self._rec("v:f1", obj="person"),
                self._rec("w:f0", obj="person")]
        retr = self._FakeRetriever(["w:f0", "v:f1", "v:f0"])
        entry = {"query_id": "Q", "query": "q",
                 "relevance_rule": "relevant iff 'person' is present in "
                                   "object_evidence class names",
                 "scope": {"video_id": "v", "start_time": None, "end_time": None}}
        out = E.hybrid_search_for_judgment(recs, entry, retr, top_k=1)
        self.assertEqual(len(out), 1)
        self.assertNotIn("w:f0", [r.evidence_id for r in out])

    def test_empty_relevance_stays_null(self):
        metrics = E.evaluate_query(["v:f0"], [])
        self.assertEqual(metrics, {"recall@5": None, "recall@10": None, "mrr": None})


if __name__ == "__main__":
    unittest.main()
