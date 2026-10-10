"""Isolated full-pipeline smoke test (I28 only). Stdlib only.

3C (local) -> frozen deterministic 3D -> 3E (local) -> 3F (local), using
frozen prompts, serializers, schemas, and validators. No Meta client, no
API key (asserted absent), localhost server only. Fail-closed: any stage
failure stops the run and is recorded honestly.
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
OUT_DIR = EXP_ROOT / "outputs" / "smoke_i28_full"
LOG_PATH = EXP_ROOT / "logs" / "smoke_i28_full.jsonl"
SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"
CLIENT_DEADLINE_S = 1800.0
QUERY_ID = "I28"

sys.path.insert(0, str(PROJECT_ROOT))


def mem_snapshot() -> dict:
    import ctypes

    box = (ctypes.c_ulonglong * 8)()
    box[0] = ctypes.sizeof(box)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(box))
    return {"ram_total_gb": round(box[1] / 1e9, 2),
            "ram_free_gb": round(box[2] / 1e9, 2)}


def post(messages: list, max_tokens: int, schema_fmt: dict) -> tuple:
    payload = {
        "model": "qwen2.5-3b-instruct-q4_k_m",
        "messages": messages,
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
    latency = round(time.perf_counter() - start, 3)
    raw = envelope["choices"][0]["message"]["content"]
    usage = envelope.get("usage") or {}
    return raw, {"request_s": latency,
                 "n_prompt_tokens": usage.get("prompt_tokens"),
                 "n_predicted_tokens": usage.get("completion_tokens"),
                 "server_timings": envelope.get("timings") or {}}


def log(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def main() -> int:
    if os.environ.get("MODEL_API_KEY"):
        print("refusing: MODEL_API_KEY present in environment")
        return 2
    from src.agents import query_planner as Q
    from src.agents import timeline_correlation as E
    from src.agents import verification_report as F
    from src.agents import evidence_retrieval as D3
    from src.pipeline.retrieve_evidence import load_evidence
    from src.pipeline.retrieve_temporal import load_incidents

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mem0 = mem_snapshot()
    with (PROJECT_ROOT / "eval/investigation_benchmark_v1.json").open(
            "r", encoding="utf-8") as fh:
        cases = {c["query_id"]: c for c in json.load(fh)["cases"]}
    question = cases[QUERY_ID]["question"]

    # ---- 3C (local) ----
    raw, info = post(
        [{"role": "system", "content": Q.SYSTEM_PROMPT},
         {"role": "user", "content": question}],
        Q.PLAN_MAX_TOKENS, Q.plan_response_format())
    (OUT_DIR / "3c_raw.txt").write_text(raw, encoding="utf-8")
    try:
        plan = Q.parse_and_validate_plan(raw)
        v3c = {"valid": True, "error": None}
    except Exception as exc:  # noqa: BLE001 - recorded, stop
        log({"stage": "3c", "ok": False, "error": str(exc)[:500],
             "info": info, "mem": mem_snapshot()})
        print("3C validation failed: %s" % exc)
        return 3
    (OUT_DIR / "3c_plan.json").write_text(
        json.dumps(plan, indent=2), encoding="utf-8")
    log({"stage": "3c", "ok": True, "info": info, "plan": plan})

    # ---- 3D (frozen deterministic) ----
    t0 = time.perf_counter()
    try:
        records = load_evidence(
            PROJECT_ROOT / "data/data_155n/fused_155/evidence.json")
        incidents = load_incidents(
            PROJECT_ROOT / "data/data_155n/fused_155/incidents.json")
        result_3d = D3.execute_plan(plan, records, incidents)
        d3_s = round(time.perf_counter() - t0, 3)
    except Exception as exc:  # noqa: BLE001 - recorded, stop
        log({"stage": "3d", "ok": False, "error": str(exc)[:500]})
        print("3D failed: %s" % exc)
        return 3
    (OUT_DIR / "3d_result.json").write_text(
        json.dumps(result_3d, indent=2), encoding="utf-8")
    groups = (result_3d.get("merged_results") or {}).get("groups", [])
    n_ev = sum(len(g.get("matched_evidence", []))
               + len(g.get("contextual_evidence", [])) for g in groups)
    log({"stage": "3d", "ok": True, "seconds": d3_s,
         "incident_groups": len(groups), "evidence_records": n_ev})
    if result_3d.get("summary", {}).get("query_errors"):
        log({"stage": "3d", "ok": False, "error": "planner queries failed"})
        print("3D query errors; stopping")
        return 3

    # ---- 3E (local) ----
    user_message = ("Retrieved evidence (JSON):\n"
                    + json.dumps(E.serialize_for_llm(result_3d), indent=2))
    if question.strip():
        user_message += ("\nInvestigator question (context only, not evidence): "
                         + question.strip())
    raw, info = post(
        [{"role": "system", "content": E.SYSTEM_PROMPT},
         {"role": "user", "content": user_message}],
        E.MAX_TOKENS, E.timeline_response_format())
    (OUT_DIR / "3e_raw.txt").write_text(raw, encoding="utf-8")
    index = E.collect_evidence_index(result_3d)
    try:
        result_3e = E.parse_and_validate_timeline(raw, index)
        v3e = {"valid": True, "error": None}
    except Exception as exc:  # noqa: BLE001 - recorded, stop
        log({"stage": "3e", "ok": False, "error": str(exc)[:500],
             "info": info, "mem": mem_snapshot()})
        print("3E validation failed: %s" % exc)
        return 3
    (OUT_DIR / "3e_result.json").write_text(
        json.dumps(result_3e, indent=2), encoding="utf-8")
    log({"stage": "3e", "ok": True, "info": info,
         "timeline_n": len(result_3e.get("timeline", [])),
         "correlations_n": len(result_3e.get("correlations", [])),
         "inferences_n": len(result_3e.get("inferences", []))})

    # ---- 3F (local) ----
    claims = [{k: v for k, v in c.items() if not k.startswith("_")}
              for c in F.derive_claims(result_3e)]
    f_message = {
        "investigator_question": question.strip(),
        "claims_to_verify": claims,
        "prior_limitations": list(result_3e.get("limitations", []) or []),
        "evidence": E.serialize_for_llm(result_3d),
    }
    raw, info = post(
        [{"role": "system", "content": F.SYSTEM_PROMPT},
         {"role": "user", "content": json.dumps(f_message, indent=2)}],
        F.REPORT_MAX_TOKENS, F.report_response_format())
    (OUT_DIR / "3f_raw.txt").write_text(raw, encoding="utf-8")
    try:
        result_3f = F.parse_and_validate_report(
            raw, index, [c["claim_id"] for c in claims])
        v3f = {"valid": True, "error": None}
    except Exception as exc:  # noqa: BLE001 - recorded, stop
        log({"stage": "3f", "ok": False, "error": str(exc)[:500],
             "info": info, "mem": mem_snapshot()})
        print("3F validation failed: %s" % exc)
        return 3
    (OUT_DIR / "3f_result.json").write_text(
        json.dumps(result_3f, indent=2), encoding="utf-8")
    statuses = [v.get("status") for v in result_3f.get("verification", [])]
    log({"stage": "3f", "ok": True, "info": info,
         "claims": len(statuses),
         "supported": statuses.count("supported"),
         "partial": statuses.count("partially_supported"),
         "unsupported": statuses.count("unsupported"),
         "mem": mem_snapshot(), "mem_start": mem0})
    print("FULL SMOKE COMPLETE: 3c ok, 3d ok (%d records), 3e ok, 3f ok "
          "(%d claims: %d supported)" % (
              n_ev, len(statuses), statuses.count("supported")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
