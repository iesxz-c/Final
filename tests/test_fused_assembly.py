"""Controlled-arm tests: lexical ranking, direct assembly, new arms.

Synthetic fixtures only - mock LLM, no network, no API key, no live calls."""

import json
import unittest

from src.agents.llm_client import MockLLMClient
from src.agents import timeline_correlation as E
from src.agents import verification_report as F
from src.pipeline import investigation_eval as IE
from src.pipeline.retrieval_eval import RetrievalResult

VA = "anomaly/Robbery/vA.mp4"
VB = "anomaly/Shoplifting/vB.mp4"
VC = "anomaly/Arson/vC.mp4"


def _evt(obs_id, label, conf=0.8):
    return {"observation_id": obs_id, "label": label, "confidence": conf,
            "model_name": "m", "model_version": "v", "top_k": [],
            "source_reference": obs_id}


def _act(obs_id, label="walking", conf=0.6):
    return {"observation_id": obs_id, "label": label, "confidence": conf,
            "model_name": "m", "model_version": "v", "top_k": [],
            "source_reference": obs_id}


def _det(evidence_id, ts, cls="person", conf=0.9):
    return {"detection_id": evidence_id + ":d0",
            "observation_id": evidence_id,
            "timestamp_seconds": ts, "class_name": cls, "confidence": conf,
            "bounding_box": [1.0, 2.0, 3.0, 4.0], "model_name": "yolo11n"}


def _rec(eid, video, start, end, objects=(), actions=(), events=()):
    return {"evidence_id": eid, "video_id": video,
            "start_time": start, "end_time": end,
            "object_evidence": list(objects),
            "generic_action_evidence": list(actions),
            "surveillance_event_evidence": list(events),
            "source_references": [f"{video}@t={start}s-{end}s"],
            "temporal_support": {}, "anomaly_score": 0.5}


def _fixtures():
    f0 = _rec(f"{VA}:f0", VA, 0.0, 2.0,
              objects=[_det(f"{VA}:f0", 1.0)],
              actions=[_act(f"{VA}:f0:a")],
              events=[_evt(f"{VA}:f0:e", "Fighting", 0.8)])
    f1 = _rec(f"{VA}:f1", VA, 2.0, 4.0,
              events=[_evt(f"{VA}:f1:e", "Fighting", 0.7)])
    f2 = _rec(f"{VA}:f2", VA, 4.0, 6.0,
              events=[_evt(f"{VA}:f2:e", "Normal", 0.9)])
    f3 = _rec(f"{VA}:f3", VA, 100.0, 102.0,
              events=[_evt(f"{VA}:f3:e", "Arson", 0.75)])
    f4 = _rec(f"{VA}:f4", VA, 6.0, 8.0,
              events=[_evt(f"{VA}:f4:e", "Normal", 0.6)])
    f5 = _rec(f"{VA}:f5", VA, 50.0, 52.0,
              events=[_evt(f"{VA}:f5:e", "Normal", 0.6)])
    g0 = _rec(f"{VB}:g0", VB, 1.0, 3.0,
              events=[_evt(f"{VB}:g0:e", "Fighting", 0.6)])
    g9 = _rec(f"{VB}:g9", VB, 200.0, 202.0)
    h0 = _rec(f"{VC}:h0", VC, 10.0, 12.0,
              events=[_evt(f"{VC}:h0:e", "Burglary", 0.65)])
    records = [f0, f1, f2, f3, f4, f5, g0, g9, h0]
    incidents = [
        {"incident_id": f"{VA}:i0", "video_id": VA, "start_time": 0.0,
         "end_time": 6.0, "evidence_ids": [f"{VA}:f0", f"{VA}:f1", f"{VA}:f2"],
         "event_hypotheses": ["Fighting"], "num_windows": 3,
         "span_seconds": 6.0, "anomaly_score": 0.5,
         "schema_version": "phase2d/v1"},
        {"incident_id": f"{VA}:i1", "video_id": VA, "start_time": 100.0,
         "end_time": 102.0, "evidence_ids": [f"{VA}:f3"],
         "event_hypotheses": ["Arson"], "num_windows": 1,
         "span_seconds": 2.0, "anomaly_score": 0.5,
         "schema_version": "phase2d/v1"},
        {"incident_id": f"{VB}:j0", "video_id": VB, "start_time": 1.0,
         "end_time": 3.0, "evidence_ids": [f"{VB}:g0"],
         "event_hypotheses": ["Fighting"], "num_windows": 1,
         "span_seconds": 2.0, "anomaly_score": 0.5,
         "schema_version": "phase2d/v1"},
        {"incident_id": f"{VC}:k0", "video_id": VC, "start_time": 10.0,
         "end_time": 12.0, "evidence_ids": [f"{VC}:h0"],
         "event_hypotheses": ["Burglary"], "num_windows": 1,
         "span_seconds": 2.0, "anomaly_score": 0.5,
         "schema_version": "phase2d/v1"},
    ]
    return records, incidents


