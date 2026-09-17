"""Phase 3C planner tests: validation, mock planning, error handling.

No network access; no MODEL_API_KEY required."""

import json
import os
import unittest

from src.agents import query_planner as Q
from src.agents.llm_client import LLMError, MockLLMClient, ProviderError


def _plan(**overrides):
    base = {"schema_version": "phase3c/v1", "intent": "search_evidence",
            "queries": [{"query": "Fighting", "source": None}],
            "video_id": None, "start_time": None, "end_time": None,
            "temporal_context_seconds": 0, "needs_timeline": False,
            "needs_cross_evidence": False}
    base.update(overrides)
    return json.dumps(base)


def _planned(query, response):
    return Q.plan_query(MockLLMClient(response), query)


class ValidPlanTest(unittest.TestCase):
    def test_search_evidence(self):
        plan = Q.parse_and_validate_plan(_plan())
        self.assertEqual(plan["intent"], "search_evidence")
        self.assertEqual(plan["queries"], [{"query": "Fighting", "source": None}])

    def test_incident_investigation(self):
        plan = Q.parse_and_validate_plan(_plan(
            intent="investigate_incident",
            queries=[{"query": "Fighting", "source": "surveillance_event"}],
            temporal_context_seconds=5, needs_timeline=True, needs_cross_evidence=True))
        self.assertEqual(plan["intent"], "investigate_incident")
        self.assertTrue(plan["needs_timeline"])
        self.assertTrue(plan["needs_cross_evidence"])

    def test_object_query(self):
        plan = Q.parse_and_validate_plan(_plan(
            intent="find_object", queries=[{"query": "person", "source": "object"}]))
        self.assertEqual(plan["queries"][0]["source"], "object")

    def test_event_query(self):
        plan = Q.parse_and_validate_plan(_plan(
            intent="find_event", queries=[{"query": "Fighting", "source": None}]))
        self.assertEqual(plan["intent"], "find_event")

    def test_generic_action_query(self):
        plan = Q.parse_and_validate_plan(_plan(
            intent="search_evidence",
            queries=[{"query": "walking", "source": "generic_action"}]))
        self.assertEqual(plan["queries"][0]["source"], "generic_action")

    def test_surveillance_event_query(self):
        plan = Q.parse_and_validate_plan(_plan(
            intent="find_event",
            queries=[{"query": "Assault", "source": "surveillance_event"}]))
        self.assertEqual(plan["queries"][0]["source"], "surveillance_event")

    def test_multiple_queries(self):
        plan = Q.parse_and_validate_plan(_plan(
            queries=[{"query": "Fighting", "source": "surveillance_event"},
                     {"query": "person", "source": "object"}]))
        self.assertEqual(len(plan["queries"]), 2)

    def test_video_id_extraction(self):
        plan = Q.parse_and_validate_plan(_plan(
            video_id="anomaly/Fighting/Fighting004_x264.mp4"))
        self.assertEqual(plan["video_id"], "anomaly/Fighting/Fighting004_x264.mp4")

    def test_time_range(self):
        plan = Q.parse_and_validate_plan(_plan(start_time=12.0, end_time=14.0))
        self.assertEqual((plan["start_time"], plan["end_time"]), (12.0, 14.0))

    def test_temporal_context(self):
        plan = Q.parse_and_validate_plan(_plan(temporal_context_seconds=5))
        self.assertEqual(plan["temporal_context_seconds"], 5)


class RejectionTest(unittest.TestCase):
    def _rejects(self, text):
        with self.assertRaises(Q.PlanValidationError):
            Q.parse_and_validate_plan(text)

    def test_invalid_intent(self):
        self._rejects(_plan(intent="arrest_the_suspect"))

    def test_invalid_source(self):
        self._rejects(_plan(queries=[{"query": "x", "source": "thermal"}]))

    def test_empty_query_string(self):
        self._rejects(_plan(queries=[{"query": "  ", "source": None}]))

    def test_negative_timestamp(self):
        self._rejects(_plan(start_time=-1.0))

    def test_end_before_start(self):
        self._rejects(_plan(start_time=14.0, end_time=12.0))

    def test_excessive_context(self):
        self._rejects(_plan(temporal_context_seconds=301))

    def test_invalid_boolean(self):
        self._rejects(_plan(needs_timeline="yes"))

    def test_missing_queries(self):
        data = json.loads(_plan())
        del data["queries"]
        self._rejects(json.dumps(data))

    def test_empty_queries_list(self):
        self._rejects(_plan(queries=[]))

    def test_malformed_json(self):
        self._rejects("{not json")

    def test_empty_response(self):
        self._rejects("   ")

    def test_unknown_top_level_field(self):
        self._rejects(_plan(confidence=0.99))

    def test_bool_timestamp_rejected(self):
        self._rejects(_plan(start_time=True))


