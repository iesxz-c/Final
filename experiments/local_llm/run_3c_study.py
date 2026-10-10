"""Isolated 3C field study (10 cases). Stdlib only.

For each case: frozen SYSTEM_PROMPT + verbatim benchmark question ->
localhost model -> raw plan saved verbatim -> frozen validator verdict ->
mechanical comparison vs benchmark scope, corpus video IDs, and the
locked reference plan (reference only, never a grade). No 3D/3E/3F.
No Meta client, no API key (asserted absent), no plan repair.
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
OUT_BASE = EXP_ROOT / "outputs" / "study_3c"
LOG_PATH = EXP_ROOT / "logs" / "study_3c.jsonl"
SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"
CLIENT_DEADLINE_S = 600.0
CASES = ["I01", "I02", "I05", "I10", "I11",
         "I19", "I22", "I23", "I28", "I30"]

sys.path.insert(0, str(PROJECT_ROOT))


def mem_snapshot() -> dict:
    import ctypes

    box = (ctypes.c_ulonglong * 8)()
    box[0] = ctypes.sizeof(box)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(box))
    return {"ram_total_gb": round(box[1] / 1e9, 2),
            "ram_free_gb": round(box[2] / 1e9, 2)}


def post(system: str, user: str, max_tokens: int, schema_fmt: dict) -> tuple:
    payload = {
        "model": "qwen2.5-3b-instruct-q4_k_m",
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "stream": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_fmt["json_schema"]["name"],
                            "strict": True,
                            "schema": schema_fmt["json_schema"]["schema"]},
        },
    }
    start = time.perf_counter()
    req = urllib.request.Request(
        SERVER_URL, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=CLIENT_DEADLINE_S) as resp:
        envelope = json.loads(resp.read().decode("utf-8"))
    return (envelope["choices"][0]["message"]["content"],
            round(time.perf_counter() - start, 3),
            envelope.get("usage") or {})


def log(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def main() -> int:
    if os.environ.get("MODEL_API_KEY"):
        print("refusing: MODEL_API_KEY present in environment")
        return 2
    from src.agents import query_planner as Q

    with (PROJECT_ROOT / "eval/investigation_benchmark_v1.json").open(
            "r", encoding="utf-8") as fh:
        cases = {c["query_id"]: c for c in json.load(fh)["cases"]}
    with (PROJECT_ROOT / "data/data_155n/fused_155/evidence.json").open(
            "r", encoding="utf-8") as fh:
        corpus_videos = {r.get("video_id") for r in json.load(fh)}
    locked = {}
    for qid in CASES:
        for arm in ("full-hybrid", "full-lexical"):
            path = (PROJECT_ROOT / "data/evaluations/paired_30case" / arm
                    / ("%s.%s.json" % (qid, arm)))
            if path.exists():
                with path.open("r", encoding="utf-8") as fh:
                    locked.setdefault(qid, json.load(fh).get("plan"))
                break
    fmt = Q.plan_response_format()
    for qid in CASES:
        case = cases[qid]
        out_dir = OUT_BASE / qid
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            raw, req_s, usage = post(
                Q.SYSTEM_PROMPT, case["question"], Q.PLAN_MAX_TOKENS, fmt)
        except Exception as exc:  # noqa: BLE001 - recorded, next case
            log({"query_id": qid, "ok": False, "phase": "request",
                 "error": str(exc)[:500], "mem": mem_snapshot()})
            print("%s REQUEST FAILED: %s" % (qid, exc))
            continue
        (out_dir / "raw_output.txt").write_text(raw, encoding="utf-8")
        try:
            plan = Q.parse_and_validate_plan(raw)
            valid, verr = True, None
            (out_dir / "validated_plan.json").write_text(
                json.dumps(plan, indent=2), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - verdict, not a retry
            plan, valid, verr = None, False, str(exc)[:500]
        scope = case.get("scope") or {}
        ref = locked.get(qid) or {}
        comparison = {"scope_video": scope.get("video_id"),
                      "scope_start": scope.get("start_time"),
                      "scope_end": scope.get("end_time")}
        if plan is not None:
            comparison.update({
                "plan_video": plan.get("video_id"),
                "video_exact_corpus_match":
                    plan.get("video_id") in corpus_videos
                    if plan.get("video_id") else None,
                "video_equals_scope":
                    plan.get("video_id") == scope.get("video_id"),
                "video_equals_locked_plan":
                    plan.get("video_id") == (ref.get("video_id")),
                "plan_start": plan.get("start_time"),
                "plan_end": plan.get("end_time"),
                "start_equals_scope":
                    plan.get("start_time") == scope.get("start_time"),
                "end_equals_scope":
                    plan.get("end_time") == scope.get("end_time"),
                "queries": plan.get("queries"),
                "temporal_context_seconds":
                    plan.get("temporal_context_seconds"),
                "locked_plan_queries": (ref.get("queries") if ref else None),
            })
        log({"query_id": qid, "ok": True, "valid": valid, "error": verr,
             "request_s": req_s,
             "n_prompt_tokens": usage.get("prompt_tokens"),
             "n_predicted_tokens": usage.get("completion_tokens"),
             "comparison": comparison, "mem": mem_snapshot()})
        print("%s valid=%s video_match=%s req=%.1fs" % (
            qid, valid, comparison.get("video_exact_corpus_match"), req_s))
    print("STUDY COMPLETE (3C only, 10 cases)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
