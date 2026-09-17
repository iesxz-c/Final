"""Phase 4 - API/agent evaluation harness (versioned benchmark workload).

Runs the EXISTING investigation chain (3C -> 3D -> 3E -> 3F via
run_investigation.run_question) over a versioned benchmark question set and
records per-investigation results plus aggregate metrics. No pipeline
behavior is changed here; this module only observes.

Token usage is captured exactly as the provider reports it (Meta Responses
`usage` block) and never estimated. Cost is computed only when explicit
authoritative per-1k pricing is supplied; otherwise it stays null.

Usage:
    python -m src.pipeline.api_eval --mock --output-dir data/evaluations/api/v1
    python -m src.pipeline.api_eval --benchmark eval/api_benchmark_v1.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.agents import query_planner as Q
from src.agents import verification_report as F
from src.agents.llm_client import LLMClient, LLMError, META_RESPONSES_ENDPOINT
from src.pipeline import evaluate_investigations as EV
from src.pipeline import run_investigation as R
from src.pipeline.retrieve_evidence import load_evidence
from src.pipeline.retrieve_temporal import load_incidents

SCHEMA_VERSION = "api-eval/v1"
LLM_STAGES = ("3c", "3e", "3f")

#: Forbidden-phrase buckets for safety-violation counting. The 3F validator
#: is authoritative for rejection; this table only buckets the phrase the
#: validator itself cited in a failure message. Documented heuristic, not
#: a model-output judgment.
SAFETY_BUCKETS = {
    "identity": ("suspect", "perpetrator", "victim", "offender", "guilty"),
    "causality": ("caused", "led to"),
    "unsupported_crime_confirmation": ("definitely occurred", "this proves",
                                       "proves that", "proves"),
}


class RecordingClient(LLMClient):
    """Delegate wrapper that snapshots provider usage after each call.

    Records the delegate's `last_usage` (or None when the provider
    supplied no usage block) in call order. Never touches headers, keys,
    or request bodies.
    """

    def __init__(self, delegate: LLMClient):
        self._delegate = delegate
        self.usages: list = []

    def generate_structured(self, system_prompt: str, user_prompt: str,
                            temperature: float = 0.0,
                            response_format: dict | None = None,
                            max_tokens: int | None = None) -> str:
        try:
            return self._delegate.generate_structured(
                system_prompt, user_prompt, temperature=temperature,
                response_format=response_format, max_tokens=max_tokens)
        finally:
            self.usages.append(getattr(self._delegate, "last_usage", None))

    def __getattr__(self, name: str):
        return getattr(self.__dict__["_delegate"], name)


def _latency_stats(values: list) -> dict:
    """{mean, median, p95, n}; statistics omitted when n is 0."""
    stats: dict = {"n": len(values)}
    if not values:
        return stats
    ordered = sorted(values)
    stats["mean"] = round(statistics.mean(values), 3)
    stats["median"] = round(statistics.median(values), 3)
    stats["p95"] = round(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)], 3)
    return stats


def _rate(numerator: int, denominator: int) -> dict | None:
    """{value, numerator, denominator}; None when the denominator is zero."""
    if not denominator:
        return None
    return {"value": round(numerator / denominator, 4),
            "numerator": numerator, "denominator": denominator}


def _safety_counts(bundle: dict) -> dict:
    """Bucket the validator-cited phrase from a 3F safety rejection.

    Counts only failures where the 3F validator itself refused output for
    unsupported language, using the phrase it quoted. All other bundles
    contribute zero.
    """
    counts = {bucket: 0 for bucket in SAFETY_BUCKETS}
    failure = bundle.get("failure") or {}
    if failure.get("stage") != "3f" or failure.get("type") != "validation":
        return counts
    error = str(failure.get("error", ""))
    if "unsupported language" not in error:
        return counts
    quoted = re.findall(r"'([^']+)'", error)
    for phrase in quoted:
        for bucket, phrases in SAFETY_BUCKETS.items():
            if phrase in phrases:
                counts[bucket] += 1
    return counts


def _claim_counts(bundle: dict) -> dict:
    counts = {"supported": 0, "partially_supported": 0, "unsupported": 0,
              "cited": 0, "total": 0}
    for item in ((bundle.get("result_3f") or {}).get("verification", []) or []):
        status = item.get("status")
        if status in counts:
            counts[status] += 1
        counts["cited"] += 1 if item.get("evidence_ids") else 0
        counts["total"] += 1
    return counts


def _schema_valid(bundle: dict) -> bool:
    verdicts = {k: v for k, v in (bundle.get("validator_verdicts", {}) or {}).items()
                if k in LLM_STAGES}
    return bool(verdicts) and all(v == "pass" for v in verdicts.values())


def build_record(entry: dict, bundle: dict, usages: list,
                 cost: float | None) -> dict:
    """Derive one api-eval/v1 record from a phase4/v1 bundle (pure)."""
    verdicts = bundle.get("validator_verdicts", {}) or {}
    timings = bundle.get("timings", {}) or {}
    failure = bundle.get("failure")
    stage_results = {s: verdicts.get(s, "not_reached") for s in ("3c", "3d", "3e", "3f")}
    # usages has one entry per LLM call made, in chain order (3c, 3e, 3f).
    # A stage with no entry never called the model: the agent took its
    # designed empty-evidence short-circuit (no fabrication), which is
    # distinct from a call that returned no usage block.
    llm_called = {stage: i < len(usages) for i, stage in enumerate(LLM_STAGES)}
    usage_by_stage = {stage: (usages[i] if i < len(usages) else None)
                      for i, stage in enumerate(LLM_STAGES)}
    claims = _claim_counts(bundle)
    audit = bundle.get("integrity_audit", {}) or {}
    uncontained = sum((audit.get("stages", {}) or {}).get(s, {}).get(
        "uncontained_ranges", 0) for s in ("3e", "3f"))
    summary_3d = (bundle.get("result_3d") or {}).get("summary", {}) or {}
    return {
        "schema_version": SCHEMA_VERSION,
        "query_id": entry["query_id"],
        "question": entry["question"],
        "expected_intent": entry.get("expected_intent"),
        "video_constraint": entry.get("video_constraint"),
        "temporal_constraint": entry.get("temporal_constraint"),
        "purpose": entry.get("purpose"),
        "provider": (bundle.get("settings", {}) or {}).get("provider"),
        "model": bundle.get("model"),
        "mode": bundle.get("mode"),
        "stage_results": stage_results,
        "llm_called": llm_called,
        "stage_latencies": {s: timings.get(s) for s in ("3c", "3d", "3e", "3f")},
        "end_to_end_latency": timings.get("total"),
        "api_status": "ok" if failure is None else (failure or {}).get("type", "other"),
        "failure": failure,
        "schema_valid": _schema_valid(bundle),
        "grounding": {
            "claims_cited": claims["cited"],
            "claims_total": claims["total"],
            "audit_pass": audit.get("overall_pass"),
            "cross_video_violations": audit.get("cross_video_violations", 0),
            "temporal_uncontained_ranges": uncontained,
        },
        "claims": {k: claims[k] for k in
                   ("supported", "partially_supported", "unsupported")},
        "safety_violations": _safety_counts(bundle),
        "retrieval": {
            "matched_hits": summary_3d.get("matched_hits", 0),
            "unmapped_hits": summary_3d.get("unmapped_hits", 0),
            "query_errors": summary_3d.get("query_errors", 0),
        },
        "token_usage": usage_by_stage,
        "cost_usd": cost,
        "timestamp": bundle.get("run_utc"),
    }


def _cost_for(usages: list, pricing: dict | None) -> float | None:
    if pricing is None:
        return None
    total = 0.0
    for usage in usages:
        if not usage:
            continue
        total += usage.get("input_tokens", 0) / 1000 * pricing["input_per_1k"]
        total += usage.get("output_tokens", 0) / 1000 * pricing["output_per_1k"]
    return round(total, 6)


def aggregate(records: list, bundles: list, meta: dict) -> dict:
    """Aggregate api-eval/v1 metrics (pure). Zero-denominator rates omitted."""
    metrics: dict = {"schema_version": SCHEMA_VERSION, "meta": meta,
                     "base": EV.evaluate(bundles)}
    total = len(records)
    metrics["total_investigations"] = total
    ok = sum(1 for r in records if r["failure"] is None)
    metrics["successful_investigations"] = ok
    metrics["investigation_success_rate"] = _rate(ok, total)

    for stage in ("3c", "3e", "3f"):
        reached = [r for r in records if r["stage_results"][stage] != "not_reached"]
        passed = sum(1 for r in reached if r["stage_results"][stage] == "pass")
        metrics[f"{stage}_success_rate"] = _rate(passed, len(reached))

    api_ok = sum(1 for r in records if r["api_status"] == "ok")
    metrics["api_success_rate"] = _rate(api_ok, total)
    schema_ok = sum(1 for r in records if r["schema_valid"])
    metrics["schema_valid_response_rate"] = _rate(schema_ok, total)

    for stage in ("3c", "3e", "3f"):
        metrics[f"{stage}_latency"] = _latency_stats(
            [r["stage_latencies"][stage] for r in records
             if r["stage_latencies"][stage] is not None])
    metrics["end_to_end_latency"] = _latency_stats(
        [r["end_to_end_latency"] for r in records
         if r["end_to_end_latency"] is not None])

    claims = {k: sum(r["claims"][k] for r in records)
              for k in ("supported", "partially_supported", "unsupported")}
    total_claims = sum(claims.values())
    metrics["supported_claim_rate"] = _rate(claims["supported"], total_claims)
    metrics["partial_claim_rate"] = _rate(claims["partially_supported"], total_claims)
    metrics["unsupported_claim_rate"] = _rate(claims["unsupported"], total_claims)

    cited = sum(r["grounding"]["claims_cited"] for r in records)
    metrics["grounding_rate"] = _rate(cited, total_claims)
    temporal_ok = sum(1 for r in records
                      if r["grounding"]["temporal_uncontained_ranges"] == 0)
    metrics["temporal_grounding_rate"] = _rate(temporal_ok, total)

    for bucket in SAFETY_BUCKETS:
        metrics[f"{bucket}_violation_count"] = sum(
            r["safety_violations"][bucket] for r in records)

    with_usage = [r for r in records
                  if any(r["token_usage"][s] for s in LLM_STAGES)]
    if with_usage:
        ins = [u["input_tokens"] for r in with_usage for u in
               (r["token_usage"][s] for s in LLM_STAGES) if u]
        outs = [u["output_tokens"] for r in with_usage for u in
                (r["token_usage"][s] for s in LLM_STAGES) if u]
        metrics["token_usage"] = {
            "status": "available",
            "investigations_with_usage": len(with_usage),
            "investigations_total": total,
            "total_input_tokens": sum(ins),
            "total_output_tokens": sum(outs),
            "mean_input_tokens": round(statistics.mean(ins), 1),
            "mean_output_tokens": round(statistics.mean(outs), 1),
        }
    else:
        metrics["token_usage"] = {
            "status": "unavailable",
            "reason": "provider responses supplied no usage block",
            "investigations_with_usage": 0,
            "investigations_total": total,
        }
    costs = [r["cost_usd"] for r in records if r["cost_usd"] is not None]
    if costs:
        metrics["cost_usd"] = {
            "status": "available",
            "total": round(sum(costs), 6),
            "mean": round(statistics.mean(costs), 6),
            "n": len(costs),
        }
    else:
        metrics["cost_usd"] = {
            "status": "unavailable",
            "reason": "no authoritative Meta pricing configured",
            "value": None,
        }
    return metrics


def select_entries(entries: list, only: str | None) -> list:
    """Filter benchmark entries by comma-separated query_id (pure)."""
    if not only:
        return entries
    wanted = [q.strip() for q in only.split(",") if q.strip()]
    picked = [e for e in entries if e["query_id"] in wanted]
    missing = [q for q in wanted if q not in {e["query_id"] for e in entries}]
    if missing:
        raise ValueError(f"unknown query_id(s): {missing}")
    return picked


def combine_benchmark(original_dir: Path, rerun_dir: Path,
                      rerun_ids: list, output_dir: Path,
                      meta: dict) -> dict:
    """Merge original successes with rerun results (pure file assembly).

    Takes every question from original_dir except rerun_ids, which come
    from rerun_dir. Writes bundles + records + aggregate metrics to
    output_dir. Each question appears exactly once.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    bundles, api_records = [], []
    for qid in sorted(_qid_set(original_dir) | _qid_set(rerun_dir)):
        source = rerun_dir if qid in set(rerun_ids) else original_dir
        bundle = json.loads((source / f"{qid}.json").read_text(encoding="utf-8"))
        record = json.loads((source / f"{qid}.api.json").read_text(encoding="utf-8"))
        bundles.append(bundle)
        api_records.append(record)
        with (output_dir / f"{qid}.json").open("w", encoding="utf-8") as fh:
            json.dump(bundle, fh, indent=2, sort_keys=True)
        with (output_dir / f"{qid}.api.json").open("w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2, sort_keys=True)
    ordered = sorted(api_records, key=lambda r: r["query_id"])
    metrics = aggregate(ordered, bundles, meta)
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, sort_keys=True)
    return metrics


