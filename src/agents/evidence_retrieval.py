"""Phase 3D - Evidence Retrieval Agent (deterministic, no LLM).

Executes an already-validated Phase 3C plan (phase3c/v1) against the
existing Phase 3A lexical retrieval and Phase 3B temporal-context layers.

LLM plans. Deterministic code retrieves. The planner output is
re-validated defensively with Phase 3C validation; no competing schema
is introduced and no retrieval logic is duplicated here.

Usage:
    python -m src.agents.evidence_retrieval --plan plan.json
    python -m src.agents.evidence_retrieval --query "Fighting" --mock-planner
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.pipeline import retrieve_temporal as T
from src.agents import query_planner as Q

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SCHEMA_VERSION = "phase3d/v1"


class RetrievalError(RuntimeError):
    """A planner query failed during deterministic execution."""


def load_plan(path: str | Path) -> dict:
    """Read a Phase 3C plan JSON file (must be a JSON object)."""
    with Path(path).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise Q.PlanValidationError("plan file must contain a JSON object")
    return data


def validate_plan(plan: dict) -> dict:
    """Defensively re-validate with Phase 3C validation; returns normalized plan."""
    try:
        text = json.dumps(plan)
    except (TypeError, ValueError) as exc:
        raise Q.PlanValidationError(f"plan is not JSON-serializable: {exc}") from exc
    return Q.parse_and_validate_plan(text)


def _with_provenance(hit: dict, index: int, phrase: str) -> dict:
    annotated = dict(hit)
    annotated["planner_query_index"] = index
    annotated["planner_query"] = phrase
    return annotated


def _merge_hit_lists(existing: list, new: list) -> list:
    seen = {json.dumps(h, sort_keys=True, default=str) for h in existing}
    for hit in new:
        key = json.dumps(hit, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            existing.append(hit)
    return existing


def execute_plan(plan: dict, records: list, incidents: list) -> dict:
    """Execute a validated phase3c/v1 plan; merge per-query 3B results."""
    plan = validate_plan(plan)
    context_seconds = plan["temporal_context_seconds"]

    query_results = []
    query_errors = []
    for index, item in enumerate(plan["queries"]):
        phrase, source = item["query"], item["source"]
        sources = [source] if source is not None else None
        try:
            partial = T.retrieve_temporal(
                records, incidents, phrase, plan["video_id"], plan["start_time"],
                plan["end_time"], sources, context_seconds, limit=None)
        except Exception as exc:  # noqa: BLE001 - one bad query must be reported
            query_errors.append({"planner_query_index": index,
                                 "planner_query": phrase, "error": str(exc)})
            continue
        query_results.append({"query": phrase, "source": source,
                              "planner_query_index": index,
                              "groups": partial["groups"],
                              "unmapped_hits": partial["unmapped_hits"],
                              "summary": partial["summary"]})

    merged: dict = {}
    order: list = []
    merged_unmapped: list = []
    for entry in query_results:
        index, phrase = entry["planner_query_index"], entry["query"]
        for group in entry["groups"]:
            incident_id = group["incident_id"]
            if incident_id not in merged:
                merged[incident_id] = {
                    "incident_id": incident_id, "video_id": group["video_id"],
                    "incident_start_time": group["incident_start_time"],
                    "incident_end_time": group["incident_end_time"],
                    "event_hypotheses": list(group["event_hypotheses"]),
                    "matched_evidence": {}, "contextual_evidence": {}}
                order.append(incident_id)
            slot = merged[incident_id]
            for record in group["matched_evidence"]:
                evidence_id = record["evidence_id"]
                if evidence_id not in slot["matched_evidence"]:
                    slot["matched_evidence"][evidence_id] = {
                        k: v for k, v in record.items() if k != "matched_hits"}
                    slot["matched_evidence"][evidence_id]["matched_hits"] = []
                slot["matched_evidence"][evidence_id]["matched_hits"] = _merge_hit_lists(
                    slot["matched_evidence"][evidence_id]["matched_hits"],
                    [_with_provenance(h, index, phrase)
                     for h in record.get("matched_hits", [])])
            for record in group["contextual_evidence"]:
                slot["contextual_evidence"].setdefault(record["evidence_id"], record)
        for hit in entry["unmapped_hits"]:
            merged_unmapped = _merge_hit_lists(
                merged_unmapped, [_with_provenance(hit, index, phrase)])

    groups = []
    for incident_id in sorted(
            order, key=lambda i: (float(merged[i]["incident_start_time"] or 0), i)):
        slot = merged[incident_id]
        matched = sorted(slot["matched_evidence"].values(),
                         key=lambda r: (float(r.get("start_time", 0)),
                                        str(r.get("evidence_id", ""))))
        context = sorted(slot["contextual_evidence"].values(),
                         key=lambda r: (float(r.get("start_time", 0)),
                                        str(r.get("evidence_id", ""))))
        # Matched records never also appear as context.
        matched_ids = {r["evidence_id"] for r in matched}
        context = [r for r in context if r["evidence_id"] not in matched_ids]
        groups.append({**{k: v for k, v in slot.items()
                          if k not in ("matched_evidence", "contextual_evidence")},
                       "matched_evidence": matched, "contextual_evidence": context})
    merged_unmapped.sort(key=lambda h: (str(h["video_id"]), float(h["start_time"]),
                                        str(h["evidence_id"]), str(h["matched_source"])))

    matched_hits = sum(e["summary"]["matched_hits"] for e in query_results)
    return {
        "schema_version": SCHEMA_VERSION,
        "plan": plan,
        "query_results": query_results,
        "query_errors": query_errors,
        "merged_results": {"groups": groups, "unmapped_hits": merged_unmapped},
        "summary": {"planner_queries": len(plan["queries"]),
                    "matched_hits": matched_hits,
                    "incident_groups": len(groups),
                    "context_records": sum(len(g["contextual_evidence"]) for g in groups),
                    "unmapped_hits": len(merged_unmapped),
                    "query_errors": len(query_errors)},
    }


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3D: evidence retrieval agent")
    parser.add_argument("--plan", default=None, help="path to a phase3c/v1 plan JSON file")
    parser.add_argument("--query", default=None,
                        help="convenience testing path only (uses mock planner)")
    parser.add_argument("--mock-planner", action="store_true",
                        help="build the plan from --query with the mock LLM (testing only)")
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--incidents", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    if args.plan is not None:
        try:
            plan = load_plan(args.plan)
        except (OSError, ValueError, Q.PlanValidationError) as exc:
            print(f"retrieval error: bad plan file: {exc}")
            return 2
    elif args.mock_planner and args.query:
        from src.agents.llm_client import MockLLMClient
        from src.agents.query_planner import _mock_response

        print("note: mock-planner convenience path (testing only), not the 3C architecture")
        try:
            plan = Q.plan_query(MockLLMClient(_mock_response(args.query)), args.query)
        except Q.PlanValidationError as exc:
            print(f"retrieval error: mock plan invalid: {exc}")
            return 2
    else:
        print("retrieval error: provide --plan <file> (or --query <text> --mock-planner)")
        return 2

    evidence_path = Path(args.evidence) if args.evidence else PROJECT_ROOT / T.DEFAULT_EVIDENCE
    incidents_path = Path(args.incidents) if args.incidents else PROJECT_ROOT / T.DEFAULT_INCIDENTS
    for path in (evidence_path, incidents_path):
        if not path.exists():
            print(f"retrieval error: input not found: {path} (run Phase 2D first)")
            return 2
    try:
        records = T.R.load_evidence(evidence_path)
        incidents = T.load_incidents(incidents_path)
    except (OSError, ValueError) as exc:
        print(f"retrieval error: bad input: {exc}")
        return 2

    try:
        result = execute_plan(plan, records, incidents)
    except Q.PlanValidationError as exc:
        print(f"retrieval error: invalid plan: {exc}")
        return 2

    print(json.dumps(result, indent=2))
    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print(f"Wrote result -> {args.output}")
    if result["summary"]["query_errors"]:
        print(f"retrieval error: {result['summary']['query_errors']} planner query(ies) failed")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
