"""Phase 3E tests: timeline validation, correlation facts, grounding.

Synthetic fixtures only - no OpenRouter, no API key, mock LLM only."""

import json
import os
import unittest

from src.agents import timeline_correlation as E
from src.agents.llm_client import MockLLMClient, ProviderError

VA = "anomaly/Robbery/vA.mp4"
VB = "anomaly/Shoplifting/vB.mp4"


def _hit(evidence_id, video_id, start, end, source, label, conf=0.8):
    return {"video_id": video_id, "evidence_id": evidence_id,
            "start_time": start, "end_time": end, "matched_source": source,
            "matched_id": evidence_id + ":m0", "matched_label": label,
            "confidence": conf, "source_reference": f"{video_id}@t={start}s",
            "anomaly_score": 0.5, "planner_query_index": 0,
            "planner_query": label}


def _rec(evidence_id, video_id, start, end, kinds=(), label="Fighting", conf=0.8):
    rec = {"evidence_id": evidence_id, "video_id": video_id,
           "start_time": start, "end_time": end, "object_evidence": [],
           "generic_action_evidence": [], "surveillance_event_evidence": [],
           "source_references": [f"{video_id}@t={start}s-{end}s"],
           "temporal_support": {}, "anomaly_score": 0.5, "matched_hits": []}
    if "object" in kinds:
        rec["object_evidence"] = [
            {"detection_id": evidence_id + ":d0", "observation_id": evidence_id,
             "timestamp_seconds": start, "class_name": "person",
             "confidence": 0.9, "bounding_box": [1, 2, 3, 4], "model_name": "y"}]
    if "action" in kinds:
        rec["generic_action_evidence"] = [
            {"observation_id": evidence_id + ":a", "label": "walking",
             "confidence": 0.6, "model_name": "m", "model_version": "v",
             "top_k": [], "source_reference": rec["source_references"][0]}]
    if "event" in kinds:
        rec["surveillance_event_evidence"] = [
            {"observation_id": evidence_id + ":e", "label": label,
             "confidence": conf, "model_name": "m", "model_version": "v",
             "top_k": [], "source_reference": rec["source_references"][0]}]
        rec["matched_hits"] = [_hit(evidence_id, video_id, start, end,
                                    "surveillance_event", label, conf)]
    return rec


def _fixtures():
    f0 = _rec(f"{VA}:f0", VA, 10.0, 12.0, ("object", "event"))
    f1 = _rec(f"{VA}:f1", VA, 12.0, 14.0, ("event",))
    f2 = _rec(f"{VA}:f2", VA, 14.0, 16.0, ())
    f3 = _rec(f"{VA}:f3", VA, 100.0, 102.0, ("event",), label="Assault")
    g0 = _rec(f"{VB}:g0", VB, 1.0, 3.0, ("event",))
    groups = [
        {"incident_id": f"{VA}:i0", "video_id": VA, "incident_start_time": 10.0,
         "incident_end_time": 16.0, "event_hypotheses": ["Fighting"],
         "matched_evidence": [f0, f1], "contextual_evidence": [f2]},
        {"incident_id": f"{VA}:i1", "video_id": VA, "incident_start_time": 100.0,
         "incident_end_time": 102.0, "event_hypotheses": ["Assault"],
         "matched_evidence": [f3], "contextual_evidence": []},
        {"incident_id": f"{VB}:j0", "video_id": VB, "incident_start_time": 1.0,
         "incident_end_time": 3.0, "event_hypotheses": ["Fighting"],
         "matched_evidence": [g0], "contextual_evidence": []},
    ]
    return {"schema_version": "phase3d/v1", "plan": {}, "query_results": [],
            "merged_results": {"groups": groups, "unmapped_hits": []},
            "summary": {}}


def _out(timeline=(), correlations=(), inferences=(), limitations=("lim",)):
    return json.dumps({"schema_version": "phase3e/v1", "timeline": list(timeline),
                       "correlations": list(correlations),
                       "inferences": list(inferences),
                       "limitations": list(limitations)})


def _item(start, end, ids, text="obs"):
    return {"start_time": start, "end_time": end, "evidence_ids": list(ids),
            "observation": {"text": text, "evidence_ids": list(ids)}}


