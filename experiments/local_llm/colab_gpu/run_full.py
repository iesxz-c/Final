"""Optional end-to-end runner: 3C (local) -> frozen 3D -> 3E/3F (local).

Usage: python3 run_full.py --evidence EVIDENCE.JSON --incidents INCIDENTS.JSON
       [--server-url URL] [--inputs DIR] [--results DIR] [--cases I28]
       [--max-prompt-chars N]
Corpus files are NOT vendored (35.9 MB): upload evidence.json +
incidents.json (fused_155) and pass their paths. Without them the runner
records an honest skip for every case instead of failing or fabricating.
Fail-closed per stage; no plan repair; no external API. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))


def post(server_url: str, system: str, user: str, max_tokens: int,
         schema_fmt: dict, deadline: float) -> tuple:
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
        server_url + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=deadline) as resp:
        envelope = json.loads(resp.read().decode("utf-8"))
    return (envelope["choices"][0]["message"]["content"],
            round(time.perf_counter() - start, 3),
            envelope.get("usage") or {})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="optional end-to-end runner")
    parser.add_argument("--server-url", default="http://127.0.0.1:8080")
    parser.add_argument("--inputs", default="inputs")
    parser.add_argument("--results", default="results/full")
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--incidents", default=None)
    parser.add_argument("--cases", default="I28")
    parser.add_argument("--max-prompt-chars", type=int, default=100000)
    parser.add_argument("--deadline", type=float, default=1800.0)
    args = parser.parse_args(argv)
    if os.environ.get("MODEL_API_KEY"):
        print("refusing: MODEL_API_KEY present in environment")
        return 2
    from src.agents import query_planner as Q
    from src.agents import timeline_correlation as E
    from src.agents import verification_report as F
    from src.agents import evidence_retrieval as D3

    results = Path(args.results)
    results.mkdir(parents=True, exist_ok=True)
    log_fh = (results / "full.jsonl").open("a", encoding="utf-8")
    have_corpus = bool(args.evidence and args.incidents
                       and Path(args.evidence).exists()
                       and Path(args.incidents).exists())
    try:
        for qid in [q.strip() for q in args.cases.split(",") if q.strip()]:
            with (Path(args.inputs) / "questions_3c.json").open(
                    "r", encoding="utf-8") as fh:
                question = json.load(fh)[qid]["question"]
            d = results / qid
            d.mkdir(parents=True, exist_ok=True)
            if not have_corpus:
                log_fh.write(json.dumps(
                    {"query_id": qid, "ok": False, "phase": "skipped",
                     "reason": "corpus evidence.json/incidents.json not "
                               "provided (see README)"}) + "\n")
                print("%s SKIPPED: no corpus files" % qid)
                continue
            from src.pipeline.retrieve_evidence import load_evidence
            from src.pipeline.retrieve_temporal import load_incidents

            raw, c_s, c_u = post(
                args.server_url, Q.SYSTEM_PROMPT, question,
                Q.PLAN_MAX_TOKENS, Q.plan_response_format(), args.deadline)
            (d / "3c_raw.txt").write_text(raw, encoding="utf-8")
            try:
                plan = Q.parse_and_validate_plan(raw)
            except Exception as exc:  # noqa: BLE001 - recorded, next case
                log_fh.write(json.dumps(
                    {"query_id": qid, "ok": False, "phase": "3c",
                     "error": str(exc)[:500]}) + "\n")
                print("%s 3C INVALID: %s" % (qid, exc))
                continue
            t0 = time.perf_counter()
            result_3d = D3.execute_plan(
                plan, load_evidence(args.evidence),
                load_incidents(args.incidents))
            d3_s = round(time.perf_counter() - t0, 3)
            (d / "3d_result.json").write_text(
                json.dumps(result_3d, indent=2), encoding="utf-8")
            if result_3d.get("summary", {}).get("query_errors"):
                log_fh.write(json.dumps(
                    {"query_id": qid, "ok": False, "phase": "3d",
                     "error": "planner queries failed"}) + "\n")
                print("%s 3D QUERY ERRORS" % qid)
                continue
            user_message = ("Retrieved evidence (JSON):\n" + json.dumps(
                E.serialize_for_llm(result_3d), indent=2)
                + "\nInvestigator question (context only, not evidence): "
                + question.strip())
            if len(E.SYSTEM_PROMPT) + len(user_message) > args.max_prompt_chars:
                log_fh.write(json.dumps(
                    {"query_id": qid, "ok": False, "phase": "oversize-3e"})
                    + "\n")
                print("%s 3E OVERSIZE: recorded, stopping case" % qid)
                continue
            raw, e_s, e_u = post(
                args.server_url, E.SYSTEM_PROMPT, user_message,
                E.MAX_TOKENS, E.timeline_response_format(), args.deadline)
            (d / "3e_raw.txt").write_text(raw, encoding="utf-8")
            index = E.collect_evidence_index(result_3d)
            try:
                result_3e = E.parse_and_validate_timeline(raw, index)
            except Exception as exc:  # noqa: BLE001 - recorded, next case
                log_fh.write(json.dumps(
                    {"query_id": qid, "ok": False, "phase": "3e",
                     "error": str(exc)[:500]}) + "\n")
                print("%s 3E INVALID: %s" % (qid, exc))
                continue
            claims = [{k: v for k, v in c.items() if not k.startswith("_")}
                      for c in F.derive_claims(result_3e)]
            f_message = {
                "investigator_question": question.strip(),
                "claims_to_verify": claims,
                "prior_limitations": list(
                    result_3e.get("limitations", []) or []),
                "evidence": E.serialize_for_llm(result_3d)}
            f_text = json.dumps(f_message, indent=2)
            if len(F.SYSTEM_PROMPT) + len(f_text) > args.max_prompt_chars:
                log_fh.write(json.dumps(
                    {"query_id": qid, "ok": False, "phase": "oversize-3f"})
                    + "\n")
                print("%s 3F OVERSIZE: recorded, stopping case" % qid)
                continue
            raw, f_s, f_u = post(
                args.server_url, F.SYSTEM_PROMPT, f_text,
                F.REPORT_MAX_TOKENS, F.report_response_format(),
                args.deadline)
            (d / "3f_raw.txt").write_text(raw, encoding="utf-8")
            try:
                result_3f = F.parse_and_validate_report(
                    raw, index, [c["claim_id"] for c in claims])
            except Exception as exc:  # noqa: BLE001 - recorded, next case
                log_fh.write(json.dumps(
                    {"query_id": qid, "ok": False, "phase": "3f",
                     "error": str(exc)[:500]}) + "\n")
                print("%s 3F INVALID: %s" % (qid, exc))
                continue
            statuses = [v.get("status")
                        for v in result_3f.get("verification", [])]
            log_fh.write(json.dumps(
                {"query_id": qid, "ok": True, "3c_s": c_s, "3d_s": d3_s,
                 "3e_s": e_s, "3f_s": f_s,
                 "claims": len(statuses),
                 "supported": statuses.count("supported")}) + "\n")
            print("%s COMPLETE (%d claims)" % (qid, len(statuses)))
    finally:
        log_fh.close()
    print("FULL RUNNER DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
