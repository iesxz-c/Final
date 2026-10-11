"""3C benchmark on local server: 10 frozen benchmark questions.

Usage: python3 run_3c_bench.py [--server-url URL] [--inputs DIR]
       [--results DIR] [--cases I01,I02,...]
Frozen SYSTEM_PROMPT + verbatim questions + frozen schema/validator.
No 3D/3E/3F. No external API (asserts no MODEL_API_KEY). Stdlib only.
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
    parser = argparse.ArgumentParser(description="3C local benchmark")
    parser.add_argument("--server-url", default="http://127.0.0.1:8080")
    parser.add_argument("--inputs", default="inputs")
    parser.add_argument("--results", default="results/bench_3c")
    parser.add_argument("--cases", default="I01,I02,I05,I10,I11,I19,I22,I23,I28,I30")
    parser.add_argument("--deadline", type=float, default=600.0)
    args = parser.parse_args(argv)
    if os.environ.get("MODEL_API_KEY"):
        print("refusing: MODEL_API_KEY present in environment")
        return 2
    from src.agents import query_planner as Q

    results = Path(args.results)
    results.mkdir(parents=True, exist_ok=True)
    log_path = results / "bench_3c.jsonl"
    fmt = Q.plan_response_format()
    with (Path(args.inputs) / "questions_3c.json").open(
            "r", encoding="utf-8") as fh:
        questions = json.load(fh)
    with LOG_APPEND(log_path) as log:
        for qid in [q.strip() for q in args.cases.split(",") if q.strip()]:
            case = questions[qid]
            d = results / qid
            d.mkdir(parents=True, exist_ok=True)
            try:
                raw, req_s, usage = post(
                    args.server_url, Q.SYSTEM_PROMPT, case["question"],
                    Q.PLAN_MAX_TOKENS, fmt, args.deadline)
            except Exception as exc:  # noqa: BLE001 - recorded, next case
                log({"query_id": qid, "ok": False, "phase": "request",
                     "error": str(exc)[:500]})
                print("%s REQUEST FAILED: %s" % (qid, exc))
                continue
            (d / "raw_output.txt").write_text(raw, encoding="utf-8")
            try:
                plan = Q.parse_and_validate_plan(raw)
                valid, verr = True, None
                (d / "validated_plan.json").write_text(
                    json.dumps(plan, indent=2), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001 - verdict, not a retry
                plan, valid, verr = None, False, str(exc)[:500]
            log({"query_id": qid, "ok": True, "valid": valid, "error": verr,
                 "request_s": req_s,
                 "n_prompt_tokens": (usage or {}).get("prompt_tokens"),
                 "n_predicted_tokens": (usage or {}).get("completion_tokens"),
                 "plan": plan})
            print("%s valid=%s req=%.1fs" % (qid, valid, req_s))
    print("3C BENCH COMPLETE")
    return 0


class LOG_APPEND:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        self.fh = self.path.open("a", encoding="utf-8")

        def _log(record: dict) -> None:
            self.fh.write(json.dumps(record) + "\n")

        return _log

    def __exit__(self, *exc):
        self.fh.close()
        return False


if __name__ == "__main__":
    sys.exit(main())
