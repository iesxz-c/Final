"""Phase 4 api_eval tests: aggregation, stats, failures, usage, cost.

No network access; no MODEL_API_KEY required. Mock LLM only."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.pipeline import api_eval as A
from src.pipeline import run_investigation as R


VA = "anomaly/Robbery/vA.mp4"


def _rec(evidence_id, video_id, start, end, label="Fighting"):
    return {"evidence_id": evidence_id, "video_id": video_id,
            "start_time": start, "end_time": end,
            "object_evidence": [], "generic_action_evidence": [],
            "surveillance_event_evidence": [
                {"observation_id": evidence_id + ":e", "label": label,
                 "confidence": 0.8, "model_name": "m", "model_version": "v",
                 "top_k": [], "source_reference": evidence_id + ":e"}],
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


def _entry(qid="q01", question="Find Fighting"):
    return {"query_id": qid, "question": question, "expected_intent": "search_evidence",
            "video_constraint": None, "temporal_constraint": None, "purpose": "t"}


def _bundle(**over):
    records, incidents = _mini()
    bundle = R.run_question("Find Fighting", records, incidents, "mock",
                            None, _settings(), 6000, "mock")
    bundle.update(over)
    return bundle


def _claimed(bundle, statuses):
    items = [{"claim_id": f"claim_{i + 1:03d}", "claim": f"c{i}",
              "status": status, "evidence_ids": [f"{VA}:f0"],
              "reason": "r"} for i, status in enumerate(statuses)]
    bundle["result_3f"]["verification"] = items
    return bundle


def _meta():
    return {"benchmark_version": "api-benchmark/v1", "provider": "mock",
            "model": "mock", "endpoint": None, "git_revision": "t",
            "run_utc": "t", "n_questions": 1,
            "execution": {"temperature": 0.0, "timeout": None,
                          "max_tokens_3f": 6000, "pricing_supplied": False}}


class LatencyStatsTest(unittest.TestCase):
    def test_mean_median_p95_n(self):
        stats = A._latency_stats([1.0, 2.0, 3.0, 4.0])
        self.assertEqual(stats["n"], 4)
        self.assertEqual(stats["mean"], 2.5)
        self.assertEqual(stats["median"], 2.5)
        self.assertEqual(stats["p95"], 4.0)

    def test_p95_nearest_rank(self):
        values = [float(i) for i in range(1, 21)]
        self.assertEqual(A._latency_stats(values)["p95"], 19.0)
        self.assertEqual(A._latency_stats([7.0])["p95"], 7.0)

    def test_empty_omits_statistics(self):
        self.assertEqual(A._latency_stats([]), {"n": 0})


class RateTest(unittest.TestCase):
    def test_rate_shape(self):
        self.assertEqual(A._rate(3, 4),
                         {"value": 0.75, "numerator": 3, "denominator": 4})

    def test_zero_denominator_omitted(self):
        self.assertIsNone(A._rate(0, 0))
        self.assertIsNone(A._rate(5, 0))


class FailureTaxonomyTest(unittest.TestCase):
    def test_classification_reused(self):
        from src.agents.llm_client import LLMError, MissingAPIKeyError, ProviderError
        from src.agents.query_planner import PlanValidationError
        self.assertEqual(R.classify_failure(MissingAPIKeyError("k")), "provider")
        self.assertEqual(R.classify_failure(ProviderError("timed out after 1s")), "timeout")
        self.assertEqual(R.classify_failure(ProviderError("down")), "provider")
        self.assertEqual(R.classify_failure(LLMError("bad model")), "provider")
        self.assertEqual(R.classify_failure(ValueError("not valid JSON: x")), "parse")
        self.assertEqual(R.classify_failure(PlanValidationError("bad")), "validation")
        err = RuntimeError("store exploded")
        self.assertEqual(R.classify_failure(err), "other")

    def test_record_carries_failure_taxonomy(self):
        bundle = _bundle(failure={"stage": "3e", "type": "timeout", "error": "timed out"},
                         validator_verdicts={"3c": "pass", "3d": "pass", "3e": "error"})
        record = A.build_record(_entry(), bundle, [], None)
        self.assertEqual(record["api_status"], "timeout")
        self.assertEqual(record["failure"]["stage"], "3e")
        self.assertFalse(record["schema_valid"])


class SafetyBucketTest(unittest.TestCase):
    def _safety_bundle(self, phrase):
        return _bundle(failure={"stage": "3f", "type": "validation",
                                "error": f"report summary contains unsupported language: {phrase!r}"})

    def test_identity_bucket(self):
        counts = A._safety_counts(self._safety_bundle("suspect"))
        self.assertEqual(counts["identity"], 1)
        self.assertEqual(counts["causality"], 0)
        self.assertEqual(counts["unsupported_crime_confirmation"], 0)

    def test_causality_and_confirmation_buckets(self):
        counts = A._safety_counts(self._safety_bundle("led to"))
        self.assertEqual(counts["causality"], 1)
        counts = A._safety_counts(self._safety_bundle("definitely occurred"))
        self.assertEqual(counts["unsupported_crime_confirmation"], 1)

    def test_non_safety_failure_counts_zero(self):
        bundle = _bundle(failure={"stage": "3c", "type": "provider", "error": "down"})
        self.assertEqual(A._safety_counts(bundle),
                         {"identity": 0, "causality": 0,
                          "unsupported_crime_confirmation": 0})
        self.assertEqual(A._safety_counts(_bundle()),
                         {"identity": 0, "causality": 0,
                          "unsupported_crime_confirmation": 0})


class UsageCostTest(unittest.TestCase):
    def test_usage_captured_per_stage(self):
        usages = [{"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
                  {"input_tokens": 20, "output_tokens": 6, "total_tokens": 26},
                  None]
        record = A.build_record(_entry(), _bundle(), usages, None)
        self.assertEqual(record["token_usage"]["3c"]["input_tokens"], 10)
        self.assertEqual(record["token_usage"]["3e"]["output_tokens"], 6)
        self.assertIsNone(record["token_usage"]["3f"])
        self.assertIsNone(record["cost_usd"])

    def test_cost_computed_only_with_pricing(self):
        usages = [{"input_tokens": 1000, "output_tokens": 500, "total_tokens": 1500}]
        pricing = {"input_per_1k": 0.5, "output_per_1k": 2.0}
        self.assertEqual(A._cost_for(usages, pricing), 1.5)
        self.assertIsNone(A._cost_for(usages, None))
        self.assertEqual(A._cost_for([], pricing), 0.0)

    def test_missing_usage_aggregates_unavailable(self):
        record = A.build_record(_entry(), _bundle(), [], None)
        metrics = A.aggregate([record], [_bundle()], _meta())
        self.assertEqual(metrics["token_usage"]["status"], "unavailable")
        self.assertEqual(metrics["token_usage"]["investigations_with_usage"], 0)
        self.assertEqual(metrics["cost_usd"]["status"], "unavailable")
        self.assertIsNone(metrics["cost_usd"]["value"])

    def test_client_extracts_usage_block(self):
        from src.agents import llm_client as C

        envelope = {"output": [{"type": "message", "content": [
            {"type": "output_text", "text": "{}"}]}],
            "usage": {"input_tokens": 12, "output_tokens": 3, "total_tokens": 15}}
        fake = mock.MagicMock()
        fake.__enter__.return_value.read.return_value = json.dumps(envelope).encode()
        with mock.patch("src.agents.llm_client.load_env_file", lambda path=None: {}), \
             mock.patch("urllib.request.urlopen", return_value=fake):
            client = C.MetaDirectClient(api_key="k", model="m")
            client.generate_structured("s", "u")
        self.assertEqual(client.last_usage, {"input_tokens": 12, "output_tokens": 3,
                                             "total_tokens": 15})

    def test_missing_usage_block_is_none(self):
        from src.agents import llm_client as C

        envelope = {"output": [{"type": "message", "content": [
            {"type": "output_text", "text": "{}"}]}]}
        fake = mock.MagicMock()
        fake.__enter__.return_value.read.return_value = json.dumps(envelope).encode()
        with mock.patch("src.agents.llm_client.load_env_file", lambda path=None: {}), \
             mock.patch("urllib.request.urlopen", return_value=fake):
            client = C.MetaDirectClient(api_key="k", model="m")
            client.generate_structured("s", "u")
        self.assertIsNone(client.last_usage)


class AggregationTest(unittest.TestCase):
    def test_rates_claims_grounding(self):
        good_bundle = _claimed(_bundle(), ["supported", "supported", "unsupported"])
        good = A.build_record(_entry("q01"), good_bundle, [], None)
        bad = A.build_record(_entry("q02"), _bundle(
            failure={"stage": "3c", "type": "parse", "error": "not valid JSON"}), [], None)
        metrics = A.aggregate([good, bad], [good_bundle, _bundle()], _meta())
        self.assertEqual(metrics["total_investigations"], 2)
        self.assertEqual(metrics["successful_investigations"], 1)
        self.assertEqual(metrics["investigation_success_rate"],
                         {"value": 0.5, "numerator": 1, "denominator": 2})
        self.assertEqual(metrics["api_success_rate"],
                         {"value": 0.5, "numerator": 1, "denominator": 2})
        for key in ("supported_claim_rate", "grounding_rate",
                    "temporal_grounding_rate"):
            rate = metrics[key]
            self.assertIn("numerator", rate)
            self.assertIn("denominator", rate)
        self.assertIn("base", metrics)
        self.assertEqual(metrics["base"]["total_runs"], 2)

    def test_zero_denominator_rates_omitted(self):
        metrics = A.aggregate([], [], _meta())
        self.assertEqual(metrics["total_investigations"], 0)
        self.assertIsNone(metrics["investigation_success_rate"])
        self.assertIsNone(metrics["supported_claim_rate"])
        self.assertEqual(metrics["end_to_end_latency"], {"n": 0})

    def test_deterministic_bytes(self):
        records = [A.build_record(_entry("q02"), _bundle(), [], None),
                   A.build_record(_entry("q01"), _bundle(), [], None)]
        first = json.dumps(A.aggregate(records, [_bundle(), _bundle()], _meta()),
                           indent=2, sort_keys=True)
        second = json.dumps(A.aggregate(records, [_bundle(), _bundle()], _meta()),
                            indent=2, sort_keys=True)
        self.assertEqual(first, second)

    def test_metrics_schema_shape(self):
        bundle = _claimed(_bundle(), ["supported", "partially_supported"])
        record = A.build_record(_entry(), bundle, [], None)
        metrics = A.aggregate([record], [bundle], _meta())
        for key in ("investigation_success_rate", "3c_success_rate", "3e_success_rate",
                    "3f_success_rate", "api_success_rate", "schema_valid_response_rate",
                    "supported_claim_rate", "partial_claim_rate", "unsupported_claim_rate",
                    "grounding_rate", "temporal_grounding_rate"):
            rate = metrics[key]
            self.assertEqual(set(rate), {"value", "numerator", "denominator"}, key)
        for key in ("3c_latency", "3e_latency", "3f_latency", "end_to_end_latency"):
            self.assertIn("n", metrics[key], key)
        for key in ("identity_violation_count", "causality_violation_count",
                    "unsupported_crime_confirmation_violation_count"):
            self.assertIsInstance(metrics[key], int, key)
        self.assertIn("token_usage", metrics)
        self.assertIn("cost_usd", metrics)
        self.assertIn("meta", metrics)


class EmptyEvidenceShortCircuitTest(unittest.TestCase):
    def test_3e_skips_llm_on_empty_retrieval(self):
        from src.agents import timeline_correlation as E
        from src.agents.llm_client import MockLLMClient

        empty_3d = {"schema_version": "phase3d/v1",
                    "merged_results": {"groups": []}}
        client = MockLLMClient('{"never": "used"}')
        out = E.run_timeline(client, empty_3d, "Relate X to Y")
        self.assertEqual((out["timeline"], out["correlations"], out["inferences"]),
                         ([], [], []))
        self.assertEqual(client.calls, [])

    def test_3f_skips_llm_when_no_claims(self):
        from src.agents import verification_report as F
        from src.agents.llm_client import MockLLMClient

        empty_3e = {"schema_version": "phase3e/v1", "timeline": [],
                    "correlations": [], "inferences": [], "limitations": ["none"]}
        empty_3d = {"schema_version": "phase3d/v1",
                    "merged_results": {"groups": []}}
        client = MockLLMClient('{"never": "used"}')
        out = F.run_verification_report(client, empty_3e, empty_3d, "Relate X to Y")
        self.assertEqual(out["verification"], [])
        self.assertEqual(client.calls, [])

    def test_record_distinguishes_shortcircuit_from_call(self):
        usage = {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}
        record = A.build_record(_entry(), _bundle(), [usage], None)
        self.assertEqual(record["llm_called"],
                         {"3c": True, "3e": False, "3f": False})
        self.assertIsNone(record["failure"])
        self.assertIsNone(record["token_usage"]["3e"])
        record3 = A.build_record(_entry(), _bundle(), [usage, usage, usage], None)
        self.assertEqual(record3["llm_called"],
                         {"3c": True, "3e": True, "3f": True})


class RecordingClientTest(unittest.TestCase):
    def test_delegates_and_snapshots_usage(self):
        from src.agents.llm_client import MockLLMClient

        delegate = MockLLMClient(['{"a": 1}'])
        delegate.last_usage = {"input_tokens": 4, "output_tokens": 2, "total_tokens": 6}
        client = A.RecordingClient(delegate)
        out = client.generate_structured("s", "u", temperature=0.0,
                                         response_format={"type": "json_object"},
                                         max_tokens=9)
        self.assertEqual(out, '{"a": 1}')
        self.assertEqual(client.usages, [{"input_tokens": 4, "output_tokens": 2,
                                          "total_tokens": 6}])
        self.assertEqual(delegate.calls[0]["max_tokens"], 9)

    def test_none_usage_recorded_when_absent(self):
        from src.agents.llm_client import MockLLMClient

        client = A.RecordingClient(MockLLMClient("{}"))
        client.generate_structured("s", "u")
        self.assertEqual(client.usages, [None])


class MockBenchmarkEndToEndTest(unittest.TestCase):
    def test_mock_benchmark_writes_artifacts(self):
        records, incidents = _mini()
        entries = [_entry("q01", "Find Fighting"), _entry("q02", "Show person")]
        settings = _settings()
        meta = _meta()
        meta["n_questions"] = 2
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "v1"
            metrics = A.run_benchmark(entries, records, incidents, "mock",
                                      lambda: None, settings, 6000, out, None, meta)
            self.assertEqual(metrics["total_investigations"], 2)
            self.assertEqual(metrics["successful_investigations"], 2)
            for qid in ("q01", "q02"):
                self.assertTrue((out / f"{qid}.json").exists())
                record = json.loads((out / f"{qid}.api.json").read_text(encoding="utf-8"))
                self.assertEqual(record["schema_version"], "api-eval/v1")
                self.assertEqual(record["query_id"], qid)
                self.assertIsNone(record["failure"])
            saved = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["total_investigations"], 2)

    def test_no_secrets_in_artifacts(self):
        sentinel = "sentinel-model-key-999"
        os.environ["MODEL_API_KEY"] = sentinel
        try:
            records, incidents = _mini()
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "v1"
                A.run_benchmark([_entry()], records, incidents, "mock",
                                lambda: None, _settings(), 6000, out, None, _meta())
                blob = "".join(p.read_text(encoding="utf-8") for p in out.glob("*.json"))
        finally:
            os.environ.pop("MODEL_API_KEY", None)
        self.assertNotIn(sentinel, blob)
        self.assertNotIn("Authorization", blob)


class SelectEntriesTest(unittest.TestCase):
    def test_subset_and_order_preserved(self):
        entries = [_entry("q01", "a"), _entry("q02", "b"), _entry("q03", "c")]
        picked = A.select_entries(entries, "q03,q01")
        self.assertEqual([e["query_id"] for e in picked], ["q01", "q03"])

    def test_none_returns_all(self):
        entries = [_entry("q01", "a")]
        self.assertEqual(A.select_entries(entries, None), entries)

    def test_unknown_id_rejected(self):
        with self.assertRaises(ValueError):
            A.select_entries([_entry("q01", "a")], "q99")


class CombineBenchmarkTest(unittest.TestCase):
    def _write_dir(self, path, qids, failures=()):
        path.mkdir(parents=True, exist_ok=True)
        records, incidents = _mini()
        bundles = []
        api_records = []
        for qid in qids:
            bundle = R.run_question("Find Fighting", records, incidents, "mock",
                                    None, _settings(), 6000, "mock")
            if qid in failures:
                bundle["failure"] = {"stage": "3e", "type": "timeout", "error": "t"}
            entry = _entry(qid, "Find Fighting")
            record = A.build_record(entry, bundle, [], None)
            bundles.append(bundle)
            api_records.append(record)
            (path / f"{qid}.json").write_text(json.dumps(bundle), encoding="utf-8")
            (path / f"{qid}.api.json").write_text(json.dumps(record), encoding="utf-8")
        meta = _meta()
        (path / "metrics.json").write_text(
            json.dumps({"meta": meta}), encoding="utf-8")
        return bundles, api_records

    def test_combine_takes_rerun_for_listed_ids(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            self._write_dir(tmp / "orig", ["q01", "q02"], failures=("q02",))
            self._write_dir(tmp / "re", ["q02"])
            meta = _meta()
            metrics = A.combine_benchmark(tmp / "orig", tmp / "re", ["q02"],
                                          tmp / "final", meta)
            self.assertEqual(metrics["total_investigations"], 2)
            self.assertEqual(metrics["successful_investigations"], 2)
            final_q02 = json.loads((tmp / "final" / "q02.api.json").read_text(
                encoding="utf-8"))
            self.assertIsNone(final_q02["failure"])
            self.assertTrue((tmp / "final" / "q01.json").exists())

    def test_only_subset_executes(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sub"
            code = A.main(["--mock", "--only", "q02",
                           "--benchmark", "eval/api_benchmark_v1.json",
                           "--output-dir", str(out)])
            self.assertEqual(code, 0)
            self.assertFalse((out / "q01.json").exists())
            self.assertTrue((out / "q02.json").exists())
            metrics = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(metrics["total_investigations"], 1)

    def test_timeout_conflict_rejected(self):
        code = A.main(["--mock", "--timeout", "5", "--no-total-timeout",
                       "--output-dir", "unused"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
