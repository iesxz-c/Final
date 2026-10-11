"""Evidence-backed 3E runs on vendored frozen result_3d inputs.

Usage: python3 run_3e_evidence.py [--server-url URL] [--inputs DIR]
       [--results DIR] [--cases I28,I23,...] [--max-prompt-chars N]
Frozen 3E prompt construction + frozen schema/validator. No 3C/3D/3F.
Refuses inputs over --max-prompt-chars (default 100000, well under the
native 32768-token slot): oversized evidence is reported, never cut.
No external API (asserts no MODEL_API_KEY). Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


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
    parser = argparse.ArgumentParser(description="evidence-backed 3E runs")
    parser.add_argument("--server-url", default="http://127.0.0.1:8080")
    parser.add_argument("--inputs", default="inputs")
    parser.add_argument("--results", default="results/stage_3e")
    parser.add_argument("--cases",
                        default="I03,I19,I23,I24,I27,I28,I29,I30")
    parser.add_argument("--max-prompt-chars", type=int, default=100000)
    parser.add_argument("--deadline", type=float, default=1800.0)
    args = parser.parse_args(argv)
    if os.environ.get("MODEL_API_KEY"):
        print("refusing: MODEL_API_KEY present in environment")
        return 2
    from src.agents import timeline_correlation as E

    results = Path(args.results)
    results.mkdir(parents=True, exist_ok=True)
    log_path = results / "stage_3e.jsonl"
    log_fh = log_path.open("a", encoding="utf-8")
    fmt = E.timeline_response_format()
    try:
        for qid in [q.strip() for q in args.cases.split(",") if q.strip()]:
            with (Path(args.inputs) / ("%s.json" % qid)).open(
                    "r", encoding="utf-8") as fh:
                case = json.load(fh)
            d = results / qid
            d.mkdir(parents=True, exist_ok=True)
            user_message = ("Retrieved evidence (JSON):\n" + json.dumps(
                E.serialize_for_llm(case["result_3d"]), indent=2))
            if (case.get("question") or "").strip():
                user_message += (
                    "\nInvestigator question (context only, not evidence): "
                    + case["question"].strip())
            prompt_chars = len(E.SYSTEM_PROMPT) + len(user_message)
            if prompt_chars > args.max_prompt_chars:
                log_fh.write(json.dumps(
                    {"query_id": qid, "ok": False, "phase": "oversize",
                     "prompt_chars": prompt_chars,
                     "max_prompt_chars": args.max_prompt_chars}) + "\n")
                print("%s OVERSIZE (%d chars): recorded, not run"
                      % (qid, prompt_chars))
                continue
            try:
                raw, req_s, usage = post(
                    args.server_url, E.SYSTEM_PROMPT, user_message,
                    E.MAX_TOKENS, fmt, args.deadline)
            except Exception as exc:  # noqa: BLE001 - recorded, next case
                log_fh.write(json.dumps(
                    {"query_id": qid, "ok": False, "phase": "request",
                     "prompt_chars": prompt_chars,
                     "error": str(exc)[:500]}) + "\n")
                print("%s REQUEST FAILED: %s" % (qid, exc))
                continue
            (d / "raw_output.txt").write_text(raw, encoding="utf-8")
            index = E.collect_evidence_index(case["result_3d"])
            try:
                validated = E.parse_and_validate_timeline(raw, index)
                valid, verr = True, None
                (d / "validated_3e.json").write_text(
                    json.dumps(validated, indent=2), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001 - verdict, not a retry
                valid, verr = False, str(exc)[:500]
            log_fh.write(json.dumps(
                {"query_id": qid, "ok": True, "valid": valid, "error": verr,
                 "request_s": req_s, "prompt_chars": prompt_chars,
                 "n_prompt_tokens": (usage or {}).get("prompt_tokens"),
                 "n_predicted_tokens": (usage or {}).get("completion_tokens"),
                 "timeline_n": len((validated.get("timeline", [])
                                    if valid else [])),
                 "direct_ids": [r.get("evidence_id")
                                for g in (case["result_3d"].get(
                                    "merged_results", {}).get("groups", [])
                                          or []) for r in g.get(
                                              "matched_evidence", [])]})
                + "\n")
            print("%s valid=%s req=%.1fs prompt_chars=%d"
                  % (qid, valid, req_s, prompt_chars))
    finally:
        log_fh.close()
    print("3E EVIDENCE RUNS COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
