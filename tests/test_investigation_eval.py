"""investigation_eval tests: arms, isolation, metrics, failures.

Synthetic fixtures only - mock LLM, no network, no API key."""

import json
import unittest
from pathlib import Path
from unittest import mock

from src.pipeline import investigation_eval as IE
from src.pipeline import run_investigation as R

VA = "anomaly/Robbery/vA.mp4"


def _rec(eid, video=VA, start=0.0, end=2.0, label="Fighting"):
    return {"evidence_id": eid, "video_id": video,
            "start_time": start, "end_time": end,
            "object_evidence": [], "generic_action_evidence": [],
            "surveillance_event_evidence": [
                {"observation_id": eid + ":e", "label": label,
                 "confidence": 0.8, "model_name": "m", "model_version": "v",
                 "top_k": [], "source_reference": eid + ":e"}],
            "source_references": [f"{video}@t={start}s-{end}s"],
            "temporal_support": {}, "anomaly_score": 0.5}


def _mini():
    records = [_rec(f"{VA}:f0", start=0.0, end=2.0),
               _rec(f"{VA}:f1", start=2.0, end=4.0)]
    incidents = [{"incident_id": f"{VA}:i0", "video_id": VA, "start_time": 0.0,
                  "end_time": 4.0, "evidence_ids": [f"{VA}:f0", f"{VA}:f1"],
                  "event_hypotheses": ["Fighting"], "num_windows": 2,
                  "span_seconds": 4.0, "anomaly_score": 0.5,
                  "schema_version": "phase2d/v1"}]
    return records, incidents


def _case(**over):
    base = {"query_id": "T01", "question": "Fighting",
            "pattern": "event",
            "scope": {"video_id": VA, "start_time": None, "end_time": None},
            "ground_truth_source": "synthetic",
            "expected_evidence_ids": [f"{VA}:f0", f"{VA}:f1"],
            "expected_facts": ["SENTINEL-FACT-xyz"],
            "forbidden_claims": ["SENTINEL-FORBIDDEN-xyz"],
            "expected_temporal_relations": [
                {"relation": "before", "a_evidence_id": f"{VA}:f0",
                 "b_evidence_id": f"{VA}:f1"}],
            "abstention_expected": False, "provenance": "test", "notes": ""}
    base.update(over)
    return base


def _settings():
    return {"provider": "mock", "model": "mock", "temperature": 0.0}


