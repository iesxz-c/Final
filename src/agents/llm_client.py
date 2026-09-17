"""Phase 3 - Minimal provider-independent LLM client (stdlib only).

The planner depends on this abstraction; Meta Model API HTTP stays isolated
here. No API key is ever logged, printed, or included in exceptions.

Sole provider: Meta Model API DIRECT (Responses API). There is no fallback
provider and no router. Structured output uses the documented Responses
parameter `text.format` (Meta docs: sending `response_format` to /v1/responses
returns HTTP 400). The caller-supplied `strict` flag is intentionally not
forwarded: Meta documents that omitting it still constrains decoding to the
schema while avoiding HTTP 400 on schemas outside the strict subset.
"""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request

from src.env_file import load_env_file

API_KEY_ENV = "MODEL_API_KEY"
META_RESPONSES_ENDPOINT = "https://api.meta.ai/v1/responses"
DEFAULT_MODEL = "muse-spark-1.3-contributor"
REQUEST_TIMEOUT_SECONDS = 60


class LLMError(RuntimeError):
    """Base class for LLM client failures."""


class MissingAPIKeyError(LLMError):
    """No API key was available for the provider."""


class ProviderError(LLMError):
    """The provider returned an error or an unusable response."""


class EmptyResponseError(ProviderError):
    """The provider returned no content."""


class LLMClient:
    """Interface: turn (system, user) prompts into raw model text."""

    def generate_structured(self, system_prompt: str, user_prompt: str,
                            temperature: float = 0.0,
                            response_format: dict | None = None,
                            max_tokens: int | None = None) -> str:
        raise NotImplementedError


def _text_format(response_format: dict | None) -> dict:
    """Translate a caller response_format into Responses `text.format`.

    Accepts the OpenAI-style shapes the agents already build:
    {"type": "json_schema", "json_schema": {"name", "schema", ...}} or
    {"type": "json_object"}. Anything else fails closed.
    """
    if response_format is None:
        return {"type": "json_object"}
    kind = response_format.get("type")
    if kind == "json_object":
        return {"type": "json_object"}
    if kind == "json_schema":
        spec = response_format.get("json_schema") or {}
        name, schema = spec.get("name"), spec.get("schema")
        if not name or not isinstance(schema, dict):
            raise LLMError("json_schema format needs a name and a schema object")
        return {"type": "json_schema", "name": str(name), "schema": schema}
    raise LLMError(f"unsupported response_format for Meta Responses: {kind!r}")