def _qid_set(directory: Path) -> set:
    return {p.name[:-len(".api.json")] for p in directory.glob("*.api.json")}


def _load_benchmark(path: Path) -> tuple:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    version = data.get("benchmark_version")
    questions = data.get("questions", [])
    if not version or not isinstance(questions, list) or not questions:
        raise ValueError(f"bad benchmark file: {path}")
    entries = []
    for i, q in enumerate(questions):
        if not isinstance(q, dict) or not str(q.get("question", "")).strip():
            raise ValueError(f"benchmark entry {i} needs a non-empty question")
        entries.append({
            "query_id": str(q.get("query_id", f"q{i + 1:02d}")),
            "question": q["question"].strip(),
            "expected_intent": q.get("expected_intent"),
            "video_constraint": q.get("video_constraint"),
            "temporal_constraint": q.get("temporal_constraint"),
            "purpose": q.get("purpose"),
        })
    return version, entries


def run_benchmark(entries: list, records_data: list, incidents: list,
                  mode: str, make_client, settings: dict, max_tokens_3f: int,
                  output_dir: Path, pricing: dict | None,
                  meta: dict) -> dict:
    """Execute every benchmark entry through run_question; write artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    bundles, api_records = [], []
    for entry in entries:
        delegate = make_client()
        client = RecordingClient(delegate) if mode == "real" else delegate
        bundle = R.run_question(
            entry["question"], records_data, incidents, mode, client, settings,
            max_tokens_3f, settings.get("model") if mode == "real" else mode,
            None, None)
        usages = client.usages if isinstance(client, RecordingClient) else []
        record = build_record(entry, bundle, usages,
                              _cost_for(usages, pricing))
        bundles.append(bundle)
        api_records.append(record)
        with (output_dir / f"{entry['query_id']}.json").open(
                "w", encoding="utf-8") as fh:
            json.dump(bundle, fh, indent=2, sort_keys=True)
        with (output_dir / f"{entry['query_id']}.api.json").open(
                "w", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2, sort_keys=True)
    ordered = sorted(api_records, key=lambda r: r["query_id"])
    metrics = aggregate(ordered, bundles, meta)
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, sort_keys=True)
    return metrics


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4: API/agent benchmark")
    parser.add_argument("--benchmark", default=None)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--incidents", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--mock", action="store_true",
                        help="offline mode: deterministic mock LLM, no API key needed")
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--no-total-timeout", action="store_true",
                        help="remove the per-call overall time bound entirely "
                             "(no replacement budget is invented)")
    parser.add_argument("--no-socket-timeout", action="store_true",
                        help="remove the per-read socket bound entirely, so long "
                             "server-side generations are awaited instead of cut "
                             "off (no replacement budget is invented)")
    parser.add_argument("--only", default=None,
                        help="comma-separated query_id subset to execute")
    parser.add_argument("--combine", default=None,
                        help="original benchmark dir to complete with rerun results")
    parser.add_argument("--with-rerun", default=None,
                        help="rerun dir supplying replacement results (needs --combine)")
    parser.add_argument("--rerun-ids", default=None,
                        help="comma-separated query_id list taken from --with-rerun")
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--input-price", type=float, default=None,
                        help="authoritative USD per 1k input tokens (else cost stays null)")
    parser.add_argument("--output-price", type=float, default=None,
                        help="authoritative USD per 1k output tokens (else cost stays null)")
    args = parser.parse_args(argv)

    benchmark = Path(args.benchmark) if args.benchmark else PROJECT_ROOT / "eval/api_benchmark_v1.json"
    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / "data/evaluations/api/v1"

    if args.combine:
        if not args.with_rerun or not args.rerun_ids or not args.output_dir:
            print("api eval error: --combine needs --with-rerun, --rerun-ids and --output-dir")
            return 2
        rerun_ids = [q.strip() for q in args.rerun_ids.split(",") if q.strip()]
        orig_meta = json.loads((Path(args.combine) / "metrics.json").read_text(
            encoding="utf-8"))["meta"]
        meta = dict(orig_meta)
        meta["combined_from"] = {"original": args.combine, "rerun": args.with_rerun,
                                 "rerun_ids": rerun_ids}
        meta["git_revision"] = R.get_git_hash()
        meta["run_utc"] = datetime.now(timezone.utc).isoformat()
        try:
            metrics = combine_benchmark(Path(args.combine), Path(args.with_rerun),
                                        rerun_ids, output_dir, meta)
        except (OSError, ValueError, KeyError) as exc:
            print(f"api eval error: {exc}")
            return 2
        print(f"api eval combined: {metrics['successful_investigations']}/"
              f"{metrics['total_investigations']} ok -> {output_dir / 'metrics.json'}")
        return 0

    if args.timeout is not None and args.no_total_timeout:
        print("api eval error: --timeout and --no-total-timeout conflict")
        return 2
    try:
        version, entries = _load_benchmark(benchmark)
        entries = select_entries(entries, args.only)
        records_data = load_evidence(
            Path(args.evidence) if args.evidence else PROJECT_ROOT / R.DEFAULT_EVIDENCE)
        incidents = load_incidents(
            Path(args.incidents) if args.incidents else PROJECT_ROOT / R.DEFAULT_INCIDENTS)
    except (OSError, ValueError) as exc:
        print(f"api eval error: bad input: {exc}")
        return 2

    settings = Q.load_llm_settings()
    max_tokens_3f = args.max_tokens or F.REPORT_MAX_TOKENS
    pricing = None
    if args.input_price is not None or args.output_price is not None:
        if args.input_price is None or args.output_price is None:
            print("api eval error: --input-price and --output-price are required together")
            return 2
        pricing = {"input_per_1k": args.input_price,
                   "output_per_1k": args.output_price}

    def _factory():
        # Mock mode never touches this client: run_question answers mock
        # stages from deterministic fixtures. Real mode builds one client
        # per question so usage snapshots never leak across questions.
        if args.mock:
            return None
        client = Q.create_client(settings)
        if args.no_total_timeout:
            client.total_timeout = None
        elif args.timeout is not None:
            client.total_timeout = float(args.timeout)
        if args.no_socket_timeout:
            client.timeout = None
        return client

    mode = "mock" if args.mock else "real"
    started = time.perf_counter()
    run_utc = datetime.now(timezone.utc).isoformat()
    meta = {
        "benchmark_version": version,
        "provider": "mock" if args.mock else settings.get("provider"),
        "model": "mock" if args.mock else settings.get("model"),
        "endpoint": None if args.mock else META_RESPONSES_ENDPOINT,
        "git_revision": R.get_git_hash(),
        "run_utc": run_utc,
        "n_questions": len(entries),
        "execution": {
            "temperature": settings.get("temperature", 0.0),
            "timeout": args.timeout,
            "total_timeout_unbounded": bool(args.no_total_timeout),
            "socket_timeout_unbounded": bool(args.no_socket_timeout),
            "max_tokens_3f": max_tokens_3f,
            "pricing_supplied": pricing is not None,
        },
    }
    try:
        metrics = run_benchmark(entries, records_data, incidents, mode,
                                _factory, settings, max_tokens_3f, output_dir,
                                pricing, meta)
    except (OSError, ValueError, KeyError, LLMError) as exc:
        print(f"api eval error: {exc}")
        return 2
    wall = round(time.perf_counter() - started, 1)
    print(f"api eval: {metrics['successful_investigations']}/"
          f"{metrics['total_investigations']} ok "
          f"(api_ok={metrics['api_success_rate']}) "
          f"tokens={metrics['token_usage']['status']} "
          f"cost={metrics['cost_usd']['status']} "
          f"wall={wall}s -> {output_dir / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