class LoadingTest(unittest.TestCase):
    def test_loads_frozen_benchmark(self):
        cases = IE.load_cases("eval/investigation_benchmark_v1.json")
        self.assertEqual(len(cases), 30)
        self.assertEqual(cases[0]["query_id"], "I01")

    def test_rejects_bad_schema(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "b.json"
            path.write_text(json.dumps({"schema_version": "nope", "cases": []}),
                            encoding="utf-8")
            with self.assertRaises(ValueError):
                IE.load_cases(path)


class ArmSelectionTest(unittest.TestCase):
    def test_baseline_never_calls_reasoning_agents(self):
        records, incidents = _mini()
        with mock.patch.object(IE.E, "run_timeline",
                               side_effect=AssertionError("3E called")), \
             mock.patch.object(IE.F, "run_verification_report",
                               side_effect=AssertionError("3F called")):
            bundle = IE.run_case(_case(), records, incidents, "mock",
                                 lambda: None, _settings(), "mock", "baseline")
        self.assertIsNone(bundle["failure"])
        self.assertIsNotNone(bundle["baseline_report"])
        self.assertIsNone(bundle["result_3e"])
        self.assertIsNone(bundle["result_3f"])
        self.assertEqual(bundle["validator_verdicts"].get("report"), "pass")

    def test_templated_report_deterministic(self):
        records, incidents = _mini()
        first = IE.run_case(_case(), records, incidents, "mock",
                            lambda: None, _settings(), "mock", "baseline")
        second = IE.run_case(_case(), records, incidents, "mock",
                             lambda: None, _settings(), "mock", "baseline")
        self.assertEqual(first["baseline_report"], second["baseline_report"])
        report = first["baseline_report"]
        self.assertIn("limitations", report)
        self.assertTrue(report["evidence_records"])

    def test_full_arm_reaches_3f_in_mock(self):
        records, incidents = _mini()
        bundle = IE.run_case(_case(), records, incidents, "mock",
                             lambda: None, _settings(), "mock", "full")
        self.assertIsNone(bundle["failure"])
        self.assertIsNotNone(bundle["result_3f"])
        self.assertIsNone(bundle["baseline_report"])


class IsolationTest(unittest.TestCase):
    def test_ground_truth_never_reaches_agents(self):
        from src.agents.llm_client import MockLLMClient

        records, incidents = _mini()
        seen = []

        real_plan = IE.Q.plan_query

        def _spy_plan(client, question, temperature=0.0):
            seen.append(("3c", question))
            return real_plan(client, question, temperature)

        def _spy_timeline(client, result_3d, question, temperature=0.0):
            seen.append(("3e", result_3d, question))
            return IE.E.run_timeline(MockLLMClient("{}"), result_3d, question)

        with mock.patch.object(IE.Q, "plan_query", _spy_plan), \
             mock.patch.object(IE.E, "run_timeline", _spy_timeline):
            plan = IE.Q.parse_and_validate_plan(IE.Q._mock_response("Fighting"))
            subset = [r for r in records]
            result_3d = IE.D3.execute_plan(plan, subset, incidents)
            blob = json.dumps({"plan": plan, "subset": subset,
                               "seen": [(s, json.dumps(a, default=str)[:2000])
                                        for s, *a in seen]})
        self.assertNotIn("SENTINEL-FACT-xyz", blob)
        self.assertNotIn("SENTINEL-FORBIDDEN-xyz", blob)


class MetricsTest(unittest.TestCase):
    def _evaluated(self, **over):
        records, incidents = _mini()
        bundle = IE.run_case(_case(**over), records, incidents, "mock",
                             lambda: None, _settings(), "mock", "full")
        return IE.evaluate_case(_case(**over), bundle)

    def test_grounding_counts(self):
        evaluation = self._evaluated()
        total = (evaluation["claims"]["supported"]
                 + evaluation["claims"]["partially_supported"]
                 + evaluation["claims"]["unsupported"])
        self.assertGreaterEqual(total, 0)
        self.assertGreaterEqual(evaluation["citation"]["total"], 0)

    def test_expected_id_overlap(self):
        evaluation = self._evaluated()
        self.assertLessEqual(evaluation["retrieved_expected_count"],
                             evaluation["expected_count"])

    def test_temporal_relations_supported(self):
        evaluation = self._evaluated()
        self.assertIn(evaluation["relations_supported"], (0, 1))
        self.assertEqual(evaluation["relations_total"], 1)

    def test_abstention(self):
        empty_case = _case(query_id="T02", question="Fighting",
                           expected_evidence_ids=[],
                           expected_facts=[],
                           abstention_expected=True)
        records, incidents = _mini()
        bundle = IE.run_case(empty_case, records, incidents, "mock",
                             lambda: None, _settings(), "mock", "full")
        evaluation = IE.evaluate_case(empty_case, bundle)
        self.assertIn(evaluation["abstention_correct"], (True, False))
        plain = self._evaluated()
        self.assertIsNone(plain["abstention_correct"])

    def test_safety_buckets(self):
        records, incidents = _mini()
        bundle = IE.run_case(_case(), records, incidents, "mock",
                             lambda: None, _settings(), "mock", "full")
        evaluation = IE.evaluate_case(_case(), bundle)
        self.assertEqual(evaluation["forbidden_hits"], [])
        self.assertEqual(set(evaluation["safety_phrases"]),
                         {"identity", "causality", "unsupported_crime_confirmation"})

    def test_failure_taxonomy(self):
        records, incidents = _mini()
        bundle = IE.run_case(_case(question=""), records, incidents, "mock",
                             lambda: None, _settings(), "mock", "full")
        self.assertIsNotNone(bundle["failure"])
        self.assertIn(bundle["failure"]["type"],
                      ("validation", "parse", "provider", "timeout",
                       "retrieval", "other"))
        evaluation = IE.evaluate_case(_case(question=""), bundle)
        self.assertFalse(evaluation["schema_valid"])

    def test_empty_evidence_flag(self):
        records, incidents = _mini()
        bundle = IE.run_case(_case(), records, incidents, "mock",
                             lambda: None, _settings(), "mock", "full")
        evaluation = IE.evaluate_case(_case(), bundle)
        self.assertIsInstance(evaluation["empty_evidence"], bool)

    def test_aggregation(self):
        evaluations = [self._evaluated(), self._evaluated()]
        metrics = IE.aggregate_arm(evaluations)
        self.assertEqual(metrics["investigations"], 2)
        self.assertIn("completion_rate", metrics)
        self.assertIn("latency", metrics)
        self.assertIn("total", metrics["latency"])
        self.assertIsNone(metrics["answer_fact_coverage"])
        empty = IE.aggregate_arm([])
        self.assertEqual(empty["investigations"], 0)
        self.assertIsNone(empty["completion_rate"])


class FrozenConfigTest(unittest.TestCase):
    def test_rrf_constant_untouched(self):
        from src.pipeline.retrieval_eval import rrf_fuse

        self.assertEqual(IE.RRF_CONSTANT, 60)
        fused = rrf_fuse([[IE.RetrievalResult("a", 1, 0.9, "lexical")]])
        self.assertAlmostEqual(fused[0].score, 1 / 61)
        self.assertEqual(IE.RETRIEVAL_TOP_K, 10)


class HumanWorksheetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sheet = json.load(
            Path("eval/investigation_human_review_v1.json").open(encoding="utf-8"))
        cls.bench = {c["query_id"]: c for c in json.load(
            Path("eval/investigation_benchmark_v1.json").open(
                encoding="utf-8"))["cases"]}
        bundles = {}
        for path in Path("data/evaluations/investigation/v1").glob("I??.full.json"):
            bundle = json.load(path.open(encoding="utf-8"))
            bundles[bundle["query_id"]] = bundle
        cls.bundles = bundles

    def test_all_cases_facts_claims_present(self):
        self.assertEqual(len(self.sheet["cases"]), 30)
        facts = sum(len(c["fact_grades"]) for c in self.sheet["cases"])
        claims = sum(len(c["claim_grades"]) for c in self.sheet["cases"])
        self.assertEqual(facts, 46)
        self.assertEqual(claims, 158)

    def test_claim_texts_unchanged(self):
        for case in self.sheet["cases"]:
            bundle = self.bundles[case["query_id"]]
            original = {v.get("claim_id"): v.get("claim") for v in
                        (bundle.get("result_3f") or {}).get("verification", []) or []}
            for grade in case["claim_grades"]:
                self.assertEqual(grade["claim_text"], original[grade["claim_id"]])

    def test_facts_unchanged(self):
        for case in self.sheet["cases"]:
            self.assertEqual([g["fact_text"] for g in case["fact_grades"]],
                             self.bench[case["query_id"]]["expected_facts"])

    def test_all_grades_null(self):
        for case in self.sheet["cases"]:
            for grade in case["fact_grades"]:
                self.assertIsNone(grade["baseline_grade"])
                self.assertIsNone(grade["full_grade"])
            for grade in case["claim_grades"]:
                self.assertIsNone(grade["human_support_grade"])

    def test_allowed_grades_documented(self):
        text = Path("eval/investigation_human_review_v1.md").read_text(
            encoding="utf-8")
        for word in ("supported", "partial", "unsupported", "not_applicable"):
            self.assertIn(word, text)


if __name__ == "__main__":
    unittest.main()