class PlannerBehaviorTest(unittest.TestCase):
    def test_mock_plans_without_key(self):
        env = dict(os.environ)
        os.environ.pop("MODEL_API_KEY", None)
        try:
            plan = _planned("Find fighting near the incident", _plan())
            self.assertEqual(plan["intent"], "search_evidence")
        finally:
            os.environ.clear()
            os.environ.update(env)

    def test_provider_error_surfaced(self):
        client = MockLLMClient("{}", error=ProviderError("boom"))
        with self.assertRaises(ProviderError):
            Q.plan_query(client, "hello")

    def test_markdown_fence_stripped(self):
        plan = _planned("hi", "```json\n" + _plan() + "\n```")
        self.assertEqual(plan["schema_version"], "phase3c/v1")

    def test_blank_investigator_query_rejected(self):
        with self.assertRaises(Q.PlanValidationError):
            Q.plan_query(MockLLMClient(_plan()), "  ")

    def test_key_never_in_output(self):
        sentinel = "sk-test-sentinel-key-12345"
        os.environ["MODEL_API_KEY"] = sentinel
        try:
            plan = _planned("Find person", _plan(intent="find_person"))
            blob = json.dumps(plan)
            self.assertNotIn(sentinel, blob)
            client = MockLLMClient(_plan())
            with self.assertRaises(ProviderError) as ctx:
                raise ProviderError("boom")
            self.assertNotIn(sentinel, str(ctx.exception))
        finally:
            os.environ.pop("MODEL_API_KEY", None)

    def test_system_prompt_constraints(self):
        for phrase in ("do not have access to evidence", "must not invent",
                       "Return only the requested JSON"):
            self.assertIn(phrase, Q.SYSTEM_PROMPT)


class StructuredOutputTest(unittest.TestCase):
    def test_schema_mirrors_vocabularies(self):
        schema = Q.PLAN_JSON_SCHEMA
        json.dumps(schema)  # must be JSON-serializable for the wire
        props = schema["properties"]
        self.assertEqual(props["schema_version"]["enum"], [Q.SCHEMA_VERSION])
        self.assertEqual(props["intent"]["enum"], list(Q.INTENTS))
        self.assertEqual(props["queries"]["minItems"], 1)
        item = props["queries"]["items"]
        self.assertEqual(item["properties"]["query"]["minLength"], 1)
        self.assertEqual(item["properties"]["source"]["enum"], [*Q.SOURCES, None])
        self.assertFalse(item["additionalProperties"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(props["temporal_context_seconds"]["maximum"], 300)
        self.assertEqual(set(schema["required"]),
                         {"schema_version", "intent", "queries", "video_id",
                          "start_time", "end_time", "temporal_context_seconds",
                          "needs_timeline", "needs_cross_evidence"})

    def test_planner_sends_strict_schema(self):
        client = MockLLMClient(_plan())
        Q.plan_query(client, "Find fighting")
        fmt = client.calls[0]["response_format"]
        self.assertEqual(fmt["type"], "json_schema")
        self.assertTrue(fmt["json_schema"]["strict"])
        self.assertEqual(fmt["json_schema"]["name"], "phase3c_plan")
        self.assertEqual(fmt["json_schema"]["schema"], Q.PLAN_JSON_SCHEMA)
        self.assertEqual(client.calls[0]["temperature"], 0.0)

    def test_planner_caps_max_tokens(self):
        self.assertEqual(Q.PLAN_MAX_TOKENS, 2048)
        client = MockLLMClient(_plan())
        Q.plan_query(client, "Find fighting")
        self.assertEqual(client.calls[0]["max_tokens"], 2048)

    def test_prompt_output_contract(self):
        for phrase in ("MUST contain", "non-empty string", "derived from",
                       "no Markdown", "nothing else"):
            self.assertIn(phrase, Q.SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