def _corr(ctype, ids, text="desc"):
    return {"type": ctype, "evidence_ids": list(ids), "description": text}


def _inf(ids, text="inf"):
    return {"text": text, "evidence_ids": list(ids)}


def _run(response, result=None):
    result = result if result is not None else _fixtures()
    return E.run_timeline(MockLLMClient(response), result)


class ValidTest(unittest.TestCase):
    def test_valid_timeline(self):
        out = _run(_out(timeline=[_item(10.0, 14.0, [f"{VA}:f0", f"{VA}:f1"])]))
        self.assertEqual(len(out["timeline"]), 1)
        self.assertEqual(out["timeline"][0]["evidence_ids"], [f"{VA}:f0", f"{VA}:f1"])

    def test_temporal_overlap(self):
        out = _run(_out(correlations=[_corr("temporal_overlap", [f"{VA}:f0", f"{VA}:f1"])]))
        self.assertEqual(out["correlations"][0]["type"], "temporal_overlap")

    def test_temporal_sequence(self):
        out = _run(_out(correlations=[_corr("temporal_sequence", [f"{VA}:f0", f"{VA}:f3"])]))
        self.assertEqual(out["correlations"][0]["type"], "temporal_sequence")

    def test_same_incident(self):
        out = _run(_out(correlations=[_corr("same_incident", [f"{VA}:f0", f"{VA}:f1"])]))
        self.assertEqual(out["correlations"][0]["type"], "same_incident")

    def test_cross_source(self):
        out = _run(_out(correlations=[_corr("cross_source_support", [f"{VA}:f0", f"{VA}:f1"])]))
        self.assertEqual(out["correlations"][0]["type"], "cross_source_support")

    def test_persistent_event(self):
        out = _run(_out(correlations=[_corr("persistent_event", [f"{VA}:f0", f"{VA}:f1"])]))
        self.assertEqual(out["correlations"][0]["type"], "persistent_event")

    def test_grounded_inference(self):
        out = _run(_out(inferences=[_inf([f"{VA}:f0", f"{VA}:f1"],
                                          "The evidence indicates persistence.")]))
        self.assertIn("evidence indicates", out["inferences"][0]["text"])


class RejectionTest(unittest.TestCase):
    def _rejects(self, response, result=None):
        with self.assertRaises(E.TimelineValidationError):
            _run(response, result)

    def test_unknown_type(self):
        self._rejects(_out(correlations=[_corr("causal_proof", [f"{VA}:f0"])]))

    def test_unknown_evidence_id(self):
        self._rejects(_out(timeline=[_item(0.0, 1.0, ["nope:e0"])]))

    def test_invented_timestamp(self):
        self._rejects(_out(timeline=[_item(10.0, 14.0, [f"{VA}:f3"])]))

    def test_range_outside_evidence(self):
        self._rejects(_out(timeline=[_item(5.0, 20.0, [f"{VA}:f0", f"{VA}:f1"])]))

    def test_empty_evidence_ids(self):
        self._rejects(_out(timeline=[_item(10.0, 12.0, [])]))

    def test_duplicate_evidence_ids(self):
        self._rejects(_out(timeline=[_item(10.0, 12.0, [f"{VA}:f0", f"{VA}:f0"])]))

    def test_empty_observation(self):
        bad = _item(10.0, 12.0, [f"{VA}:f0"], text="  ")
        self._rejects(_out(timeline=[bad]))

    def test_empty_inference(self):
        self._rejects(_out(inferences=[_inf([f"{VA}:f0"], text=" ")]))

    def test_malformed_json(self):
        self._rejects("{not json")

    def test_empty_response(self):
        self._rejects("   ")

    def test_unknown_fields(self):
        data = json.loads(_out())
        data["crime_probability"] = 0.9
        self._rejects(json.dumps(data))
        data = json.loads(_out())
        data["temporal_relationships"] = []
        with self.assertRaises(E.TimelineValidationError) as ctx:
            _run(json.dumps(data))
        self.assertIn("temporal_relationships", str(ctx.exception))
        bad = _item(10.0, 12.0, [f"{VA}:f0"])
        bad["suspect"] = "x"
        self._rejects(_out(timeline=[bad]))

    def test_cross_video_rejected(self):
        self._rejects(_out(correlations=[_corr("temporal_overlap", [f"{VA}:f0", f"{VB}:g0"])]))
        self._rejects(_out(timeline=[_item(1.0, 12.0, [f"{VA}:f0", f"{VB}:g0"])]))
        self._rejects(_out(inferences=[_inf([f"{VA}:f0", f"{VB}:g0"])]))

    def test_false_overlap_rejected(self):
        self._rejects(_out(correlations=[_corr("temporal_overlap", [f"{VA}:f0", f"{VA}:f3"])]))

    def test_false_same_incident_rejected(self):
        self._rejects(_out(correlations=[_corr("same_incident", [f"{VA}:f0", f"{VA}:f3"])]))

    def test_false_cross_source_rejected(self):
        self._rejects(_out(correlations=[_corr("cross_source_support", [f"{VA}:f1", f"{VA}:f3"])]))

    def test_end_before_start_rejected(self):
        self._rejects(_out(timeline=[_item(14.0, 12.0, [f"{VA}:f0"])]))

    def test_negative_start_rejected(self):
        self._rejects(_out(timeline=[_item(-1.0, 12.0, [f"{VA}:f0"])]))


