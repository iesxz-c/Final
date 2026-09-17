"""Phase 3F tests: verification grounding, report rules, language safety.

Synthetic fixtures only - no Meta API, no API key, mock LLM only."""

import json
import os
import unittest

from src.agents import verification_report as F
from src.agents.llm_client import MockLLMClient, ProviderError

VA = "anomaly/Robbery/vA.mp4"
VB = "anomaly/Shoplifting/vB.mp4"


def _rec(evidence_id, video_id, start, end, kinds=()):
    rec = {"evidence_id": evidence_id, "video_id": video_id,
           "start_time": start, "end_time": end, "object_evidence": [],
           "generic_action_evidence": [], "surveillance_event_evidence": [],
           "source_references": [f"{video_id}@t={start}s-{end}s"],
           "temporal_support": {}, "anomaly_score": 0.5}
    if "object" in kinds:
        rec["object_evidence"] = [
            {"detection_id": evidence_id + ":d0", "observation_id": evidence_id,
             "timestamp_seconds": start, "class_name": "person",
             "confidence": 0.9, "bounding_box": [1, 2, 3, 4], "model_name": "y"}]
    if "event" in kinds:
        rec["surveillance_event_evidence"] = [
            {"observation_id": evidence_id + ":e", "label": "Fighting",
             "confidence": 0.8, "model_name": "m", "model_version": "v",
             "top_k": [], "source_reference": rec["source_references"][0]}]
    return rec


def _hit(evidence_id, video_id, start, end, source="surveillance_event"):
    return {"video_id": video_id, "evidence_id": evidence_id,
            "start_time": start, "end_time": end, "matched_source": source,
            "matched_id": evidence_id + ":m", "matched_label": "x",
            "confidence": 0.8, "source_reference": "r", "anomaly_score": 0.5}


def _fixtures_3d():
    f0 = _rec(f"{VA}:f0", VA, 0.0, 2.0, ("object", "event"))
    f1 = _rec(f"{VA}:f1", VA, 2.0, 4.0, ("event",))
    g0 = _rec(f"{VB}:g0", VB, 1.0, 3.0, ("event",))
    f0["matched_hits"] = [_hit(f0["evidence_id"], VA, 0.0, 2.0)]
    f1["matched_hits"] = [_hit(f1["evidence_id"], VA, 2.0, 4.0)]
    g0["matched_hits"] = [_hit(g0["evidence_id"], VB, 1.0, 3.0)]
    groups = [
        {"incident_id": f"{VA}:i0", "video_id": VA, "incident_start_time": 0.0,
         "incident_end_time": 4.0, "event_hypotheses": ["Fighting"],
         "matched_evidence": [f0, f1], "contextual_evidence": []},
        {"incident_id": f"{VB}:j0", "video_id": VB, "incident_start_time": 1.0,
         "incident_end_time": 3.0, "event_hypotheses": ["Fighting"],
         "matched_evidence": [g0], "contextual_evidence": []},
    ]
    unmapped = [_hit(f"{VA}:f9", VA, 50.0, 52.0)]
    return {"schema_version": "phase3d/v1", "plan": {}, "query_results": [],
            "merged_results": {"groups": groups, "unmapped_hits": unmapped},
            "summary": {}}


def _fixtures_3e():
    return {
        "schema_version": "phase3e/v1",
        "timeline": [{"start_time": 0.0, "end_time": 4.0,
                      "evidence_ids": [f"{VA}:f0", f"{VA}:f1"],
                      "observation": {"text": "Activity persists.",
                                      "evidence_ids": [f"{VA}:f0", f"{VA}:f1"]}}],
        "correlations": [{"type": "same_incident",
                          "evidence_ids": [f"{VA}:f0", f"{VA}:f1"],
                          "description": "Same incident members."}],
        "inferences": [{"text": "The evidence indicates persistence.",
                        "evidence_ids": [f"{VA}:f0"]}],
        "limitations": ["Labels are hypotheses."],
    }


def _good():
    return {"schema_version": "phase3f/v1",
            "verification": [
                {"claim_id": "claim_001", "claim": "Activity persists.",
                 "status": "supported", "evidence_ids": [f"{VA}:f0", f"{VA}:f1"],
                 "reason": "Both windows show it."},
                {"claim_id": "claim_002", "claim": "same_incident: Same incident members.",
                 "status": "supported", "evidence_ids": [f"{VA}:f0", f"{VA}:f1"],
                 "reason": "Shared incident."},
                {"claim_id": "claim_003", "claim": "The evidence indicates persistence.",
                 "status": "supported", "evidence_ids": [f"{VA}:f0"],
                 "reason": "Directly observed."}],
            "report": {"title": "Incident review",
                       "summary": "The evidence indicates activity in 0-4s.",
                       "timeline": [{"start_time": 0.0, "end_time": 2.0,
                                     "description": "Activity in the first window.",
                                     "evidence_ids": [f"{VA}:f0"]}],
                       "findings": [{"text": "The retrieved evidence supports persistence.",
                                     "evidence_ids": [f"{VA}:f0", f"{VA}:f1"]}],
                       "limitations": ["Labels are hypotheses."]}}


