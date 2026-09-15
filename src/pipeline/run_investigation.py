"""Phase 4 - End-to-end investigator workflow orchestration (no new reasoning).

Runs the complete pipeline in-process:

    question -> 3C plan -> 3D retrieval -> 3E timeline -> 3F report

Each stage is timed with time.perf_counter(). Failures are caught per
stage, recorded with a structured taxonomy, and stop downstream stages
without fabrication. An independent integrity audit re-derives evidence
ID sets and timestamp containment instead of trusting validators alone.

3D outputs are never truncated: grounding is preserved over brevity.

Mock mode exercises the real validators with deterministic mock LLM
responses built from the actual stage inputs (offline testing only).

Usage:
    python -m src.pipeline.run_investigation --question "..." --mock
    python -m src.pipeline.run_investigation --questions-file eval/queries.json --mock
"""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.agents import evidence_retrieval as D3
from src.agents import query_planner as Q
from src.agents import timeline_correlation as E
from src.agents import verification_report as F
from src.agents.llm_client import MockLLMClient
from src.pipeline.retrieve_evidence import load_evidence
from src.pipeline.retrieve_temporal import load_incidents

SCHEMA_VERSION = "phase4/v1"
DEFAULT_EVIDENCE = "data/evidence/fused/evidence.json"
DEFAULT_INCIDENTS = "data/evidence/fused/incidents.json"
DEFAULT_OUTPUT_DIR = "data/evaluations"


def classify_failure(exc: BaseException) -> str:
    """Map an exception to the structured failure taxonomy."""
    from src.agents.llm_client import LLMError, MissingAPIKeyError, ProviderError

    message = str(exc).lower()
    if isinstance(exc, MissingAPIKeyError):
        return "provider"
    if isinstance(exc, (ProviderError, LLMError)):
        return "timeout" if "timed out" in message else "provider"
    name = type(exc).__name__
    if "empty model response" in message or "not valid json" in message:
        return "parse"
    if name in ("PlanValidationError", "TimelineValidationError",
                "ReportValidationError") or isinstance(exc, ValueError):
        return "validation"
    return "other"


def get_git_hash() -> str:
    try:
        proc = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10,
                              cwd=PROJECT_ROOT)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return proc.stdout.strip() or "unknown"


def audit_integrity(records_snapshot: list, records_now: list,
                    result_3d: dict | None, result_3e: dict | None,
                    result_3f: dict | None) -> dict:
    """Independently re-derive ID sets, containment, and input invariance."""
    base_ids = {r.get("evidence_id") for r in records_snapshot}
    base_by_id = {r.get("evidence_id"): r for r in records_snapshot}
    audit: dict = {
        "input_unchanged": records_now == records_snapshot,
        "base_records": len(base_ids),
        "stages": {},
        "cross_video_violations": 0,
        "overall_pass": True,
    }

    def _check_lists(lists):
        """Unknown over the union; duplicates only WITHIN each list.

        The same evidence_id may legitimately appear in a timeline item,
        a correlation, and an inference at once; only a repeat inside one
        evidence_ids list is a duplicate.
        """
        flat = [e for ids in lists for e in ids]
        unknown = [e for e in flat if e not in base_ids]
        dupes = any(len(ids) != len(set(ids)) for ids in lists)
        preserved = True
        for e in set(flat) & base_ids:
            mine = next((r for r in records_now if r.get("evidence_id") == e), None)
            if mine is None or mine.get("source_references") != base_by_id[e].get(
                    "source_references"):
                preserved = False
        return unknown, dupes, preserved

    def _containment(items):
        bad = 0
        for start, end, ids in items:
            try:
                lo = min(float(base_by_id[e]["start_time"]) for e in ids if e in base_by_id)
                hi = max(float(base_by_id[e]["end_time"]) for e in ids if e in base_by_id)
            except ValueError:
                bad += 1
                continue
            if not (float(start) >= lo and float(end) <= hi):
                bad += 1
        return bad

    if result_3d is not None:
        per_list = []
        for group in result_3d.get("merged_results", {}).get("groups", []) or []:
            per_list.append([r.get("evidence_id")
                             for r in group.get("matched_evidence", []) or []])
            per_list.append([r.get("evidence_id")
                             for r in group.get("contextual_evidence", []) or []])
        per_list.append([h.get("evidence_id") for h in
                         result_3d.get("merged_results", {}).get("unmapped_hits", []) or []])
        ids = {e for ids in per_list for e in ids}
        unknown, dupes, preserved = _check_lists(per_list)
        audit["stages"]["3d"] = {"evidence_ids": len(ids), "unknown_ids": len(unknown),
                                 "duplicates": dupes, "refs_preserved": preserved,
                                 "pass": not unknown and not dupes and preserved}
    if result_3e is not None:
        timed, singles = [], []
        for item in result_3e.get("timeline", []) or []:
            timed.append((item["start_time"], item["end_time"], item["evidence_ids"]))
            singles.append(item["evidence_ids"])
        for corr in result_3e.get("correlations", []) or []:
            singles.append(corr["evidence_ids"])
        for inf in result_3e.get("inferences", []) or []:
            singles.append(inf["evidence_ids"])
        unknown, dupes_any, preserved = _check_lists(singles)
        cross = sum(1 for ids in singles
                    if len({base_by_id[e]["video_id"] for e in ids if e in base_by_id}) > 1)
        audit["cross_video_violations"] += cross
        bad_ts = _containment(timed)
        audit["stages"]["3e"] = {"evidence_ids": len({e for ids in singles for e in ids}),
                                 "unknown_ids": len(unknown),
                                 "duplicates": dupes_any, "refs_preserved": preserved,
                                 "cross_video": cross, "uncontained_ranges": bad_ts,
                                 "pass": not unknown and not dupes_any and preserved
                                 and cross == 0 and bad_ts == 0}
    if result_3f is not None:
        timed, singles = [], []
        for v in result_3f.get("verification", []) or []:
            singles.append(v["evidence_ids"])
        for t in result_3f.get("report", {}).get("timeline", []) or []:
            timed.append((t["start_time"], t["end_time"], t["evidence_ids"]))
            singles.append(t["evidence_ids"])
        for f in result_3f.get("report", {}).get("findings", []) or []:
            singles.append(f["evidence_ids"])
        unknown, dupes_any, preserved = _check_lists(singles)
        cross = sum(1 for ids in singles
                    if len({base_by_id[e]["video_id"] for e in ids if e in base_by_id}) > 1)
        audit["cross_video_violations"] += cross
        bad_ts = _containment(timed)
        audit["stages"]["3f"] = {"evidence_ids": len({e for ids in singles for e in ids}),
                                 "unknown_ids": len(unknown),
                                 "duplicates": dupes_any, "refs_preserved": preserved,
                                 "cross_video": cross, "uncontained_ranges": bad_ts,
                                 "pass": not unknown and not dupes_any and preserved
                                 and cross == 0 and bad_ts == 0}
    if audit["stages"]:
        audit["overall_pass"] = bool(audit["input_unchanged"]) and all(
            s["pass"] for s in audit["stages"].values())
    else:
        audit["overall_pass"] = bool(audit["input_unchanged"])
    return audit