class MetaDirectClient(LLMClient):
    """Meta Model API DIRECT client over stdlib urllib (Responses API)."""

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 temperature: float = 0.0,
                 endpoint: str = META_RESPONSES_ENDPOINT,
                 timeout: int = REQUEST_TIMEOUT_SECONDS,
                 total_timeout: int | float | None = None):
        load_env_file()  # repo-root .env fills gaps only; real env always wins
        key = api_key if api_key is not None else os.environ.get(API_KEY_ENV, "")
        if not key or not str(key).strip():
            raise MissingAPIKeyError(
                f"Meta Model API key not set (expected {API_KEY_ENV})")
        if not model or not str(model).strip():
            raise LLMError("Meta model is not configured")
        self._api_key = str(key)
        self.model = str(model)
        self.temperature = float(temperature)
        self.endpoint = endpoint
        self.timeout = timeout
        # Overall bound for connect + slow-drip reads, which the socket
        # timeout alone cannot enforce. Defaults to the socket timeout.
        self.total_timeout = timeout if total_timeout is None else total_timeout
        #: Usage block from the most recent response envelope, if the
        #: provider supplied one ({input_tokens, output_tokens,
        #: total_tokens}); otherwise None. Read-only observability for
        #: evaluation harnesses; never affects requests.
        self.last_usage: dict | None = None

    def __repr__(self) -> str:  # pragma: no cover - never leaks the key
        return (f"MetaDirectClient(model={self.model!r}, "
                f"temperature={self.temperature!r}, endpoint={self.endpoint!r})")

    def _read_bounded(self, request: urllib.request.Request) -> str:
        """Read the full HTTP response within an overall deadline.

        The socket timeout alone cannot stop a server that dribbles data,
        so the whole urlopen+read runs on a daemon worker joined with
        total_timeout. Daemon ensures a stuck socket never blocks exit.
        """
        box: dict = {}

        def _target() -> None:
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    box["body"] = response.read().decode("utf-8")
            except BaseException as exc:  # noqa: BLE001 - remapped below
                box["error"] = exc

        worker = threading.Thread(target=_target, daemon=True)
        worker.start()
        worker.join(self.total_timeout)
        if worker.is_alive():
            raise ProviderError(
                f"Meta request timed out after {self.total_timeout}s")
        exc = box.get("error")
        if isinstance(exc, urllib.error.HTTPError):
            raise ProviderError(
                f"Meta HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:500]}"
            ) from exc
        if isinstance(exc, (urllib.error.URLError, OSError)):
            raise ProviderError(f"Meta request failed: {exc}") from exc
        if exc is not None:
            raise exc
        return box["body"]

    def generate_structured(self, system_prompt: str, user_prompt: str,
                            temperature: float | None = None,
                            response_format: dict | None = None,
                            max_tokens: int | None = None) -> str:
        # Only documented Responses fields are sent: model, input (user role
        # with input_text parts), stream, text.format. The system prompt
        # travels as the leading input_text part; temperature/max_tokens are
        # accepted for caller compatibility but not sent (undocumented here).
        _ = temperature, max_tokens
        self.last_usage = None  # reset so a failed call never replays stale usage
        payload = {
            "model": self.model,
            "input": [{"role": "user", "content": [
                {"type": "input_text", "text": str(system_prompt)},
                {"type": "input_text", "text": str(user_prompt)}]}],
            "stream": False,
            "text": {"format": _text_format(response_format)},
        }
        request = urllib.request.Request(
            self.endpoint, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self._api_key}"},
            method="POST")
        body = self._read_bounded(request)
        try:
            data = json.loads(body)
        except ValueError as exc:
            raise ProviderError("Meta returned non-JSON output") from exc
        if isinstance(data, dict) and data.get("error"):
            raise ProviderError(f"Meta error: {data['error']}")
        self.last_usage = _extract_usage(data)
        return self._extract_text(data)

    @staticmethod
    def _extract_text(data) -> str:
        """Pull assistant text from a Responses envelope.

        Documented shape: output[].type == "message" with content[] parts of
        type "output_text" carrying "text".
        """
        parts = []
        output = data.get("output") if isinstance(data, dict) else None
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict) or item.get("type") != "message":
                    continue
                content = item.get("content") or []
                for part in content:
                    if (isinstance(part, dict)
                            and part.get("type") == "output_text"
                            and isinstance(part.get("text"), str)):
                        parts.append(part["text"])
        text = "".join(parts)
        if not text.strip():
            status = data.get("status") if isinstance(data, dict) else None
            raise EmptyResponseError(
                f"Meta returned no output text (status: {status})")
        return text


def _extract_usage(data) -> dict | None:
    """Pull token usage from a Responses envelope, if present.

    Returns {input_tokens, output_tokens, total_tokens} with integer
    values, else None. Never estimated.
    """
    usage = data.get("usage") if isinstance(data, dict) else None
    if not isinstance(usage, dict):
        return None
    try:
        values = {k: int(usage[k]) for k in
                  ("input_tokens", "output_tokens", "total_tokens")}
    except (KeyError, TypeError, ValueError):
        return None
    return values


class MockLLMClient(LLMClient):
    """Deterministic test double: replays canned responses, no network."""

    def __init__(self, responses: str | list = '{"ok": true}',
                 error: Exception | None = None):
        self._responses = [responses] if isinstance(responses, str) else list(responses)
        if not self._responses:
            raise ValueError("MockLLMClient needs at least one response")
        self._error = error
        self.calls: list = []

    def generate_structured(self, system_prompt: str, user_prompt: str,
                            temperature: float = 0.0,
                            response_format: dict | None = None,
                            max_tokens: int | None = None) -> str:
        self.calls.append({"system_prompt": system_prompt,
                           "user_prompt": user_prompt, "temperature": temperature,
                           "response_format": response_format,
                           "max_tokens": max_tokens})
        if self._error is not None:
            raise self._error
        index = min(len(self.calls) - 1, len(self._responses) - 1)
        return self._responses[index]