def _index():
    from src.agents.timeline_correlation import collect_evidence_index

    return collect_evidence_index(_fixtures_3d())


def _claims():
    return ["claim_001", "claim_002", "claim_003"]


def _validate(data):
    return F.parse_and_validate_report(json.dumps(data), _index(), _claims())


class ValidTest(unittest.TestCase):
    def test_valid_output(self):
        out = _validate(_good())
        self.assertEqual(out["schema_version"], "phase3f/v1")
        self.assertEqual(len(out["verification"]), 3)
        self.assertEqual(out["report"]["title"], "Incident review")

    def test_exact_top_level_keys(self):
        out = _validate(_good())
        self.assertEqual(set(out), {"schema_version", "verification", "report"})

    def test_supported_accepted(self):
        out = _validate(_good())
        self.assertTrue(all(v["status"] == "supported" for v in out["verification"]))

    def test_partially_supported_accepted(self):
        data = _good()
        data["verification"][0]["status"] = "partially_supported"
        out = _validate(data)
        self.assertEqual(out["verification"][0]["status"], "partially_supported")

    def test_unsupported_preserved(self):
        data = _good()
        data["verification"][0].update(status="unsupported", evidence_ids=[],
                                       reason="Nothing shows this.")
        out = _validate(data)
        self.assertEqual(out["verification"][0]["status"], "unsupported")
        self.assertEqual(out["verification"][0]["evidence_ids"], [])


class RejectionTest(unittest.TestCase):
    def _rejects(self, data):
        with self.assertRaises(F.ReportValidationError):
            _validate(data)

    def test_unknown_top_level(self):
        data = _good()
        data["extra"] = 1
        self._rejects(data)

    def test_unknown_nested(self):
        data = _good()
        data["verification"][0]["score"] = 1.0
        self._rejects(data)
        data = _good()
        data["report"]["findings"][0]["author"] = "x"
        self._rejects(data)

    def test_wrong_schema(self):
        data = _good()
        data["schema_version"] = "phase3f/v0"
        self._rejects(data)

    def test_bad_status(self):
        data = _good()
        data["verification"][0]["status"] = "confirmed"
        self._rejects(data)

    def test_unknown_evidence(self):
        data = _good()
        data["verification"][0]["evidence_ids"] = ["ghost:e0"]
        self._rejects(data)
        data = _good()
        data["report"]["findings"][0]["evidence_ids"] = ["ghost:e0"]
        self._rejects(data)

    def test_duplicate_evidence(self):
        data = _good()
        data["verification"][0]["evidence_ids"] = [f"{VA}:f0", f"{VA}:f0"]
        self._rejects(data)

    def test_bad_timestamp(self):
        data = _good()
        data["report"]["timeline"][0]["start_time"] = -1.0
        self._rejects(data)
        data = _good()
        data["report"]["timeline"][0]["start_time"] = "soon"
        self._rejects(data)

    def test_start_after_end(self):
        data = _good()
        data["report"]["timeline"][0].update(start_time=2.0, end_time=1.0)
        self._rejects(data)

    def test_ungrounded_range(self):
        data = _good()
        data["report"]["timeline"][0].update(start_time=0.0, end_time=99.0)
        self._rejects(data)

    def test_cross_video_timeline(self):
        data = _good()
        data["report"]["timeline"][0]["evidence_ids"] = [f"{VA}:f0", f"{VB}:g0"]
        self._rejects(data)

    def test_duplicate_claim_ids(self):
        data = _good()
        data["verification"][1]["claim_id"] = "claim_001"
        self._rejects(data)

    def test_empty_claim(self):
        data = _good()
        data["verification"][0]["claim"] = "  "
        self._rejects(data)

    def test_empty_reason(self):
        data = _good()
        data["verification"][0]["reason"] = ""
        self._rejects(data)

    def test_supported_empty_evidence_rejected(self):
        data = _good()
        data["verification"][0]["evidence_ids"] = []
        self._rejects(data)

    def test_finding_without_evidence(self):
        data = _good()
        data["report"]["findings"][0]["evidence_ids"] = []
        self._rejects(data)

    def test_missing_claim_rejected(self):
        data = _good()
        data["verification"] = data["verification"][:2]
        self._rejects(data)

    def test_extra_claim_rejected(self):
        data = _good()
        data["verification"].append({"claim_id": "claim_999", "claim": "New.",
                                     "status": "supported",
                                     "evidence_ids": [f"{VA}:f0"], "reason": "R."})
        self._rejects(data)

    def test_malformed_json(self):
        with self.assertRaises(F.ReportValidationError):
            F.parse_and_validate_report("{nope", _index(), _claims())

    def test_empty_response(self):
        with self.assertRaises(F.ReportValidationError):
            F.parse_and_validate_report("  ", _index(), _claims())

    def test_unsupported_claim_as_finding_rejected(self):
        data = _good()
        data["verification"][0].update(status="unsupported", evidence_ids=[],
                                       reason="Nothing shows this.")
        data["report"]["findings"][0]["text"] = "Activity persists."
        self._rejects(data)