class IntegrityTest(unittest.TestCase):
    def test_preservation(self):
        res = _fixtures()
        out = _run(_out(timeline=[_item(10.0, 14.0, [f"{VA}:f0", f"{VA}:f1"])],
                        inferences=[_inf([f"{VA}:f0"])]), res)
        self.assertEqual(out["timeline"][0]["observation"]["evidence_ids"],
                         [f"{VA}:f0", f"{VA}:f1"])
        serial = E.serialize_for_llm(res)
        flat = {e["evidence_id"]: e for i in serial["incidents"] for e in i["evidence"]}
        self.assertEqual(flat[f"{VA}:f0"]["source_references"],
                         [f"{VA}@t=10.0s-12.0s"])

    def test_deterministic_ordering(self):
        res = _fixtures()
        first = E.serialize_for_llm(res)
        rev = {"schema_version": "phase3d/v1",
               "merged_results": {"groups": list(reversed(res["merged_results"]["groups"])),
                                  "unmapped_hits": []}}
        second = E.serialize_for_llm(rev)
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))
        c1, c2 = MockLLMClient(_out()), MockLLMClient(_out())
        E.run_timeline(c1, res)
        E.run_timeline(c2, rev)
        self.assertEqual(c1.calls[0]["user_prompt"], c2.calls[0]["user_prompt"])

    def test_incidents_separated(self):
        serial = E.serialize_for_llm(_fixtures())
        self.assertEqual(len(serial["incidents"]), 3)
        by_incident = {i["incident_id"]: i for i in serial["incidents"]}
        self.assertEqual({e["evidence_id"] for e in by_incident[f"{VA}:i0"]["evidence"]},
                         {f"{VA}:f0", f"{VA}:f1", f"{VA}:f2"})
        for incident in serial["incidents"]:
            self.assertEqual(len({e["evidence_id"] for e in incident["evidence"]}),
                             len(incident["evidence"]))

    def test_empty_input_safe(self):
        client = MockLLMClient(_out())
        out = E.run_timeline(client, {"schema_version": "phase3d/v1",
                                      "merged_results": {"groups": [], "unmapped_hits": []}})
        self.assertEqual((out["timeline"], out["correlations"], out["inferences"]), ([], [], []))
        self.assertTrue(out["limitations"])
        self.assertEqual(client.calls, [])

    def test_provider_error(self):
        with self.assertRaises(ProviderError):
            E.run_timeline(MockLLMClient("{}", error=ProviderError("down")), _fixtures())

    def test_no_leakage(self):
        sentinel = "sk-test-sentinel-3e"
        os.environ["OPENROUTER_API_KEY"] = sentinel
        try:
            out = _run(_out(inferences=[_inf([f"{VA}:f0"])]))
            self.assertNotIn(sentinel, json.dumps(out))
            with self.assertRaises(ProviderError) as ctx:
                E.run_timeline(MockLLMClient("x", error=ProviderError("down")), _fixtures())
            self.assertNotIn(sentinel, str(ctx.exception))
        finally:
            os.environ.pop("OPENROUTER_API_KEY", None)

    def test_schema_and_format(self):
        self.assertFalse(E.TIMELINE_JSON_SCHEMA["additionalProperties"])
        self.assertEqual(E.TIMELINE_JSON_SCHEMA["properties"]["correlations"]
                         ["items"]["properties"]["type"]["enum"], list(E.CORRELATION_TYPES))
        client = MockLLMClient(_out())
        E.run_timeline(client, _fixtures())
        fmt = client.calls[0]["response_format"]
        self.assertEqual(fmt["type"], "json_schema")
        self.assertTrue(fmt["json_schema"]["strict"])
        self.assertEqual(client.calls[0]["temperature"], 0.0)
        self.assertEqual(client.calls[0]["max_tokens"], E.MAX_TOKENS)
        for phrase in ("reason ONLY over the supplied evidence",
                       "must not invent", "Return only the required JSON",
                       "MUST contain exactly these five top-level keys",
                       "temporal_relationships"):
            self.assertIn(phrase, E.SYSTEM_PROMPT)
        for key in ("timeline", "correlations", "inferences", "limitations",
                    "schema_version"):
            self.assertIn(key, E.SYSTEM_PROMPT)

    def test_bad_3d_input_rejected(self):
        with self.assertRaises(E.TimelineValidationError):
            E.run_timeline(MockLLMClient(_out()), {"schema_version": "phase3d/v0",
                                                   "merged_results": {}})
        with self.assertRaises(E.TimelineValidationError):
            E.run_timeline(MockLLMClient(_out()), ["not", "a", "dict"])