def _plan(**over):
    base = {"schema_version": "phase3c/v1", "intent": "search_evidence",
            "queries": [{"query": "Fighting", "source": None}],
            "video_id": None, "start_time": None, "end_time": None,
            "temporal_context_seconds": 0, "needs_timeline": False,
            "needs_cross_evidence": False}
    base.update(over)
    return base


class _FakeRetriever:
    def __init__(self, ids):
        self._ids = list(ids)

    def search(self, query, top_k=10):
        return [RetrievalResult(eid, pos, 0.9 - pos * 0.01, "vector")
                for pos, eid in enumerate(self._ids[:max(0, top_k)], 1)]


def _rank(ids, method="hybrid-rrf"):
    return [RetrievalResult(eid, pos, 0.9 - pos * 0.01, method)
            for pos, eid in enumerate(ids, 1)]


class LexicalRankingTest(unittest.TestCase):
    def test_lexical_only_subset(self):
        records, _ = _fixtures()
        ranked = IE.lexical_ranking_for_plan(records, _plan(), {})
        ids = {r.evidence_id for r in ranked}
        self.assertEqual(ids, {f"{VA}:f0", f"{VA}:f1", f"{VB}:g0"})
        self.assertTrue(all(r.retrieval_method == "lexical" for r in ranked))

    def test_ranking_for_arm_lexical_needs_no_retriever(self):
        records, _ = _fixtures()
        ranked = IE.ranking_for_arm("full-lexical", records, "Fighting",
                                    _plan(), None, {})
        self.assertTrue(ranked)

    def test_ranking_for_arm_hybrid_needs_retriever(self):
        records, _ = _fixtures()
        with self.assertRaises(IE.AssemblyError):
            IE.ranking_for_arm("full-hybrid", records, "Fighting",
                               _plan(), None, {})


