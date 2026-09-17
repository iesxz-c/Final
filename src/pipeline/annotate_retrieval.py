"""Manual relevance-annotation workflow for the retrieval benchmark.

Inspection only: dumps ACTUAL fused corpus records inside a query's scope
(video_id exact match plus optional time-window overlap) in deterministic
order so a human can choose relevant evidence IDs by hand.

This utility NEVER ranks, scores, or retrieves:
- no Phase 3A lexical retrieval,
- no vector retrieval,
- no LLM, no models, no inference.

Scope browsing is exhaustive within the scope (first-N display cap only),
so annotation cannot depend on any system under evaluation. Relevance
judgments must be typed into eval/retrieval_benchmark_v1.json by hand.

Usage:
    python -m src.pipeline.annotate_retrieval --check
    python -m src.pipeline.annotate_retrieval --evidence data/data_155n/fused_155/evidence.json --query-id Q05
    python -m src.pipeline.annotate_retrieval --evidence data/data_155n/fused_155/evidence.json --video-id anomaly/X/x.mp4 --start 0 --end 60
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_BENCHMARK = "eval/retrieval_benchmark_v1.json"
DEFAULT_EVIDENCE = "data/data_155n/fused_155/evidence.json"

INSPECT_FIELDS = ("evidence_id", "video_id", "start_time", "end_time",
                  "object_evidence", "generic_action_evidence",
                  "surveillance_event_evidence", "source_references",
                  "anomaly_score")


def load_entries(benchmark_path: str | Path) -> tuple:
    """Read benchmark queries with annotation status (no validation)."""
    with Path(benchmark_path).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("schema_version", "?"), data.get("queries", [])


def entry_status(entry: dict) -> str:
    """complete | marked-empty | incomplete (pure)."""
    relevant = entry.get("relevant_evidence_ids") or []
    if relevant:
        return "complete"
    if entry.get("empty_relevance_intended") is True:
        return "marked-empty"
    return "incomplete"


def check_benchmark(benchmark_path: str | Path) -> dict:
    """Per-query annotation status over the whole file (pure report)."""
    _, queries = load_entries(benchmark_path)
    rows = [{"query_id": q.get("query_id"), "status": entry_status(q)}
            for q in queries]
    return {"queries": len(rows),
            "complete": sum(1 for r in rows if r["status"] == "complete"),
            "marked_empty": sum(1 for r in rows if r["status"] == "marked-empty"),
            "incomplete": sum(1 for r in rows if r["status"] == "incomplete"),
            "rows": rows}


def _match_terms(match: str | None) -> list:
    """Split --match into OR terms (comma-separated, case-insensitive)."""
    if match is None:
        return []
    return [t.strip().lower() for t in str(match).split(",") if t.strip()]


def scope_records(records: list, video_id: str | None = None,
                  start_time: float | None = None,
                  end_time: float | None = None,
                  match: str | None = None) -> list:
    """Exhaustive scope filter in deterministic order (no ranking).

    Keeps records of one video_id whose interval overlaps [start, end].
    The optional match keeps records containing ANY of the comma-separated
    case-insensitive substrings in STORED fields (object class names,
    action/event labels incl. top-k, source references). It only reduces
    display volume for human annotation: no scoring, no ordering change,
    no retrieval, no judgments.
    Order: (video_id, start_time, evidence_id). NOT a retrieval result.
    """
    terms = _match_terms(match)
    kept = []
    for record in records:
        if video_id is not None and record.get("video_id") != video_id:
            continue
        if start_time is not None and float(record.get("end_time", 0)) < start_time:
            continue
        if end_time is not None and float(record.get("start_time", 0)) > end_time:
            continue
        if terms and not any(_record_contains(record, t) for t in terms):
            continue
        kept.append(record)
    kept.sort(key=lambda r: (str(r.get("video_id", "")),
                             float(r.get("start_time", 0)),
                             str(r.get("evidence_id", ""))))
    return kept


def _record_contains(record: dict, needle: str) -> bool:
    """Case-insensitive substring over stored evidence fields only."""
    for det in record.get("object_evidence", []) or []:
        if needle in str(det.get("class_name", "")).lower():
            return True
    for key in ("generic_action_evidence", "surveillance_event_evidence"):
        for entry in record.get(key, []) or []:
            if needle in str(entry.get("label", "")).lower():
                return True
            for top in entry.get("top_k", []) or []:
                if needle in str(top.get("label", "")).lower():
                    return True
    for ref in record.get("source_references", []) or []:
        if needle in str(ref).lower():
            return True
    return False


def format_record(record: dict) -> str:
    lines = [f"evidence_id: {record.get('evidence_id')} "
             f"| video: {record.get('video_id')} "
             f"| t: {record.get('start_time')}-{record.get('end_time')}s "
             f"| score: {record.get('anomaly_score')}"]
    objects = [(d.get("class_name"), d.get("confidence"))
               for d in record.get("object_evidence", []) or []]
    if objects:
        lines.append("  objects: " + ", ".join(
            f"{c} ({cf:.2f})" for c, cf in objects))
    for key, tag in (("generic_action_evidence", "actions"),
                     ("surveillance_event_evidence", "events")):
        labels = [(e.get("label"), e.get("confidence"))
                  for e in record.get(key, []) or []]
        if labels:
            lines.append(f"  {tag}: " + ", ".join(
                f"{label} ({cf:.4f})" for label, cf in labels))
    refs = record.get("source_references", []) or []
    if refs:
        lines.append("  refs: " + "; ".join(str(r) for r in refs))
    return "\n".join(lines)


def format_compact(record: dict) -> str:
    """One-line inspection summary (same stored fields, less verbatim)."""
    objects = sorted({str(d.get("class_name", "")) for d in
                      record.get("object_evidence", []) or [] if d.get("class_name")})
    actions = sorted({str(e.get("label", "")) for e in
                      record.get("generic_action_evidence", []) or [] if e.get("label")})
    events = sorted({str(e.get("label", "")) for e in
                     record.get("surveillance_event_evidence", []) or [] if e.get("label")})
    refs = record.get("source_references", []) or []
    return (f"{record.get('evidence_id')} | {record.get('video_id')} | "
            f"{record.get('start_time')}-{record.get('end_time')}s | "
            f"objects=[{', '.join(objects)}] actions=[{', '.join(actions)}] "
            f"events=[{', '.join(events)}] refs={len(refs)} "
            f"score={record.get('anomaly_score')}")


def _label_groups(records: list) -> dict:
    """Group scoped records by stored label/class (inspection aid only).

    Returns {group_kind: {label: [records]}} for surveillance-event labels,
    generic-action labels, and object classes. Never declares relevance.
    """
    groups: dict = {"event": {}, "action": {}, "object": {}}
    for record in records:
        for entry in record.get("surveillance_event_evidence", []) or []:
            if entry.get("label"):
                groups["event"].setdefault(str(entry["label"]), []).append(record)
        for entry in record.get("generic_action_evidence", []) or []:
            if entry.get("label"):
                groups["action"].setdefault(str(entry["label"]), []).append(record)
        for det in record.get("object_evidence", []) or []:
            if det.get("class_name"):
                groups["object"].setdefault(str(det["class_name"]), []).append(record)
    return groups


def _source_types(record: dict) -> list:
    present = []
    for key, name in (("object_evidence", "object"),
                      ("generic_action_evidence", "action"),
                      ("surveillance_event_evidence", "event")):
        if record.get(key):
            present.append(name)
    return present


def summarize_scope(records: list) -> list:
    """Compact per-label summary lines over scoped records (pure).

    Per label: record count, first/last timestamp, source-type coverage.
    Deterministic order: kind, then label. Inspection aid, not relevance.
    """
    lines = [f"scope records: {len(records)}"]
    if records:
        starts = [float(r.get("start_time", 0)) for r in records]
        ends = [float(r.get("end_time", 0)) for r in records]
        lines.append(f"span: {min(starts)}-{max(ends)}s")
    for kind in ("event", "action", "object"):
        for label in sorted(_label_groups(records)[kind]):
            members = _label_groups(records)[kind][label]
            starts = [float(r.get("start_time", 0)) for r in members]
            ends = [float(r.get("end_time", 0)) for r in members]
            types = sorted({t for r in members for t in _source_types(r)})
            lines.append(f"[{kind}] {label}: n={len(members)} "
                         f"first={min(starts)} last={max(ends)} "
                         f"sources={','.join(types)}")
    return lines


def bucket_records(records: list, bucket_seconds: float) -> list:
    """Deterministic time buckets over scoped records (pure).

    Bucket k covers [k*N, (k+1)*N) by record start_time. Per bucket: count,
    object classes, action labels, event labels, evidence IDs. No ranking,
    no selection.
    """
    if bucket_seconds is None or float(bucket_seconds) <= 0:
        raise ValueError("bucket-seconds must be positive")
    width = float(bucket_seconds)
    buckets: dict = {}
    for record in records:
        key = int(float(record.get("start_time", 0)) // width)
        buckets.setdefault(key, []).append(record)
    lines = []
    for key in sorted(buckets):
        members = sorted(buckets[key], key=lambda r: str(r.get("evidence_id", "")))
        objects = sorted({str(d.get("class_name", "")) for r in members
                          for d in r.get("object_evidence", []) or []
                          if d.get("class_name")})
        actions = sorted({str(e.get("label", "")) for r in members
                          for e in r.get("generic_action_evidence", []) or []
                          if e.get("label")})
        events = sorted({str(e.get("label", "")) for r in members
                         for e in r.get("surveillance_event_evidence", []) or []
                         if e.get("label")})
        lines.append(f"[{key * width:g}-{(key + 1) * width:g}s] n={len(members)} "
                     f"objects=[{', '.join(objects)}] actions=[{', '.join(actions)}] "
                     f"events=[{', '.join(events)}]")
        lines.append("  ids: " + ", ".join(str(r.get("evidence_id", "")) for r in members))
    return lines


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manual relevance annotation workflow")
    parser.add_argument("--benchmark", default=None)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--check", action="store_true",
                        help="report per-query annotation completeness")
    parser.add_argument("--query-id", default=None,
                        help="inspect the scope of one benchmark query")
    parser.add_argument("--video-id", default=None)
    parser.add_argument("--start", type=float, default=None)
    parser.add_argument("--end", type=float, default=None)
    parser.add_argument("--max-records", type=int, default=50,
                        help="display cap for scope dumps (0 = all)")
    parser.add_argument("--match", default=None,
                        help="comma-separated case-insensitive substrings over stored "
                             "evidence fields only (display reduction, not retrieval)")
    parser.add_argument("--compact", action="store_true",
                        help="one-line summary per record instead of full dump")
    parser.add_argument("--incident-summary", action="store_true",
                        help="per-label group summary instead of record dumps")
    parser.add_argument("--bucket-seconds", type=float, default=None,
                        help="group display into deterministic time buckets")
    parser.add_argument("--ids-only", action="store_true",
                        help="print only evidence IDs for the filtered scope")
    args = parser.parse_args(argv)

    benchmark = Path(args.benchmark) if args.benchmark else PROJECT_ROOT / DEFAULT_BENCHMARK
    if args.check:
        try:
            report = check_benchmark(benchmark)
        except (OSError, ValueError) as exc:
            print(f"annotation error: bad benchmark: {exc}")
            return 2
        for row in report["rows"]:
            print(f"{row['query_id']}: {row['status']}")
        print(f"{report['complete']}/{report['queries']} complete, "
              f"{report['marked_empty']} marked-empty, "
              f"{report['incomplete']} incomplete")
        return 0 if report["incomplete"] == 0 else 1

    evidence_path = Path(args.evidence) if args.evidence else PROJECT_ROOT / DEFAULT_EVIDENCE
    try:
        with evidence_path.open("r", encoding="utf-8") as fh:
            records = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"annotation error: bad evidence: {exc}")
        return 2

    video_id, start, end = args.video_id, args.start, args.end
    if args.query_id is not None:
        try:
            _, queries = load_entries(benchmark)
        except (OSError, ValueError) as exc:
            print(f"annotation error: bad benchmark: {exc}")
            return 2
        matches = [q for q in queries if q.get("query_id") == args.query_id]
        if not matches:
            print(f"annotation error: unknown query_id: {args.query_id}")
            return 2
        entry = matches[0]
        print(f"query: {entry.get('query')}")
        print(f"pattern: {entry.get('pattern')} | notes: {entry.get('notes')}")
        print(f"status: {entry_status(entry)}")
        scope = entry.get("scope") or {}
        video_id = scope.get("video_id")
        start = scope.get("start_time")
        end = scope.get("end_time")

    scoped = scope_records(records, video_id, start, end, args.match)
    total = len(scoped)
    summary_mode = args.ids_only or args.incident_summary or args.bucket_seconds is not None
    # Summary modes aggregate the whole scope: capping them would silently
    # bias the human's view. --max-records caps record dumps only.
    shown = scoped if summary_mode or not args.max_records or args.max_records <= 0 \
        else scoped[:args.max_records]
    header = (f"video={video_id} start={start} end={end} match={args.match}")
    if args.ids_only:
        for record in shown:
            print(record.get("evidence_id"))
    elif args.incident_summary:
        for line in summarize_scope(shown):
            print(line)
    elif args.bucket_seconds is not None:
        try:
            bucket_lines = bucket_records(shown, args.bucket_seconds)
        except ValueError as exc:
            print(f"annotation error: {exc}")
            return 2
        for line in bucket_lines:
            print(line)
    elif args.compact:
        for record in shown:
            print(format_compact(record))
    else:
        for record in shown:
            print(format_record(record))
    print(f"showing {len(shown)}/{total} scope records ({header}); "
          f"type chosen evidence_ids into relevant_evidence_ids by hand")
    return 0


if __name__ == "__main__":
    sys.exit(main())
