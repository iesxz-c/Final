"""Phase 3A - Deterministic lexical evidence retrieval (no models, no LLM).

Searches the EXISTING Phase 2D fused evidence
(`data/evidence/fused/evidence.json`) with case-insensitive substring
matching over video/evidence ids, YOLO object class names, generic-action
labels, surveillance-event labels (including top-k), and source references.

Timestamps and confidences are preserved verbatim from the stored records;
nothing is inferred. Ordering is deterministic: exact matches first, then
higher confidence, then (video_id, start_time, evidence_id, source, label).

Usage:
    python -m src.pipeline.retrieve_evidence --query "Assault"
    python -m src.pipeline.retrieve_evidence --query "person" --video-id V --limit 10
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_EVIDENCE = "data/evidence/fused/evidence.json"

SOURCE_OBJECT = "object"
SOURCE_ACTION = "generic_action"
SOURCE_EVENT = "surveillance_event"
SOURCE_RECORD = "record"
ALL_SOURCES = (SOURCE_OBJECT, SOURCE_ACTION, SOURCE_EVENT, SOURCE_RECORD)


def _norm(text) -> str:
    return str(text).strip().lower()


def load_evidence(path: str | Path) -> list:
    """Read a fused evidence.json file (a JSON list of records)."""
    with Path(path).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"expected a JSON list: {path}")
    return data


def _record_in_window(record: dict, start_time: float | None,
                      end_time: float | None) -> bool:
    if start_time is not None and float(record.get("end_time", 0)) < start_time:
        return False
    if end_time is not None and float(record.get("start_time", 0)) > end_time:
        return False
    return True


def _make_hit(record: dict, matched_source: str, matched_id: str,
              matched_label: str, confidence: float,
              source_reference: str) -> dict:
    return {
        "video_id": record.get("video_id", ""),
        "evidence_id": record.get("evidence_id", ""),
        "start_time": record.get("start_time"),
        "end_time": record.get("end_time"),
        "matched_source": matched_source,
        "matched_id": matched_id,
        "matched_label": matched_label,
        "confidence": confidence,
        "source_reference": source_reference,
        "anomaly_score": record.get("anomaly_score", 0.0),
    }


def _label_hits(record: dict, entries: list, source: str,
                query_norm: str) -> list:
    """One hit per matching (entry, label-text) pair, incl. top-k entries."""
    hits = []
    seen = set()
    for entry in entries:
        candidates = [(entry.get("label", ""), entry.get("confidence", 0.0))]
        for top in entry.get("top_k", []) or []:
            candidates.append((top.get("label", ""), top.get("confidence", 0.0)))
        item_id = entry.get("observation_id", "")
        ref = entry.get("source_reference", "")
        for text, conf in candidates:
            if query_norm in _norm(text) and (item_id, str(text)) not in seen:
                seen.add((item_id, str(text)))
                hits.append(_make_hit(record, source, item_id, str(text),
                                      float(conf), str(ref)))
    return hits


def iter_record_hits(record: dict, query_norm: str) -> list:
    """All lexical hits within one fused record (unsorted)."""
    hits = []
    for det in record.get("object_evidence", []) or []:
        if query_norm in _norm(det.get("class_name", "")):
            ts = det.get("timestamp_seconds", record.get("start_time"))
            hits.append(_make_hit(
                record, SOURCE_OBJECT, det.get("detection_id", ""),
                str(det.get("class_name", "")), float(det.get("confidence", 0.0)),
                f"{record.get('video_id', '')}@t={ts}s"))
    hits.extend(_label_hits(record, record.get("generic_action_evidence", []) or [],
                            SOURCE_ACTION, query_norm))
    hits.extend(_label_hits(record, record.get("surveillance_event_evidence", []) or [],
                            SOURCE_EVENT, query_norm))
    for field in ("video_id", "evidence_id"):
        value = str(record.get(field, ""))
        if value and query_norm in _norm(value):
            hits.append(_make_hit(
                record, SOURCE_RECORD, value, value,
                float(record.get("anomaly_score", 0.0)),
                (record.get("source_references", []) or [""])[0]))
    for ref in record.get("source_references", []) or []:
        if ref and query_norm in _norm(ref):
            hits.append(_make_hit(
                record, SOURCE_RECORD, str(ref), str(ref),
                float(record.get("anomaly_score", 0.0)), str(ref)))
    return hits


def retrieve(records: list, query: str, video_id: str | None = None,
             start_time: float | None = None, end_time: float | None = None,
             sources: list | tuple | None = None,
             limit: int | None = None) -> list:
    """Deterministic lexical search over fused records.

    Empty/blank queries match nothing. `sources` restricts matched_source.
    `limit` caps hits (None or <= 0 means all).
    """
    if not query or not str(query).strip():
        return []
    query_norm = _norm(query)
    wanted = set(sources) if sources else None
    hits = []
    for record in records:
        if video_id is not None and record.get("video_id") != video_id:
            continue
        if not _record_in_window(record, start_time, end_time):
            continue
        for hit in iter_record_hits(record, query_norm):
            if wanted is not None and hit["matched_source"] not in wanted:
                continue
            hits.append(hit)

    def _key(hit: dict):
        exact = 0 if _norm(hit["matched_label"]) == query_norm else 1
        return (exact, -float(hit["confidence"]), str(hit["video_id"]),
                float(hit["start_time"]), str(hit["evidence_id"]),
                str(hit["matched_source"]), str(hit["matched_label"]),
                str(hit["matched_id"]))

    hits.sort(key=_key)
    if limit is not None and limit > 0:
        hits = hits[:limit]
    return hits


def format_hit(hit: dict) -> str:
    return (f"[{hit['video_id']}] {hit['evidence_id']} "
            f"{hit['start_time']}-{hit['end_time']}s | {hit['matched_source']} | "
            f"{hit['matched_label']} | conf={hit['confidence']} | {hit['source_reference']}")


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3A: lexical evidence retrieval")
    parser.add_argument("--query", required=True, help="case-insensitive substring to match")
    parser.add_argument("--evidence", default=None, help="override fused evidence.json path")
    parser.add_argument("--video-id", default=None, help="restrict to one video_id (exact)")
    parser.add_argument("--start-time", type=float, default=None)
    parser.add_argument("--end-time", type=float, default=None)
    parser.add_argument("--source", action="append", default=None,
                        choices=list(ALL_SOURCES),
                        help="restrict matched source type (repeatable)")
    parser.add_argument("--limit", type=int, default=20,
                        help="max hits to show (0 = all)")
    parser.add_argument("--output", default=None, help="write hits as JSON to PATH")
    args = parser.parse_args(argv)

    evidence_path = Path(args.evidence) if args.evidence else PROJECT_ROOT / DEFAULT_EVIDENCE
    if not evidence_path.exists():
        print(f"Evidence not found: {evidence_path} (run Phase 2D first)")
        return 2
    try:
        records = load_evidence(evidence_path)
    except (OSError, ValueError) as exc:
        print(f"Evidence error: {exc}")
        return 2

    limit = None if args.limit is not None and args.limit <= 0 else args.limit
    hits = retrieve(records, args.query, args.video_id, args.start_time,
                    args.end_time, args.source, limit)

    for hit in hits:
        print(format_hit(hit))
    print(f"{len(hits)} hit(s) for query {args.query!r} "
          f"over {len(records)} records ({evidence_path})")
    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as fh:
            json.dump(hits, fh, indent=2)
        print(f"Wrote {len(hits)} hits -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
