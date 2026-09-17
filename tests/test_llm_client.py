"""Phase 3 llm_client tests: key handling, mock determinism, error mapping.

Meta Model API DIRECT only. No network access; no MODEL_API_KEY required."""

import io
import json
import os
import unittest
import urllib.error
from unittest import mock

from src.agents import llm_client as C


def _envelope(text):
    return {"output": [{"type": "message", "role": "assistant",
                        "content": [{"type": "output_text", "text": text}]}]}


class KeyHandlingTest(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("MODEL_API_KEY", None)
        # Isolate from any ambient repo-root .env for key-absence cases.
        self._env_patcher = mock.patch(
            "src.agents.llm_client.load_env_file", lambda path=None: {})
        self._env_patcher.start()

    def tearDown(self):
        self._env_patcher.stop()
        if self._saved is not None:
            os.environ["MODEL_API_KEY"] = self._saved
        else:
            os.environ.pop("MODEL_API_KEY", None)

    def test_missing_key_raises(self):
        with self.assertRaises(C.MissingAPIKeyError):
            C.MetaDirectClient(model="muse-spark-1.3-contributor")

    def test_blank_key_raises(self):
        with self.assertRaises(C.MissingAPIKeyError):
            C.MetaDirectClient(api_key="  ", model="muse-spark-1.3-contributor")

    def test_missing_model_raises(self):
        with self.assertRaises(C.LLMError):
            C.MetaDirectClient(api_key="sk-x", model="  ")

    def test_env_key_accepted_but_never_shown(self):
        os.environ["MODEL_API_KEY"] = "synthetic-env-secret"
        client = C.MetaDirectClient(model="muse-spark-1.3-contributor")
        self.assertNotIn("synthetic-env-secret", repr(client))
        self.assertNotIn("synthetic-env-secret", str(client.__dict__.keys()))


class MockClientTest(unittest.TestCase):
    def test_deterministic_replay(self):
        client = C.MockLLMClient(['{"a": 1}', '{"a": 2}'])
        self.assertEqual(client.generate_structured("s", "u"), '{"a": 1}')
        self.assertEqual(client.generate_structured("s", "u"), '{"a": 2}')
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(client.calls[0]["user_prompt"], "u")

    def test_error_option(self):
        client = C.MockLLMClient("{}", error=C.ProviderError("down"))
        with self.assertRaises(C.ProviderError):
            client.generate_structured("s", "u")


class MetaWireTest(unittest.TestCase):
    def setUp(self):
        self._env_patcher = mock.patch(
            "src.agents.llm_client.load_env_file", lambda path=None: {})
        self._env_patcher.start()

    def tearDown(self):
        self._env_patcher.stop()

    def _client(self, model="muse-spark-1.3-contributor"):
        return C.MetaDirectClient(api_key="synthetic-test-key", model=model)

    def _urlopen(self, payload):
        fake = mock.MagicMock()
        fake.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return mock.patch("urllib.request.urlopen", return_value=fake)

    def test_endpoint_is_meta_responses(self):
        self.assertEqual(C.META_RESPONSES_ENDPOINT,
                         "https://api.meta.ai/v1/responses")
        self.assertEqual(self._client().endpoint,
                         "https://api.meta.ai/v1/responses")

    def test_success_posts_bearer_and_model(self):
        client = self._client()
        with self._urlopen(_envelope('{"ok": true}')) as urlopen:
            out = client.generate_structured("sys", "usr", temperature=0.0)
        self.assertEqual(out, '{"ok": true}')
        request = urlopen.call_args[0][0]
        self.assertEqual(request.full_url, "https://api.meta.ai/v1/responses")
        self.assertIn("Bearer synthetic-test-key",
                      request.get_header("Authorization"))
        body = json.loads(request.data.decode())
        self.assertEqual(body["model"], "muse-spark-1.3-contributor")
        self.assertFalse(body["stream"])

    def test_request_uses_input_text_parts_not_messages(self):
        with self._urlopen(_envelope("{}")) as urlopen:
            self._client().generate_structured("sys", "usr")
        body = json.loads(urlopen.call_args[0][0].data.decode())
        self.assertNotIn("messages", body)
        self.assertNotIn("response_format", body)
        self.assertEqual(body["input"], [{"role": "user", "content": [
            {"type": "input_text", "text": "sys"},
            {"type": "input_text", "text": "usr"}]}])

    def test_schema_format_uses_text_format(self):
        fmt = {"type": "json_schema",
               "json_schema": {"name": "n", "strict": True, "schema": {"type": "object"}}}
        with self._urlopen(_envelope('{"ok": true}')) as urlopen:
            self._client().generate_structured("s", "u", temperature=0.0,
                                               response_format=fmt,
                                               max_tokens=2048)
        body = json.loads(urlopen.call_args[0][0].data.decode())
        self.assertEqual(body["text"], {"format": {"type": "json_schema",
                                                  "name": "n",
                                                  "schema": {"type": "object"}}})
        self.assertNotIn("response_format", body)
        self.assertNotIn("messages", body)
        self.assertNotIn("tools", body)
        self.assertNotIn("tool_choice", body)

    def test_default_format_is_json_object(self):
        with self._urlopen(_envelope("{}")) as urlopen:
            self._client().generate_structured("s", "u")
        body = json.loads(urlopen.call_args[0][0].data.decode())
        self.assertEqual(body["text"], {"format": {"type": "json_object"}})

    def test_unsupported_format_fails_closed(self):
        with self.assertRaises(C.LLMError):
            self._client().generate_structured("s", "u", response_format={
                "type": "nope", "json_schema": {"name": "n", "schema": {}}})

    def test_empty_content_raises(self):
        with self._urlopen(_envelope("  ")):
            with self.assertRaises(C.EmptyResponseError):
                self._client().generate_structured("s", "u")

    def test_missing_output_raises(self):
        with self._urlopen({"id": "resp_1", "status": "incomplete"}):
            with self.assertRaises(C.ProviderError):
                self._client().generate_structured("s", "u")

    def test_non_json_raises(self):
        fake = mock.MagicMock()
        fake.__enter__.return_value.read.return_value = b"not json"
        with mock.patch("urllib.request.urlopen", return_value=fake):
            with self.assertRaises(C.ProviderError):
                self._client().generate_structured("s", "u")

    def test_http_error_mapped_without_key(self):
        err = urllib.error.HTTPError("url", 429, "slow", {}, io.BytesIO(b"rate limited"))
        with mock.patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(C.ProviderError) as ctx:
                self._client().generate_structured("s", "u")
        self.assertIn("429", str(ctx.exception))
        self.assertNotIn("synthetic-test-key", str(ctx.exception))

    def test_network_error_mapped(self):
        with mock.patch("urllib.request.urlopen",
                        side_effect=urllib.error.URLError("dns")):
            with self.assertRaises(C.ProviderError):
                self._client().generate_structured("s", "u")

    def test_slow_drip_becomes_timeout_error(self):
        import time

        def _hang(request, timeout=None):
            time.sleep(5)
            raise AssertionError("worker should have been abandoned first")

        client = C.MetaDirectClient(api_key="synthetic-test-key",
                                    model="muse-spark-1.3-contributor",
                                    total_timeout=0.2)
        with mock.patch("urllib.request.urlopen", side_effect=_hang):
            with self.assertRaises(C.ProviderError) as ctx:
                client.generate_structured("s", "u")
        self.assertIn("timed out", str(ctx.exception))
        self.assertNotIn("synthetic-test-key", str(ctx.exception))

    def test_total_timeout_defaults_to_socket_timeout(self):
        client = self._client()
        self.assertEqual(client.total_timeout, client.timeout)


class ProviderSelectionTest(unittest.TestCase):
    def test_openrouter_explicitly_rejected(self):
        from src.agents.query_planner import create_client
        with self.assertRaises(C.LLMError):
            create_client({"provider": "openrouter", "model": "m",
                           "temperature": 0.0}, api_key="synthetic-test-key")

    def test_unknown_provider_rejected(self):
        from src.agents.query_planner import create_client
        with self.assertRaises(C.LLMError):
            create_client({"provider": "router", "model": "m",
                           "temperature": 0.0}, api_key="synthetic-test-key")

    def test_default_provider_is_meta(self):
        from src.agents.query_planner import load_llm_settings
        with mock.patch("src.agents.query_planner.load_env_file",
                        lambda path=None: {}), \
             mock.patch("src.settings.load_config", return_value={}), \
             mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CCTV_LLM_PROVIDER", None)
            os.environ.pop("CCTV_LLM_MODEL", None)
            settings = load_llm_settings()
        self.assertEqual(settings["provider"], "meta")
        self.assertEqual(settings["model"], "muse-spark-1.3-contributor")

    def test_other_model_rejected(self):
        from src.agents.query_planner import create_client
        with self.assertRaises(C.LLMError):
            create_client({"provider": "meta", "model": "muse-spark-1.1",
                           "temperature": 0.0}, api_key="synthetic-test-key")

    def test_meta_client_built_by_default(self):
        from src.agents.query_planner import create_client
        client = create_client({"provider": "meta",
                                "model": "muse-spark-1.3-contributor",
                                "temperature": 0.0},
                               api_key="synthetic-test-key")
        self.assertIsInstance(client, C.MetaDirectClient)
        self.assertEqual(client.model, "muse-spark-1.3-contributor")


class ResponseFormatTest(unittest.TestCase):
    def test_mock_records_format(self):
        client = C.MockLLMClient("{}")
        client.generate_structured("s", "u", response_format={"type": "json_object"},
                                   max_tokens=4096)
        self.assertEqual(client.calls[0]["response_format"], {"type": "json_object"})
        self.assertEqual(client.calls[0]["max_tokens"], 4096)


if __name__ == "__main__":
    unittest.main()