def _mock_plan(question: str) -> dict:
    return Q.parse_and_validate_plan(Q._mock_response(question))


def _mock_timeline(result_3d: dict, question: str) -> dict:
    return E.run_timeline(MockLLMClient(E._mock_response_for(result_3d)),
                          result_3d, question)


def _mock_report(result_3e: dict, result_3d: dict, question: str) -> dict:
    claims = [{k: v for k, v in c.items() if not k.startswith("_")}
              for c in F.derive_claims(result_3e)]
    index = E.collect_evidence_index(result_3d)
    if not claims or not index:
        return F.run_verification_report(MockLLMClient("{}"), result_3e, result_3d,
                                         question)
    raw = F._mock_response_for(claims, index)
    return F.parse_and_validate_report(raw, index, [c["claim_id"] for c in claims])


def max_token_exposure(max_tokens_3f: int) -> dict:
    """Configured per-stage output caps (3C/3E fixed, 3F selectable)."""
    return {"3c": Q.PLAN_MAX_TOKENS, "3e": E.MAX_TOKENS, "3f": max_tokens_3f}


def run_question(question, records, incidents, mode, client, settings,
                 max_tokens_3f, model_name, input_evidence_path=None,
                 input_incidents_path=None):
    """Run one question through 3C->3D->3E->3F. Returns the phase4/v1 bundle."""
    snapshot = copy.deepcopy(records)
    bundle: dict = {
        "schema_version": SCHEMA_VERSION,
        "question": question,
        "plan": None, "result_3d": None, "result_3e": None, "result_3f": None,
        "timings": {}, "validator_verdicts": {}, "failure": None,
        "integrity_audit": None, "git_hash": get_git_hash(),
        "model": model_name, "mode": mode,
        "settings": {"provider": settings.get("provider"),
                     "model": settings.get("model"),
                     "temperature": settings.get("temperature", 0.0)},
        "inputs": {"evidence_path": str(input_evidence_path or ""),
                   "incidents_path": str(input_incidents_path or ""),
                   "records": len(records), "incidents": len(incidents)},
        "max_token_exposure": max_token_exposure(max_tokens_3f),
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }
    total_start = time.perf_counter()
    temperature = settings.get("temperature", 0.0)

    def _timed(stage, func, *args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - recorded, never fabricated
            bundle["timings"][stage] = round(time.perf_counter() - start, 3)
            bundle["validator_verdicts"][stage] = "error"
            bundle["failure"] = {"stage": stage, "type": classify_failure(exc),
                                 "error": str(exc)[:500]}
            return None, False
        bundle["timings"][stage] = round(time.perf_counter() - start, 3)
        bundle["validator_verdicts"][stage] = "pass"
        return result, True

    if mode == "mock":
        plan, ok = _timed("3c", _mock_plan, question)
    else:
        plan, ok = _timed("3c", Q.plan_query, client, question, temperature)
    if not ok:
        return _finish(bundle, snapshot, records, total_start)
    bundle["plan"] = plan
    result_3d, ok = _timed("3d", D3.execute_plan, plan, records, incidents)
    if not ok:
        return _finish(bundle, snapshot, records, total_start)
    bundle["result_3d"] = result_3d
    if result_3d["summary"].get("query_errors"):
        bundle["failure"] = {
            "stage": "3d", "type": "retrieval",
            "error": f"{result_3d['summary']['query_errors']} planner query(ies) failed"}
        bundle["validator_verdicts"]["3d"] = "error"
        return _finish(bundle, snapshot, records, total_start)
    if mode == "mock":
        result_3e, ok = _timed("3e", _mock_timeline, result_3d, question)
    else:
        result_3e, ok = _timed("3e", E.run_timeline, client, result_3d, question,
                               temperature)
    if not ok:
        return _finish(bundle, snapshot, records, total_start)
    bundle["result_3e"] = result_3e
    if mode == "mock":
        result_3f, ok = _timed("3f", _mock_report, result_3e, result_3d, question)
    else:
        result_3f, ok = _timed("3f", F.run_verification_report, client, result_3e,
                               result_3d, question, temperature, max_tokens_3f)
    if not ok:
        return _finish(bundle, snapshot, records, total_start)
    bundle["result_3f"] = result_3f
    return _finish(bundle, snapshot, records, total_start)


def _finish(bundle, snapshot, records, total_start):
    bundle["timings"]["total"] = round(time.perf_counter() - total_start, 3)
    bundle["integrity_audit"] = audit_integrity(
        snapshot, records, bundle["result_3d"], bundle["result_3e"], bundle["result_3f"])
    return bundle


def _load_questions(args) -> list:
    if args.questions_file:
        with Path(args.questions_file).open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ValueError("questions file must hold a JSON list")
        questions = []
        for i, entry in enumerate(data):
            if not isinstance(entry, dict) or not isinstance(
                    entry.get("question"), str) or not entry["question"].strip():
                raise ValueError(
                    f"questions file entry {i} must be "
                    f"{{id, question}} with a non-empty question")
            questions.append((str(entry.get("id", f"q{i + 1:02d}")), entry["question"]))
        return questions
    return [("q01", args.question)]


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4: end-to-end investigation run")
    parser.add_argument("--question", default=None)
    parser.add_argument("--questions-file", default=None)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--incidents", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--model", default=None)
    parser.add_argument("--timeout", type=float, default=None,
                        help="overall LLM HTTP seconds per call (sets total_timeout)")
    parser.add_argument("--max-tokens", type=int, default=None,
                        help="3F cap only; 3C/3E use their fixed constants")
    args = parser.parse_args(argv)

    if not args.question and not args.questions_file:
        print("investigation error: provide --question or --questions-file")
        return 2
    try:
        questions = _load_questions(args)
    except (OSError, ValueError) as exc:
        print(f"investigation error: bad questions file: {exc}")
        return 2
    if any(not q.strip() for _, q in questions):
        print("investigation error: questions must be non-empty")
        return 2

    evidence_path = Path(args.evidence) if args.evidence else PROJECT_ROOT / DEFAULT_EVIDENCE
    incidents_path = Path(args.incidents) if args.incidents else PROJECT_ROOT / DEFAULT_INCIDENTS
    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / DEFAULT_OUTPUT_DIR
    for path in (evidence_path, incidents_path):
        if not path.exists():
            print(f"investigation error: input not found: {path} (run Phase 2D first)")
            return 2
    try:
        records = load_evidence(evidence_path)
        incidents = load_incidents(incidents_path)
    except (OSError, ValueError) as exc:
        print(f"investigation error: bad input: {exc}")
        return 2

    settings = Q.load_llm_settings()
    if args.model:
        settings["model"] = args.model
    if args.mock:
        mode, model_name, client = "mock", "mock", None
    else:
        mode, model_name = "real", settings.get("model")
        client = Q.create_client(settings)
        if args.timeout is not None:
            client.total_timeout = float(args.timeout)
    max_tokens_3f = args.max_tokens or F.REPORT_MAX_TOKENS
    if not args.mock:
        print(f"max-token exposure per question: {max_token_exposure(max_tokens_3f)}")

    output_dir.mkdir(parents=True, exist_ok=True)
    exit_code = 0
    for qid, question in questions:
        bundle = run_question(question, records, incidents, mode, client, settings,
                              max_tokens_3f, model_name, evidence_path, incidents_path)
        path = output_dir / f"{qid}.json"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(bundle, fh, indent=2, sort_keys=True)
        status = "FAIL" if bundle["failure"] else "PASS"
        print(f"[{qid}] {status} {bundle['timings'].get('total', '?')}s "
              f"verdicts={bundle['validator_verdicts']} -> {path}")
        if bundle["failure"]:
            print(f"  failure: {bundle['failure']}")
            exit_code = 2
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