class ModelComparisonContractTest(unittest.TestCase):
    MODELS = ("qwen/qwen3-30b-a3b-instruct-2507", "meta/muse-spark-1.3")

    def test_each_configured_model_uses_identical_phase3e_request(self):
        calls = []
        for model in self.MODELS:
            client = MockLLMClient(_out())
            client.model = model
            output = E.run_timeline(client, _fixtures())
            self.assertEqual(output["schema_version"], E.SCHEMA_VERSION)
            calls.append(client.calls[0])
        self.assertEqual(calls[0], calls[1])
        self.assertEqual(calls[0]["max_tokens"], 4096)
        self.assertEqual(calls[0]["response_format"], E.timeline_response_format())
        self.assertTrue(calls[0]["response_format"]["json_schema"]["strict"])

    def test_validator_rejects_unknown_field_for_each_model(self):
        bad = json.loads(_out())
        bad["temporal_relationships"] = []
        for model in self.MODELS:
            client = MockLLMClient(json.dumps(bad))
            client.model = model
            with self.assertRaises(E.TimelineValidationError):
                E.run_timeline(client, _fixtures())


class ConsolidationTest(unittest.TestCase):
    def _index(self):
        return E.collect_evidence_index(_fixtures())

    def test_adjacent_windows_one_item(self):
        ids = [f"{VA}:f0", f"{VA}:f1", f"{VA}:f2"]
        out = E.parse_and_validate_timeline(
            _out(timeline=[_item(10.0, 16.0, ids, text="Persistent.")]),
            self._index())
        self.assertEqual(len(out["timeline"]), 1)
        self.assertEqual(out["timeline"][0]["evidence_ids"], ids)

    def test_consolidated_range_grounded(self):
        ids = [f"{VA}:f0", f"{VA}:f1"]
        out = E.parse_and_validate_timeline(
            _out(timeline=[_item(10.0, 14.0, ids)]), self._index())
        item = out["timeline"][0]
        self.assertGreaterEqual(item["start_time"], 10.0)
        self.assertLessEqual(item["end_time"], 14.0)

    def test_consolidated_range_outside_rejected(self):
        ids = [f"{VA}:f0", f"{VA}:f1"]
        with self.assertRaises(E.TimelineValidationError):
            E.parse_and_validate_timeline(
                _out(timeline=[_item(5.0, 20.0, ids)]), self._index())

    def test_prompt_requires_concise_consolidation(self):
        for phrase in ("consolidat", "concise"):
            self.assertIn(phrase, E.SYSTEM_PROMPT.lower())


if __name__ == "__main__":
    unittest.main()
