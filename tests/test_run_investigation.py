"""Phase 4 tests: orchestration order, bundle schema, failure capture,
integrity audit, offline metrics. Mock LLM only - no network, no API key."""

import copy
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from src.pipeline import run_investigation as R
from src.pipeline import evaluate_investigations as V

VA = "anomaly/Robbery/vA.mp4"


def _evt(obs_id, label, conf):
    return {"observation_id": obs_id, "label": label, "confidence": conf,
            "model_name": "m", "model_version": "v", "top_k": [],
            "source_reference": obs_id}


def _rec(evidence_id, video_id, start, end, label="Fighting"):
    return {"evidence_id": evidence_id, "video_id": video_id,
            "start_time": start, "end_time": end,
            "object_evidence": [], "generic_action_evidence": [],
            "surveillance_event_evidence": [_evt(evidence_id + ":e", label, 0.8)],
            "source_references": [f"{video_id}@t={start}s-{end}s"],
            "temporal_support": {}, "anomaly_score": 0.5}


def _mini():
    records = [_rec(f"{VA}:f0", VA, 0.0, 2.0), _rec(f"{VA}:f1", VA, 2.0, 4.0)]
    incidents = [{"incident_id": f"{VA}:i0", "video_id": VA, "start_time": 0.0,
                  "end_time": 4.0, "evidence_ids": [f"{VA}:f0", f"{VA}:f1"],
                  "event_hypotheses": ["Fighting"], "num_windows": 2,
                  "span_seconds": 4.0, "anomaly_score": 0.5,
                  "schema_version": "phase2d/v1"}]
    return records, incidents


def _settings():
    return {"provider": "mock", "model": "mock", "temperature": 0.0}


class OrchestrationTest(unittest.TestCase):
    def test_end_to_end_mock(self):
        records, incidents = _mini()
        bundle = R.run_question("Find Fighting", records, incidents, "mock",
                                None, _settings(), 6000, "mock")
        self.assertEqual(bundle["schema_version"], "phase4/v1")
        self.assertIsNone(bundle["failure"])
        self.assertEqual(bundle["validator_verdicts"],
                         {"3c": "pass", "3d": "pass", "3e": "pass", "3f": "pass"})
        self.assertIsNotNone(bundle["result_3f"])
        self.assertTrue(bundle["integrity_audit"]["overall_pass"])

    def test_stage_order_and_timing_keys(self):
        records, incidents = _mini()
        bundle = R.run_question("Find Fighting", records, incidents, "mock",
                                None, _settings(), 6000, "mock")
        self.assertEqual(set(bundle["timings"]),
                         {"3c", "3d", "3e", "3f", "total"})
        for value in bundle["timings"].values():
            self.assertGreaterEqual(value, 0.0)

    def test_mode_and_exposure(self):
        records, incidents = _mini()
        bundle = R.run_question("Find Fighting", records, incidents, "mock",
                                None, _settings(), 6000, "mock")
        self.assertEqual(bundle["mode"], "mock")
        self.assertEqual(bundle["model"], "mock")
        self.assertEqual(set(bundle["max_token_exposure"]), {"3c", "3e", "3f"})
        self.assertEqual(bundle["max_token_exposure"]["3f"], 6000)

    def test_failure_capture_skips_downstream(self):
        records, incidents = _mini()
        bundle = R.run_question("   ", records, incidents, "mock",
                                None, _settings(), 6000, "mock")
        self.assertIsNotNone(bundle["failure"])
        self.assertEqual(bundle["failure"]["stage"], "3c")
        self.assertIn(bundle["failure"]["type"], ("parse", "validation"))
        self.assertIsNone(bundle["result_3d"])
        self.assertIsNone(bundle["result_3e"])
        self.assertIsNone(bundle["result_3f"])
        self.assertEqual(bundle["validator_verdicts"]["3c"], "error")
        self.assertNotIn("3d", bundle["validator_verdicts"])

    def test_failure_taxonomy_values(self):
        for exc, expected in [
                (ValueError("bad plan"), "validation"),
                (RuntimeError("boom"), "other")]:
            self.assertEqual(R.classify_failure(exc), expected)

    def test_bundle_deterministic(self):
        records, incidents = _mini()
        first = R.run_question("Find Fighting", records, incidents, "mock",
                               None, _settings(), 6000, "mock")
        second = R.run_question("Find Fighting", records, incidents, "mock",
                                None, _settings(), 6000, "mock")
        scrub = lambda b: {k: v for k, v in b.items()
                           if k not in ("timings", "run_utc", "git_hash")}
        self.assertEqual(json.dumps(scrub(first), sort_keys=True, default=str),
                         json.dumps(scrub(second), sort_keys=True, default=str))


