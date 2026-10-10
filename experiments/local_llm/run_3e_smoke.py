"""Isolated 3E smoke test (Phase 2). Stdlib only. No Meta client, no API key.

Reads the frozen I01-hybrid bundle, builds the exact frozen 3E prompt,
POSTs to a localhost llama.cpp server, saves raw output verbatim, and
validates with the frozen 3E validator. Refuses to run if MODEL_API_KEY
is present in the environment.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

EXP_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = EXP_ROOT.parent.parent
BUNDLE = (PROJECT_ROOT / "data/evaluations/paired_30case/full-hybrid"
          / "I01.full-hybrid.json")
OUT_DIR = EXP_ROOT / "outputs" / "smoke_i01_3e"
LOG_PATH = EXP_ROOT / "logs" / "smoke_i01_3e.jsonl"
SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"
CLIENT_DEADLINE_S = 2700.0

sys.path.insert(0, str(PROJECT_ROOT))


def mem_snapshot() -> dict:
    import ctypes

    box = (ctypes.c_ulonglong * 8)()
    box[0] = ctypes.sizeof(box)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(box))
    snap = {"ram_total_gb": round(box[1] / 1e9, 2),
            "ram_free_gb": round(box[2] / 1e9, 2)}
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq llama-server.exe",
             "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=30).stdout
        snap["server_tasklist"] = out.strip()[:400]
    except Exception as exc:  # noqa: BLE001 - observability only
        snap["server_tasklist_error"] = str(exc)[:200]
    return snap


def main() -> int:
    if os.environ.get("MODEL_API_KEY"):
        print("refusing: MODEL_API_KEY present in environment")
        return 2
    from src.agents import timeline_correlation as E

    t0 = time.perf_counter()
    with BUNDLE.open("r", encoding="utf-8") as fh:
        bundle = json.load(fh)
    result_3d = bundle["result_3d"]
    question = bundle["question"]
    user_message = ("Retrieved evidence (JSON):\n"
                    + json.dumps(E.serialize_for_llm(result_3d), indent=2))
    if question and question.strip():
        user_message += ("\nInvestigator question (context only, not evidence): "
                         + question.strip())
    fmt = E.timeline_response_format()
    payload = {
        "model": "qwen2.5-3b-instruct-q4_k_m",
        "messages": [{"role": "system", "content": E.SYSTEM_PROMPT},
                     {"role": "user", "content": user_message}],
        "temperature": 0.0,
        "max_tokens": E.MAX_TOKENS,
        "stream": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": fmt["json_schema"]["name"],
                            "strict": True,
                            "schema": fmt["json_schema"]["schema"]},
        },
    }
    prompt_chars = len(E.SYSTEM_PROMPT) + len(user_message)
    mem_before = mem_snapshot()
    build_s = round(time.perf_counter() - t0, 3)
    req = urllib.request.Request(
        SERVER_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    post_start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=CLIENT_DEADLINE_S) as resp:
            envelope = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - recorded, never retried
        record = {"event": "request_failed", "error": str(exc)[:500],
                  "prompt_chars": prompt_chars, "build_s": build_s,
                  "mem_before": mem_before}
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        print("request failed: %s" % exc)
        return 3
    post_s = round(time.perf_counter() - post_start, 3)
    try:
        raw = envelope["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        record = {"event": "bad_envelope", "error": str(exc)[:300],
                  "envelope_keys": sorted(envelope.keys())
                  if isinstance(envelope, dict) else None}
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        print("bad envelope from server")
        return 3
    with (OUT_DIR / "raw_output.txt").open("w", encoding="utf-8") as fh:
        fh.write(raw if isinstance(raw, str) else json.dumps(raw))
    usage = envelope.get("usage") or {}
    timings = envelope.get("timings") or {}
    index = E.collect_evidence_index(result_3d)
    val_start = time.perf_counter()
    try:
        validated = E.parse_and_validate_timeline(raw, index)
        verdict = {"valid": True, "error": None,
                   "timeline_n": len(validated.get("timeline", [])),
                   "correlations_n": len(validated.get("correlations", [])),
                   "inferences_n": len(validated.get("inferences", []))}
    except Exception as exc:  # noqa: BLE001 - validator verdict, not a retry
        verdict = {"valid": False, "error": str(exc)[:500]}
    record = {
        "event": "smoke_3e_complete",
        "model": "Qwen/Qwen2.5-3B-Instruct-GGUF qwen2.5-3b-instruct-q4_k_m.gguf",
        "prompt_chars": prompt_chars,
        "system_chars": len(E.SYSTEM_PROMPT),
        "server_n_prompt_tokens": usage.get("prompt_tokens"),
        "server_n_predicted_tokens": usage.get("completion_tokens"),
        "server_timings": timings,
        "build_s": build_s,
        "request_s": post_s,
        "validate_s": round(time.perf_counter() - val_start, 3),
        "raw_chars": len(raw) if isinstance(raw, str) else None,
        "validator": verdict,
        "mem_before": mem_before,
        "mem_after": mem_snapshot(),
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")
    print(json.dumps({k: record[k] for k in (
        "server_n_prompt_tokens", "server_n_predicted_tokens", "request_s",
        "raw_chars")}, indent=2))
    print("validator valid: %s" % verdict["valid"])
    if verdict["error"]:
        print("validator error: %s" % verdict["error"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
