"""Phase 3C llm_client tests: key handling, mock determinism, error mapping.

No network access; no OPENROUTER_API_KEY required."""

import io
import json
import os
import unittest
import urllib.error
from unittest import mock

from src.agents import llm_client as C


def _response(content):
    return {"choices": [{"message": {"content": content}}]}


class KeyHandlingTest(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("OPENROUTER_API_KEY", None)
        # Isolate from any ambient repo-root .env for key-absence cases.
        self._env_patcher = mock.patch(
            "src.agents.llm_client.load_env_file", lambda path=None: {})
        self._env_patcher.start()

    def tearDown(self):
        self._env_patcher.stop()
        if self._saved is not None:
            os.environ["OPENROUTER_API_KEY"] = self._saved
        else:
            os.environ.pop("OPENROUTER_API_KEY", None)

    def test_missing_key_raises(self):
        with self.assertRaises(C.MissingAPIKeyError):
            C.OpenRouterClient(model="m")

    def test_blank_key_raises(self):
        with self.assertRaises(C.MissingAPIKeyError):
            C.OpenRouterClient(api_key="  ", model="m")

    def test_missing_model_raises(self):
        with self.assertRaises(C.LLMError):
            C.OpenRouterClient(api_key="sk-x", model="  ")

    def test_env_key_accepted_but_never_shown(self):
        os.environ["OPENROUTER_API_KEY"] = "sk-env-secret"
        client = C.OpenRouterClient(model="m")
        self.assertNotIn("sk-env-secret", repr(client))
        self.assertNotIn("sk-env-secret", str(client.__dict__.keys()))


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


class OpenRouterWireTest(unittest.TestCase):
    def _client(self):
        return C.OpenRouterClient(api_key="sk-test-key", model="test/model")

    def _urlopen(self, payload):
        fake = mock.MagicMock()
        fake.__enter__.return_value.read.return_value = json.dumps(payload).encode()
        return mock.patch("urllib.request.urlopen", return_value=fake)

    def test_success_posts_bearer_and_model(self):
        client = self._client()
        with self._urlopen(_response('{"ok": true}')) as urlopen:
            out = client.generate_structured("sys", "usr", temperature=0.0)
        self.assertEqual(out, '{"ok": true}')
        request = urlopen.call_args[0][0]
        self.assertIn("Bearer sk-test-key", request.get_header("Authorization"))
        body = json.loads(request.data.decode())
        self.assertEqual(body["model"], "test/model")
        self.assertEqual(body["temperature"], 0.0)

    def test_empty_content_raises(self):
        with self._urlopen(_response("  ")):
            with self.assertRaises(C.EmptyResponseError):
                self._client().generate_structured("s", "u")

    def test_http_error_mapped_without_key(self):
        err = urllib.error.HTTPError("url", 429, "slow", {}, io.BytesIO(b"rate limited"))
        with mock.patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(C.ProviderError) as ctx:
                self._client().generate_structured("s", "u")
        self.assertIn("429", str(ctx.exception))
        self.assertNotIn("sk-test-key", str(ctx.exception))

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

        client = C.OpenRouterClient(api_key="sk-test-key", model="m", total_timeout=0.2)
        with mock.patch("urllib.request.urlopen", side_effect=_hang):
            with self.assertRaises(C.ProviderError) as ctx:
                client.generate_structured("s", "u")
        self.assertIn("timed out", str(ctx.exception))
        self.assertNotIn("sk-test-key", str(ctx.exception))

    def test_total_timeout_defaults_to_socket_timeout(self):
        client = C.OpenRouterClient(api_key="sk-test-key", model="m")
        self.assertEqual(client.total_timeout, client.timeout)


class ResponseFormatTest(unittest.TestCase):
    def _body(self, **kwargs):
        client = C.OpenRouterClient(api_key="sk-test-key", model="test/model")
        with mock.patch("urllib.request.urlopen") as urlopen:
            fake = mock.MagicMock()
            fake.__enter__.return_value.read.return_value = json.dumps(
                {"choices": [{"message": {"content": "{}"}}]}).encode()
            urlopen.return_value = fake
            client.generate_structured("s", "u", **kwargs)
        return json.loads(urlopen.call_args[0][0].data.decode())

    def test_default_format_is_json_object(self):
        body = self._body()
        self.assertEqual(body["response_format"], {"type": "json_object"})
        self.assertEqual(body["temperature"], 0.0)

    def test_custom_schema_format_passed_through(self):
        fmt = {"type": "json_schema",
               "json_schema": {"name": "n", "strict": True, "schema": {"type": "object"}}}
        body = self._body(response_format=fmt)
        self.assertEqual(body["response_format"], fmt)

    def test_max_tokens_forwarded_when_set(self):
        body = self._body(max_tokens=2048)
        self.assertEqual(body["max_tokens"], 2048)

    def test_max_tokens_omitted_by_default(self):
        body = self._body()
        self.assertNotIn("max_tokens", body)

    def test_max_tokens_passed_through(self):
        body = self._body(max_tokens=4096)
        self.assertEqual(body["max_tokens"], 4096)

    def test_mock_records_format(self):
        client = C.MockLLMClient("{}")
        client.generate_structured("s", "u", response_format={"type": "json_object"},
                                   max_tokens=4096)
        self.assertEqual(client.calls[0]["response_format"], {"type": "json_object"})
        self.assertEqual(client.calls[0]["max_tokens"], 4096)


if __name__ == "__main__":
    unittest.main()