class LanguageTest(unittest.TestCase):
    def _rejects_text(self, text):
        data = _good()
        data["report"]["findings"][0]["text"] = text
        with self.assertRaises(F.ReportValidationError):
            _validate(data)

    def test_identity_terms_rejected(self):
        for text in ("The suspect fled.", "A victim was seen.", "The perpetrator ran.",
                     "The offender left."):
            self._rejects_text(text)

    def test_causality_terms_rejected(self):
        for text in ("This proves guilt.", "It definitely occurred.",
                     "The fight caused panic.", "One event led to another."):
            self._rejects_text(text)

    def test_cautious_language_accepted(self):
        data = _good()
        data["report"]["findings"][0]["text"] = (
            "The evidence indicates activity consistent with the hypothesis.")
        out = _validate(data)
        self.assertTrue(out["report"]["findings"])


class IntegrationTest(unittest.TestCase):
    def _valid_client(self, res3e=None, res3d=None):
        from src.agents.timeline_correlation import collect_evidence_index

        res3e = res3e if res3e is not None else _fixtures_3e()
        res3d = res3d if res3d is not None else _fixtures_3d()
        claims = [{k: v for k, v in c.items() if not k.startswith("_")}
                  for c in F.derive_claims(res3e)]
        index = collect_evidence_index(res3d)
        return MockLLMClient(F._mock_response_for(claims, index))

    def test_mock_valid_output(self):
        out = F.run_verification_report(self._valid_client(),
                                        _fixtures_3e(), _fixtures_3d())
        self.assertEqual(len(out["verification"]), 3)
        self.assertTrue(out["report"]["findings"])

    def test_strict_format_forwarded(self):
        client = self._valid_client()
        F.run_verification_report(client, _fixtures_3e(), _fixtures_3d())
        fmt = client.calls[0]["response_format"]
        self.assertEqual(fmt["type"], "json_schema")
        self.assertTrue(fmt["json_schema"]["strict"])
        self.assertEqual(fmt["json_schema"]["name"], "phase3f_report")
        self.assertEqual(fmt["json_schema"]["schema"], F.REPORT_JSON_SCHEMA)

    def test_tokens_and_temperature(self):
        client = self._valid_client()
        F.run_verification_report(client, _fixtures_3e(), _fixtures_3d())
        self.assertEqual(client.calls[0]["max_tokens"], F.REPORT_MAX_TOKENS)
        self.assertEqual(F.REPORT_MAX_TOKENS, 6000)
        self.assertEqual(client.calls[0]["temperature"], 0.0)

    def test_schema_mirrors_constants(self):
        schema = F.REPORT_JSON_SCHEMA
        json.dumps(schema)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), {"schema_version", "verification", "report"})
        statuses = schema["properties"]["verification"]["items"]["properties"]["status"]
        self.assertEqual(statuses["enum"], list(F.STATUSES))

    def test_derivation_covers_3e(self):
        claims = F.derive_claims(_fixtures_3e())
        self.assertEqual([c["claim_id"] for c in claims],
                         ["claim_001", "claim_002", "claim_003"])
        self.assertEqual([c["kind"] for c in claims],
                         ["timeline_observation", "correlation", "inference"])

    def test_deterministic(self):
        args = (_fixtures_3e(), _fixtures_3d())
        first = F.run_verification_report(self._valid_client(), *args)
        rev3d = dict(args[1], merged_results=dict(
            args[1]["merged_results"],
            groups=list(reversed(args[1]["merged_results"]["groups"]))))
        second = F.run_verification_report(self._valid_client(*args), *args[:1], rev3d)
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))

    def test_empty_3e_safe(self):
        client = MockLLMClient("{}")
        out = F.run_verification_report(
            client, {"schema_version": "phase3e/v1", "timeline": [],
                     "correlations": [], "inferences": [], "limitations": []},
            _fixtures_3d())
        self.assertEqual((out["verification"], out["report"]["findings"]), ([], []))
        self.assertEqual(client.calls, [])

    def test_provider_error(self):
        with self.assertRaises(ProviderError):
            F.run_verification_report(
                MockLLMClient("{}", error=ProviderError("down")),
                _fixtures_3e(), _fixtures_3d())

    def test_no_leakage(self):
        sentinel = "sk-test-sentinel-3f"
        os.environ["MODEL_API_KEY"] = sentinel
        try:
            out = F.run_verification_report(self._valid_client(),
                                            _fixtures_3e(), _fixtures_3d())
            self.assertNotIn(sentinel, json.dumps(out))
        finally:
            os.environ.pop("MODEL_API_KEY", None)

    def test_bad_inputs_rejected(self):
        with self.assertRaises(F.ReportValidationError):
            F.run_verification_report(MockLLMClient("{}"), {"schema_version": "x"},
                                      _fixtures_3d())
        with self.assertRaises(F.ReportValidationError):
            F.run_verification_report(MockLLMClient("{}"), _fixtures_3e(),
                                      {"schema_version": "x"})

    def test_prompt_contract(self):
        for phrase in ("VERIFY each listed claim", "exactly these three top-level keys",
                       "suspect, perpetrator, victim",
                       "Return only the required JSON structure"):
            self.assertIn(phrase, F.SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
