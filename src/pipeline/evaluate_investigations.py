"""Phase 4 - Offline evaluation over saved investigation bundles (no LLM).

Reads phase4/v1 bundles and computes only objectively supported metrics.
"supported" below means structurally grounded/cited per the validators,
NOT a factual truth judgment (that requires human annotation).

Usage:
    python -m src.pipeline.evaluate_investigations --input-dir data/evaluations/run1
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SCHEMA_VERSION = "phase4/v1"

SUPPORTED_NOTE = ("'supported' means structurally grounded/cited by the "
                  "deterministic validators, NOT a factual truth judgment.")


def load_bundles(input_dir: Path) -> list:
    bundles = []
    corrupt = []
    for path in sorted(Path(input_dir).glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            corrupt.append(path.name)
            continue
        if isinstance(data, dict) and data.get("schema_version") == SCHEMA_VERSION:
            bundles.append(data)
    if corrupt:
        raise ValueError(f"corrupt bundle file(s) in {input_dir}: {sorted(corrupt)}")
    return bundles


def _latency_stats(values: list) -> dict:
    if not values:
        return {"mean": 0.0, "p50": 0.0, "max": 0.0, "n": 0}
    ordered = sorted(values)
    mid = len(ordered) // 2
    p50 = (ordered[mid] if len(ordered) % 2
           else (ordered[mid - 1] + ordered[mid]) / 2)
    return {"mean": round(statistics.mean(values), 3), "p50": round(p50, 3),
            "max": round(max(values), 3), "n": len(values)}


def evaluate(bundles: list) -> dict:
    """Compute aggregate metrics over phase4/v1 bundles (pure function)."""
    metrics: dict = {
        "schema_version": "phase4-eval/v1",
        "total_runs": len(bundles),
        "successful_runs": 0,
        "end_to_end_success_rate": 0.0,
        "per_stage_success": {},
        "supported": 0, "partially_supported": 0, "unsupported": 0,
        "supported_structural_only": True,
        "supported_note": SUPPORTED_NOTE,
        "citation_coverage": 0.0,
        "timestamp_containment_rate": 0.0,
        "audit_pass_rate": 0.0,
        "cross_video_violations": 0,
        "unmapped_hits": 0,
        "unmapped_hit_rate": 0.0,
        "stage_latency": {},
        "total_latency": {},
        "failure_taxonomy": {},
        "max_token_exposure": {},
        "modes": {},
    }
    if not bundles:
        return metrics
    modes_present = {b.get("mode", "unknown") for b in bundles}
    if len(modes_present) > 1:
        raise ValueError(
            f"mixed mock/real bundles are not allowed: {sorted(modes_present)}")

    stage_hits = cited = contained_total = contained_ok = 0
    preserved_ok = preserved_total = 0
    hits_total = hits_unmapped = 0
    for bundle in bundles:
        verdicts = bundle.get("validator_verdicts", {}) or {}
        if bundle.get("failure") is None:
            metrics["successful_runs"] += 1
        else:
            kind = (bundle.get("failure") or {}).get("type", "other")
            metrics["failure_taxonomy"][kind] = metrics["failure_taxonomy"].get(kind, 0) + 1
        for stage, verdict in verdicts.items():
            slot = metrics["per_stage_success"].setdefault(stage, {"pass": 0, "total": 0})
            slot["total"] += 1
            slot["pass"] += verdict == "pass"
        result_3f = bundle.get("result_3f") or {}
        for item in result_3f.get("verification", []) or []:
            status = item.get("status")
            if status in ("supported", "partially_supported", "unsupported"):
                metrics[status] += 1
            cited += 1 if item.get("evidence_ids") else 0
            stage_hits += 1
        audit = bundle.get("integrity_audit", {}) or {}
        for name, slot in (audit.get("stages", {}) or {}).items():
            if name in ("3e", "3f"):
                contained_total += 1
                contained_ok += slot.get("uncontained_ranges", 1) == 0
            preserved_total += 1
            preserved_ok += slot.get("pass", False)
        metrics["cross_video_violations"] += audit.get("cross_video_violations", 0)
        summary_3d = (bundle.get("result_3d") or {}).get("summary", {}) or {}
        hits_unmapped += summary_3d.get("unmapped_hits", 0)
        hits_total += summary_3d.get("matched_hits", 0) + summary_3d.get("unmapped_hits", 0)
        timings = bundle.get("timings", {}) or {}
        for stage in ("3c", "3d", "3e", "3f"):
            if stage in timings:
                metrics.setdefault(f"_lat_{stage}", []).append(timings[stage])
        if "total" in timings:
            metrics.setdefault("_lat_total", []).append(timings["total"])
        exposure = bundle.get("max_token_exposure", {}) or {}
        for key, value in exposure.items():
            metrics["max_token_exposure"][key] = value
        mode = bundle.get("mode", "unknown")
        metrics["modes"][mode] = metrics["modes"].get(mode, 0) + 1

    metrics["end_to_end_success_rate"] = round(metrics["successful_runs"] / len(bundles), 4)
    for slot in metrics["per_stage_success"].values():
        slot["rate"] = round(slot["pass"] / slot["total"], 4) if slot["total"] else 0.0
    metrics["citation_coverage"] = round(cited / stage_hits, 4) if stage_hits else 0.0
    metrics["timestamp_containment_rate"] = round(contained_ok / contained_total, 4
                                                 ) if contained_total else 0.0
    metrics["audit_pass_rate"] = round(preserved_ok / preserved_total, 4
                                       ) if preserved_total else 0.0
    metrics["unmapped_hits"] = hits_unmapped
    metrics["unmapped_hit_rate"] = round(hits_unmapped / hits_total, 4) if hits_total else 0.0
    for stage in ("3c", "3d", "3e", "3f"):
        metrics["stage_latency"][stage] = _latency_stats(metrics.pop(f"_lat_{stage}", []))
    metrics["total_latency"] = _latency_stats(metrics.pop("_lat_total", []))
    return metrics


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4: offline bundle evaluation")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"evaluation error: not a directory: {input_dir}")
        return 2
    try:
        bundles = load_bundles(input_dir)
    except ValueError as exc:
        print(f"evaluation error: {exc}")
        return 2
    if not bundles:
        print(f"evaluation error: no phase4/v1 bundles in {input_dir}")
        return 2
    try:
        metrics = evaluate(bundles)
    except ValueError as exc:
        print(f"evaluation error: {exc}")
        return 2
    print(json.dumps(metrics, indent=2, sort_keys=True))
    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2, sort_keys=True)
        print(f"Wrote metrics -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
