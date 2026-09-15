"""Phase 3B - Deterministic temporal-context retrieval (no models, no LLM).

Groups Phase 3A lexical hits by the authoritative Phase 2D incident regions
(`data/evidence/fused/incidents.json`) and returns, per matched incident,
the matched records plus contextual records: fellow incident members that
did not match, optionally expanded by N seconds around each hit
(`--context-seconds`, never across videos).

Incident membership is read verbatim from Phase 2D; no incident logic is
recreated here. All record fields are preserved verbatim; matched records
carry an extra "matched_hits" list (Phase 3A hit dicts) so matched and
contextual evidence stay distinguishable. No crime probabilities or new
scores are computed; contextual evidence is surrounding evidence only.

Usage:
    python -m src.pipeline.retrieve_temporal --query "Fighting"
    python -m src.pipeline.retrieve_temporal --query "person" --context-seconds 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.pipeline import retrieve_evidence as R

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DEFAULT_EVIDENCE = "data/evidence/fused/evidence.json"
DEFAULT_INCIDENTS = "data/evidence/fused/incidents.json"

SCHEMA_VERSION = "phase3b/v1"
UNMAPPED_NOTE = "evidence_id not listed in any Phase 2D incident"


def load_incidents(path: str | Path) -> list:
    """Read a fused incidents.json file (a JSON list of incident regions)."""
    with Path(path).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"expected a JSON list: {path}")
    return data


def build_membership(incidents: list) -> dict:
    """Map evidence_id -> incident dict (first incident wins on duplicates)."""
    membership = {}
    for incident in sorted(incidents,
                           key=lambda i: (float(i.get("start_time", 0)),
                                          str(i.get("incident_id", "")))):
        for evidence_id in incident.get("evidence_ids", []) or []:
            membership.setdefault(evidence_id, incident)
    return membership


def _record_key(record: dict) -> tuple:
    return (float(record.get("start_time", 0)), str(record.get("evidence_id", "")))


def _in_expansion(record: dict, hit: dict, context_seconds: float) -> bool:
    if record.get("video_id") != hit.get("video_id"):
        return False
    return (float(record.get("start_time", 0)) <= float(hit["end_time"]) + context_seconds
            and float(record.get("end_time", 0)) >= float(hit["start_time"]) - context_seconds)


def retrieve_temporal(records: list, incidents: list, query: str,
                      video_id: str | None = None,
                      start_time: float | None = None,
                      end_time: float | None = None,
                      sources: list | tuple | None = None,
                      context_seconds: float = 0.0,
                      limit: int | None = None) -> dict:
    """Group Phase 3A hits by Phase 2D incident with contextual records."""
    if context_seconds is None:
        context_seconds = 0.0
    if context_seconds < 0:
        raise ValueError(f"context_seconds must be >= 0: {context_seconds}")
    by_id = {r.get("evidence_id"): r for r in records}
    membership = build_membership(incidents)

    hits = R.retrieve(records, query, video_id, start_time, end_time,
                      sources, limit=None)

    matched: dict = {}  # incident_id -> {"incident": ..., "hits": [...]}
    order: list = []
    unmapped = []
    for hit in hits:
        incident = membership.get(hit["evidence_id"])
        if incident is None:
            unmapped.append({**hit, "mapping_note": UNMAPPED_NOTE})
            continue
        incident_id = incident.get("incident_id", "")
        if incident_id not in matched:
            matched[incident_id] = {"incident": incident, "hits": []}
            order.append(incident_id)
        matched[incident_id]["hits"].append(hit)

    groups = []
    for incident_id in sorted(
            order, key=lambda i: (float(matched[i]["incident"].get("start_time", 0)), i)):
        incident = matched[incident_id]["incident"]
        group_hits = matched[incident_id]["hits"]
        matched_ids = sorted({h["evidence_id"] for h in group_hits})
        hits_by_record: dict = {}
        for hit in group_hits:
            hits_by_record.setdefault(hit["evidence_id"], []).append(hit)

        member_ids = [e for e in incident.get("evidence_ids", []) or []
                      if e not in matched_ids and e in by_id]
        context_ids = list(dict.fromkeys(member_ids))  # dedupe, keep order
        if context_seconds > 0:
            extra = [r.get("evidence_id") for r in records
                     if r.get("evidence_id") not in matched_ids
                     and r.get("evidence_id") not in context_ids
                     and any(_in_expansion(r, h, context_seconds) for h in group_hits)]
            context_ids.extend(sorted(set(extra)))

        matched_evidence = []
        for evidence_id in sorted(matched_ids):
            record = dict(by_id[evidence_id])
            record["matched_hits"] = hits_by_record[evidence_id]
            matched_evidence.append(record)
        matched_evidence.sort(key=_record_key)
        contextual_evidence = [by_id[e] for e in context_ids
                               if e in by_id]
        contextual_evidence.sort(key=_record_key)

        groups.append({
            "incident_id": incident_id,
            "video_id": incident.get("video_id", ""),
            "incident_start_time": incident.get("start_time"),
            "incident_end_time": incident.get("end_time"),
            "event_hypotheses": list(incident.get("event_hypotheses", []) or []),
            "matched_evidence": matched_evidence,
            "contextual_evidence": contextual_evidence,
        })

    if limit is not None and limit > 0:
        groups = groups[:limit]
    kept = [(len(g["matched_evidence"]), len(g["contextual_evidence"])) for g in groups]

    return {
        "schema_version": SCHEMA_VERSION,
        "query": query,
        "filters": {"video_id": video_id, "start_time": start_time,
                    "end_time": end_time,
                    "source": list(sources) if sources else None,
                    "context_seconds": context_seconds},
        "groups": groups,
        "unmapped_hits": sorted(unmapped, key=lambda h: (
            str(h["video_id"]), float(h["start_time"]),
            str(h["evidence_id"]), str(h["matched_source"]))),
        "summary": {"matched_hits": len(hits),
                    "matched_records": sum(k[0] for k in kept),
                    "incident_groups": len(groups),
                    "context_records": sum(k[1] for k in kept),
                    "unmapped_hits": len(unmapped)},
    }


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3B: temporal-context retrieval")
    parser.add_argument("--query", required=True)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--incidents", default=None)
    parser.add_argument("--video-id", default=None)
    parser.add_argument("--start-time", type=float, default=None)
    parser.add_argument("--end-time", type=float, default=None)
    parser.add_argument("--source", action="append", default=None,
                        choices=list(R.ALL_SOURCES))
    parser.add_argument("--context-seconds", type=float, default=0.0,
                        help="surrounding seconds around each hit (same video only)")
    parser.add_argument("--limit", type=int, default=0,
                        help="max incident groups (0 = all)")
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    if args.context_seconds < 0:
        print("context_seconds must be >= 0")
        return 2
    evidence_path = Path(args.evidence) if args.evidence else PROJECT_ROOT / DEFAULT_EVIDENCE
    incidents_path = Path(args.incidents) if args.incidents else PROJECT_ROOT / DEFAULT_INCIDENTS
    for path in (evidence_path, incidents_path):
        if not path.exists():
            print(f"Input not found: {path} (run Phase 2D first)")
            return 2
    try:
        records = R.load_evidence(evidence_path)
        incidents = load_incidents(incidents_path)
    except (OSError, ValueError) as exc:
        print(f"Input error: {exc}")
        return 2

    result = retrieve_temporal(records, incidents, args.query, args.video_id,
                               args.start_time, args.end_time, args.source,
                               args.context_seconds,
                               args.limit if args.limit > 0 else None)
    for group in result["groups"]:
        print(f"[{group['video_id']}] {group['incident_id']} "
              f"{group['incident_start_time']}-{group['incident_end_time']}s "
              f"hypotheses={group['event_hypotheses']}")
        print(f"  matched: {[r['evidence_id'] for r in group['matched_evidence']]}")
        print(f"  context: {[r['evidence_id'] for r in group['contextual_evidence']]}")
    if result["unmapped_hits"]:
        print(f"  unmapped: {[h['evidence_id'] for h in result['unmapped_hits']]}")
    print(f"\n{result['summary']['incident_groups']} incident group(s), "
          f"{result['summary']['matched_hits']} matched hit(s), "
          f"{result['summary']['context_records']} context record(s), "
          f"{result['summary']['unmapped_hits']} unmapped "
          f"for query {args.query!r}")
    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print(f"Wrote result -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
