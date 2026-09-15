"""Phase 3C - Minimal provider-independent LLM client (stdlib only).

The planner depends on this abstraction; OpenRouter HTTP stays isolated
here. No API key is ever logged, printed, or included in exceptions.
"""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request

from src.env_file import load_env_file

API_KEY_ENV = "OPENROUTER_API_KEY"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
REQUEST_TIMEOUT_SECONDS = 60

#: Fallback structured-output request when the caller supplies no schema.
JSON_OBJECT_FORMAT = {"type": "json_object"}


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


class OpenRouterClient(LLMClient):
    """OpenRouter chat-completions client over stdlib urllib."""

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 temperature: float = 0.0,
                 endpoint: str = OPENROUTER_ENDPOINT,
                 timeout: int = REQUEST_TIMEOUT_SECONDS,
                 total_timeout: int | float | None = None):
        load_env_file()  # repo-root .env fills gaps only; real env always wins
        key = api_key if api_key is not None else os.environ.get(API_KEY_ENV, "")
        if not key or not str(key).strip():
            raise MissingAPIKeyError(
                f"OpenRouter API key not set (expected {API_KEY_ENV})")
        if not model or not str(model).strip():
            raise LLMError("OpenRouter model is not configured")
        self._api_key = str(key)
        self.model = str(model)
        self.temperature = float(temperature)
        self.endpoint = endpoint
        self.timeout = timeout
        # Overall bound for connect + slow-drip reads, which the socket
        # timeout alone cannot enforce. Defaults to the socket timeout.
        self.total_timeout = timeout if total_timeout is None else total_timeout

    def __repr__(self) -> str:  # pragma: no cover - never leaks the key
        return (f"OpenRouterClient(model={self.model!r}, "
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
                f"OpenRouter request timed out after {self.total_timeout}s")
        exc = box.get("error")
        if isinstance(exc, urllib.error.HTTPError):
            raise ProviderError(
                f"OpenRouter HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:500]}"
            ) from exc
        if isinstance(exc, (urllib.error.URLError, OSError)):
            raise ProviderError(f"OpenRouter request failed: {exc}") from exc
        if exc is not None:
            raise exc
        return box["body"]

    def generate_structured(self, system_prompt: str, user_prompt: str,
                            temperature: float | None = None,
                            response_format: dict | None = None,
                            max_tokens: int | None = None) -> str:
        payload = {
            "model": self.model,
            "temperature": self.temperature if temperature is None else float(temperature),
            "messages": [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": user_prompt}],
            "response_format": response_format or JSON_OBJECT_FORMAT,
        }
        if max_tokens is not None:
            payload["max_tokens"] = int(max_tokens)
        request = urllib.request.Request(
            self.endpoint, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self._api_key}"},
            method="POST")
        body = self._read_bounded(request)
        try:
            data = json.loads(body)
        except ValueError as exc:
            raise ProviderError("OpenRouter returned non-JSON output") from exc
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("OpenRouter response has no message content") from exc
        if content is None or not str(content).strip():
            raise EmptyResponseError("OpenRouter returned empty content")
        return str(content)


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
