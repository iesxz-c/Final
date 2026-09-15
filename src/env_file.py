"""Safe `.env` loading for local secrets and overrides (stdlib only).

Rules:
- Reads `KEY=VALUE` lines from the repo-root `.env` (or an explicit path).
- Never overrides variables already present in the environment.
- Missing or unreadable files are silently ignored (returns {}).
- Callers must never log, print, or persist the returned values.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
MAX_ENV_FILE_BYTES = 65536

_KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def parse_env_text(text: str) -> dict:
    """Parse dotenv-style text into {KEY: value}. Invalid lines are ignored."""
    parsed: dict = {}
    for raw_line in str(text).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, _, value = line.partition("=")
        key = key.strip()
        if not _KEY_RE.match(key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            quote, inner = value[0], value[1:-1]
            if quote == '"':
                inner = (inner.replace("\\\\", "\\").replace('\\"', '"')
                         .replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r"))
            value = inner
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        parsed[key] = value
    return parsed


def load_env_file(path: str | os.PathLike | None = None) -> dict:
    """Load missing variables from a `.env` file into `os.environ`.

    Returns the variables actually set. Never touches existing entries.
    """
    target = Path(path) if path is not None else DEFAULT_ENV_PATH
    try:
        if target.stat().st_size > MAX_ENV_FILE_BYTES:
            return {}
        text = target.read_text(encoding="utf-8")
    except OSError:
        return {}
    loaded: dict = {}
    for key, value in parse_env_text(text).items():
        if key not in os.environ:
            os.environ[key] = value
            loaded[key] = value
    return loaded