class AssemblyTest(unittest.TestCase):
    def test_hybrid_direct_and_vector_only_survives(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f3", f"{VA}:f0", f"{VA}:f1"])
        result = IE.assemble_fused_evidence(_plan(), ranking, records,
                                            incidents, 0)
        matched = {r["evidence_id"] for g in result["merged_results"]["groups"]
                   for r in g["matched_evidence"]}
        self.assertIn(f"{VA}:f3", matched)
        f3 = next(r for g in result["merged_results"]["groups"]
                  for r in g["matched_evidence"]
                  if r["evidence_id"] == f"{VA}:f3")
        self.assertTrue(f3["matched_hits"])

    def test_unrelated_vector_evidence_excluded(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f0", f"{VA}:f1"])
        result = IE.assemble_fused_evidence(_plan(), ranking, records,
                                            incidents, 0)
        blob = json.dumps(result)
        self.assertNotIn(f"{VC}:h0", blob)
        self.assertNotIn(f"{VA}:f3", blob)
        self.assertNotIn(f"{VB}:g9", blob)

    def test_incident_contextual_expansion(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f0", f"{VA}:f1"])
        result = IE.assemble_fused_evidence(_plan(), ranking, records,
                                            incidents, 0)
        group = next(g for g in result["merged_results"]["groups"]
                     if g["incident_id"] == f"{VA}:i0")
        ctx = {r["evidence_id"] for r in group["contextual_evidence"]}
        self.assertIn(f"{VA}:f2", ctx)
        f2 = next(r for r in group["contextual_evidence"]
                  if r["evidence_id"] == f"{VA}:f2")
        self.assertNotIn("matched_hits", f2)

    def test_temporal_contextual_expansion(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f0", f"{VA}:f1"])
        result = IE.assemble_fused_evidence(
            _plan(temporal_context_seconds=5.0), ranking, records,
            incidents, 5.0)
        group = next(g for g in result["merged_results"]["groups"]
                     if g["incident_id"] == f"{VA}:i0")
        ctx = {r["evidence_id"] for r in group["contextual_evidence"]}
        self.assertIn(f"{VA}:f4", ctx)
        self.assertNotIn(f"{VA}:f5", ctx)

    def test_duplicate_fused_ids(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f0", f"{VA}:f0", f"{VA}:f1"])
        result = IE.assemble_fused_evidence(_plan(), ranking, records,
                                            incidents, 0)
        matched = [r["evidence_id"] for g in result["merged_results"]["groups"]
                   for r in g["matched_evidence"]]
        self.assertEqual(len(matched), len(set(matched)))
        self.assertEqual(result["assembly"]["direct_ids"],
                         [f"{VA}:f0", f"{VA}:f1"])

    def test_deterministic_ordering(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f1", f"{VA}:f0", f"{VB}:g0"])
        first = IE.assemble_fused_evidence(_plan(), ranking, records,
                                           incidents, 0)
        second = IE.assemble_fused_evidence(_plan(), ranking,
                                            list(reversed(records)),
                                            list(reversed(incidents)), 0)
        self.assertEqual(json.dumps(first, sort_keys=True, default=str),
                         json.dumps(second, sort_keys=True, default=str))

    def test_empty_retrieval(self):
        records, incidents = _fixtures()
        result = IE.assemble_fused_evidence(_plan(), [], records, incidents, 0)
        self.assertEqual(result["merged_results"]["groups"], [])
        self.assertEqual(result["merged_results"]["unmapped_hits"], [])
        self.assertEqual(result["summary"]["query_errors"], 0)
        self.assertEqual(result["schema_version"], "phase3d/v1")
        empty_3e = E.run_timeline(MockLLMClient("{}"), result, "Fighting")
        self.assertEqual(empty_3e["timeline"], [])

    def test_evidence_id_integrity(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f0", f"{VA}:f3", f"{VB}:g0"])
        result = IE.assemble_fused_evidence(_plan(), ranking, records,
                                            incidents, 0)
        corpus = {r["evidence_id"] for r in records}
        out = {r["evidence_id"] for g in result["merged_results"]["groups"]
               for r in g["matched_evidence"] + g["contextual_evidence"]}
        out |= {h["evidence_id"]
                for h in result["merged_results"]["unmapped_hits"]}
        self.assertTrue(out <= corpus)
        self.assertEqual(result["assembly"]["direct_ids"],
                         [f"{VA}:f0", f"{VA}:f3", f"{VB}:g0"])

    def test_timestamp_containment(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f0", f"{VA}:f1"])
        result = IE.assemble_fused_evidence(_plan(), ranking, records,
                                            incidents, 0)
        by_id = {r["evidence_id"]: r for r in records}
        for group in result["merged_results"]["groups"]:
            for record in group["matched_evidence"] + group["contextual_evidence"]:
                bare = by_id[record["evidence_id"]]
                self.assertEqual(record["start_time"], bare["start_time"])
                self.assertEqual(record["end_time"], bare["end_time"])
                self.assertEqual(record["video_id"], bare["video_id"])

    def test_phase3d_compatibility(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f0", f"{VB}:g9"])
        result = IE.assemble_fused_evidence(_plan(), ranking, records,
                                            incidents, 0)
        self.assertEqual(result["schema_version"], "phase3d/v1")
        for key in ("plan", "query_results", "query_errors",
                    "merged_results", "summary"):
            self.assertIn(key, result)
        for group in result["merged_results"]["groups"]:
            for key in ("incident_id", "video_id", "incident_start_time",
                        "incident_end_time", "event_hypotheses",
                        "matched_evidence", "contextual_evidence"):
                self.assertIn(key, group)
            for record in group["matched_evidence"]:
                self.assertTrue(record["matched_hits"])
            for record in group["contextual_evidence"]:
                self.assertNotIn("matched_hits", record)
        unmapped_ids = {h["evidence_id"] for h in
                        result["merged_results"]["unmapped_hits"]}
        self.assertIn(f"{VB}:g9", unmapped_ids)

    def test_cross_video_isolation(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f0", f"{VB}:g0"])
        result = IE.assemble_fused_evidence(_plan(), ranking, records,
                                            incidents, 0)
        for group in result["merged_results"]["groups"]:
            videos = {r["video_id"] for r in group["matched_evidence"]
                      + group["contextual_evidence"]}
            self.assertEqual(len(videos), 1)

    def test_malformed_record(self):
        records, incidents = _fixtures()
        with self.assertRaises(IE.AssemblyError):
            IE.direct_records_for_ranking(
                _rank(["no-such-id"]), records, top_k=10)
        bad = dict(records[1])
        bad["end_time"] = bad["start_time"] - 1.0
        with self.assertRaises(IE.AssemblyError):
            IE.direct_records_for_ranking(
                _rank([bad["evidence_id"]]), [records[0], bad],
                top_k=10)


class SourceSemanticsTest(unittest.TestCase):
    def test_object_action_event_record_synthesis(self):
        records, _ = _fixtures()
        hits = IE.synthesize_matched_hits(records[0], {"retrieval_method": "x"})
        self.assertEqual({h["matched_source"] for h in hits},
                         {"object", "generic_action", "surveillance_event",
                          "record"})

    def test_event_only_record(self):
        records, _ = _fixtures()
        hits = IE.synthesize_matched_hits(records[1], {})
        self.assertEqual({h["matched_source"] for h in hits},
                         {"surveillance_event", "record"})

    def test_fully_empty_record(self):
        records, _ = _fixtures()
        hits = IE.synthesize_matched_hits(records[7], {})
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["matched_source"], "record")

    def test_provenance_separate_from_source(self):
        records, _ = _fixtures()
        hits = IE.synthesize_matched_hits(
            records[0], {"retrieval_method": "hybrid-rrf", "rank": 1,
                         "score": 0.5})
        for hit in hits:
            self.assertNotIn(hit["matched_source"],
                             {"lexical", "vector", "hybrid", "hybrid-rrf",
                              "dense"})
            self.assertEqual(hit["retrieval_method"], "hybrid-rrf")


class ValidatorCompatTest(unittest.TestCase):
    def test_3e_3f_validators_accept_assembly(self):
        records, incidents = _fixtures()
        ranking = _rank([f"{VA}:f0", f"{VA}:f1"])
        result = IE.assemble_fused_evidence(_plan(), ranking, records,
                                            incidents, 0)
        index = E.collect_evidence_index(result)
        self.assertTrue(index)
        result_3e = E.run_timeline(
            MockLLMClient(E._mock_response_for(result)), result, "Fighting")
        self.assertEqual(result_3e["schema_version"], "phase3e/v1")
        claims = [{k: v for k, v in c.items() if not k.startswith("_")}
                  for c in F.derive_claims(result_3e)]
        index_3d = E.collect_evidence_index(result)
        raw = F._mock_response_for(claims, index_3d)
        report = F.parse_and_validate_report(
            raw, index_3d, [c["claim_id"] for c in claims])
        self.assertEqual(report["schema_version"], "phase3f/v1")


def _case(**over):
    base = {"query_id": "T01", "question": "Fighting",
            "pattern": "event",
            "scope": {"video_id": None, "start_time": None, "end_time": None},
            "ground_truth_source": "synthetic",
            "expected_evidence_ids": [],
            "expected_facts": [], "forbidden_claims": [],
            "expected_temporal_relations": [],
            "abstention_expected": False, "provenance": "test", "notes": ""}
    base.update(over)
    return base


def _settings():
    return {"provider": "mock", "model": "mock", "temperature": 0.0}


class ControlledArmTest(unittest.TestCase):
    def test_full_lexical_arm_reaches_3f(self):
        records, incidents = _fixtures()
        bundle = IE.run_case(_case(), records, incidents, "mock",
                             lambda: None, _settings(), "mock", "full-lexical")
        self.assertIsNone(bundle["failure"])
        self.assertIsNotNone(bundle["result_3f"])
        self.assertEqual(bundle["retrieval"]["method"], "lexical")
        self.assertTrue(bundle["retrieved_evidence_ids"])

    def test_full_hybrid_arm_keeps_vector_only(self):
        records, incidents = _fixtures()
        retriever = _FakeRetriever([f"{VA}:f3", f"{VA}:f0"])
        bundle = IE.run_case(_case(), records, incidents, "mock",
                             lambda: None, _settings(), "mock", "full-hybrid",
                             retriever=retriever)
        self.assertIsNone(bundle["failure"])
        self.assertEqual(bundle["retrieval"]["method"], "hybrid-rrf")
        self.assertIn(f"{VA}:f3", bundle["retrieved_evidence_ids"])
        matched = {r["evidence_id"]
                   for g in bundle["result_3d"]["merged_results"]["groups"]
                   for r in g["matched_evidence"]}
        self.assertIn(f"{VA}:f3", matched)

    def test_hybrid_without_retriever_fails_closed(self):
        records, incidents = _fixtures()
        bundle = IE.run_case(_case(), records, incidents, "mock",
                             lambda: None, _settings(), "mock", "full-hybrid")
        self.assertIsNotNone(bundle["failure"])
        self.assertEqual(bundle["failure"]["stage"], "retr")
        self.assertIsNone(bundle["result_3d"])

    def test_locked_full_path_unchanged(self):
        records, incidents = _fixtures()
        bundle = IE.run_case(_case(), records, incidents, "mock",
                             lambda: None, _settings(), "mock", "full")
        self.assertNotIn("assembly", (bundle["result_3d"] or {}))
        self.assertEqual(bundle["retrieval"]["method"], "hybrid-rrf")


if __name__ == "__main__":
    unittest.main()