class IntegrityTest(unittest.TestCase):
    def test_ids_and_timestamps(self):
        records, incidents = _mini()
        bundle = R.run_question("Find Fighting", records, incidents, "mock",
                                None, _settings(), 6000, "mock")
        audit = bundle["integrity_audit"]
        self.assertTrue(audit["input_unchanged"])
        self.assertEqual(audit["base_records"], 2)
        self.assertEqual(audit["cross_video_violations"], 0)
        self.assertTrue(audit["overall_pass"])

    def test_input_not_mutated(self):
        records, incidents = _mini()
        before = copy.deepcopy(records)
        R.run_question("Find Fighting", records, incidents, "mock",
                       None, _settings(), 6000, "mock")
        self.assertEqual(records, before)

    def test_audit_catches_unknown_id(self):
        records, incidents = _mini()
        tampered = copy.deepcopy(records)
        audit = R.audit_integrity(
            records, tampered,
            {"merged_results": {"groups": [{
                "incident_id": "x", "video_id": VA, "matched_evidence": [
                    {"evidence_id": "ghost:e0", "video_id": VA, "start_time": 0.0,
                     "end_time": 1.0, "source_references": ["r"]}],
                "contextual_evidence": []}], "unmapped_hits": []}},
            None, None)
        self.assertFalse(audit["overall_pass"])
        self.assertEqual(audit["stages"]["3d"]["unknown_ids"], 1)

    def test_cross_list_reuse_is_valid(self):
        """Same ID in timeline + correlation + inference must NOT flag dupes."""
        records, incidents = _mini()
        eid = f"{VA}:f0"
        result_3e = {
            "timeline": [{"start_time": 0.0, "end_time": 2.0,
                          "evidence_ids": [eid],
                          "observation": {"text": "t", "evidence_ids": [eid]}}],
            "correlations": [{"type": "same_incident", "evidence_ids": [eid],
                              "description": "d"}],
            "inferences": [{"text": "i", "evidence_ids": [eid]}]}
        audit = R.audit_integrity(records, copy.deepcopy(records), None,
                                  result_3e, None)
        self.assertFalse(audit["stages"]["3e"]["duplicates"])
        self.assertTrue(audit["stages"]["3e"]["pass"])

    def test_within_list_duplicate_is_invalid(self):
        records, incidents = _mini()
        eid = f"{VA}:f0"
        result_3e = {
            "timeline": [],
            "correlations": [{"type": "same_incident",
                              "evidence_ids": [eid, eid],
                              "description": "d"}],
            "inferences": []}
        audit = R.audit_integrity(records, copy.deepcopy(records), None,
                                  result_3e, None)
        self.assertTrue(audit["stages"]["3e"]["duplicates"])
        self.assertFalse(audit["stages"]["3e"]["pass"])
        self.assertFalse(audit["overall_pass"])

    def test_nonempty_end_to_end_mock(self):
        """Single-word question retrieves real fixture evidence end to end."""
        records, incidents = _mini()
        bundle = R.run_question("Fighting", records, incidents, "mock",
                                None, _settings(), 6000, "mock")
        self.assertIsNone(bundle["failure"])
        matched = [r for g in bundle["result_3d"]["merged_results"]["groups"]
                   for r in g["matched_evidence"]]
        self.assertTrue(matched)
        self.assertTrue(bundle["result_3e"]["timeline"])
        self.assertTrue(bundle["result_3f"]["verification"])
        self.assertTrue(bundle["integrity_audit"]["overall_pass"])
        self.assertEqual(bundle["integrity_audit"]["stages"]["3e"]["duplicates"],
                         False)

    def test_reproducibility_metadata(self):
        records, incidents = _mini()
        bundle = R.run_question("Fighting", records, incidents, "mock",
                                None, _settings(), 6000, "mock",
                                "ev.json", "inc.json")
        self.assertEqual(set(bundle["settings"]), {"provider", "model", "temperature"})
        self.assertEqual(bundle["settings"]["temperature"], 0.0)
        self.assertEqual(bundle["inputs"]["evidence_path"], "ev.json")
        self.assertEqual(bundle["inputs"]["incidents_path"], "inc.json")
        self.assertEqual((bundle["inputs"]["records"], bundle["inputs"]["incidents"]),
                         (2, 1))
        blob = json.dumps(bundle)
        self.assertNotIn("MODEL_API_KEY", blob)


class EvaluateTest(unittest.TestCase):
    def _bundles(self):
        records, incidents = _mini()
        good = R.run_question("Find Fighting", records, incidents, "mock",
                              None, _settings(), 6000, "mock")
        bad = R.run_question("   ", records, incidents, "mock",
                             None, _settings(), 6000, "mock")
        return [good, bad]

    def test_offline_metrics(self):
        metrics = V.evaluate(self._bundles())
        self.assertEqual(metrics["total_runs"], 2)
        self.assertEqual(metrics["successful_runs"], 1)
        self.assertEqual(metrics["end_to_end_success_rate"], 0.5)
        self.assertIn("validation", metrics["failure_taxonomy"])
        self.assertIn("supported_structural_only", metrics)
        self.assertIn("3c", metrics["stage_latency"])
        self.assertIn("mean", metrics["total_latency"])
        self.assertNotIn("precision", json.dumps(metrics).lower())

    def test_no_forbidden_claims(self):
        metrics = V.evaluate(self._bundles())
        blob = json.dumps(metrics).lower()
        for word in ("precision", "recall", "intent accuracy", "crime detection",
                     "ranking quality"):
            self.assertNotIn(word, blob)

    def test_empty_bundles(self):
        metrics = V.evaluate([])
        self.assertEqual((metrics["total_runs"], metrics["successful_runs"]), (0, 0))

    def test_mixed_modes_rejected(self):
        def _bundle(mode):
            return {"schema_version": "phase4/v1", "mode": mode,
                    "failure": None, "validator_verdicts": {},
                    "result_3f": {"verification": []}, "result_3d": {"summary": {}},
                    "integrity_audit": {"stages": {}}, "timings": {},
                    "max_token_exposure": {}}

        with self.assertRaises(ValueError) as ctx:
            V.evaluate([_bundle("mock"), _bundle("real")])
        self.assertIn("mock", str(ctx.exception))
        single = V.evaluate([_bundle("mock"), _bundle("mock")])
        self.assertEqual(single["total_runs"], 2)

    def test_audit_pass_rate_and_3f_containment(self):
        metrics = V.evaluate(self._bundles())
        self.assertIn("audit_pass_rate", metrics)
        self.assertNotIn("id_preservation_rate", json.dumps(metrics))
        self.assertGreaterEqual(metrics["timestamp_containment_rate"], 0.0)

    def test_malformed_bundle_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "bad.json").write_text("{corrupt", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                V.load_bundles(Path(tmp))
            self.assertIn("bad.json", str(ctx.exception))

    def test_malformed_questions_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "q.json")
            path.write_text(json.dumps([{"id": "q01"}]), encoding="utf-8")
            with self.assertRaises(ValueError):
                R._load_questions(SimpleNamespace(questions_file=str(path),
                                                  question=None))
            path.write_text(json.dumps(["not-a-dict"]), encoding="utf-8")
            with self.assertRaises(ValueError):
                R._load_questions(SimpleNamespace(questions_file=str(path),
                                                  question=None))


class QueriesFileTest(unittest.TestCase):
    def test_eval_queries(self):
        path = Path(__file__).resolve().parent.parent / "eval" / "queries.json"
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(len(data), 8)
        ids = [e["id"] for e in data]
        self.assertEqual(len(set(ids)), 8)
        for entry in data:
            self.assertTrue(entry["question"].strip())

    def test_q01_targets_small_incident(self):
        path = Path(__file__).resolve().parent.parent / "eval" / "queries.json"
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        q01 = next(e for e in data if e["id"] == "q01")
        self.assertIn("Fighting006", q01["question"])
        self.assertNotIn("Fighting004", q01["question"])


if __name__ == "__main__":
    unittest.main()
