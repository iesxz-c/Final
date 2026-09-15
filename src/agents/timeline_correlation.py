"""Phase 3E - Timeline and Correlation Agent (LLM reasons, Python validates).

Consumes a validated Phase 3D result (phase3d/v1) and uses the existing
Phase 3C LLM interface to reason about temporal relationships over the
supplied evidence only. No retrieval, no footage, no new predictions.

Every timeline item, correlation, and inference must cite evidence IDs
from the input; Python validates existence, timestamp grounding, and the
factual structure of each claimed relationship. Model labels are treated
as hypotheses, never as confirmed crimes.

Usage:
    python -m src.agents.timeline_correlation --input phase3d_result.json
    python -m src.agents.timeline_correlation --input phase3d_result.json --mock
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.agents.llm_client import LLMError, MockLLMClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SCHEMA_VERSION = "phase3e/v1"
EXPECTED_3D_SCHEMA = "phase3d/v1"
ADJACENCY_GAP_SECONDS = 10.0
MAX_TOKENS = 4096

CORRELATION_TYPES = ("temporal_overlap", "temporal_sequence", "same_incident",
                     "cross_source_support", "persistent_event")

SYSTEM_PROMPT = """You are the Timeline and Correlation Agent in a CCTV investigation system.

You receive structured evidence retrieved by another component.

You do not have access to CCTV footage.

You must reason ONLY over the supplied evidence.

You must not invent evidence IDs, timestamps, detections, people,
events, confidence values, crime probabilities, identities, or facts.

Model labels such as Fighting, Assault, Robbery, etc. are evidence
hypotheses and must not automatically be described as confirmed crimes.
A person detection temporally overlapping a Fighting hypothesis does NOT
mean the detected person was fighting, and model agreement does NOT mean
one model confirms another.

Every observation, correlation, and inference must cite the evidence IDs
that support it. Reference only evidence IDs present in the input, and
keep every timestamp inside the time range of the evidence cited.

Use cautious language: "the evidence indicates...", "the available
evidence suggests...", "the model produced...", "the evidence is
consistent with...". Never state that a crime definitely occurred,
never identify suspects or victims, and never claim causation from
temporal correlation.

Allowed correlation types (use exactly these strings):
- temporal_overlap: two or more evidence records with overlapping time intervals.
- temporal_sequence: one evidence interval occurs before another.
- same_incident: evidence records belonging to the same Phase 2D incident.
- cross_source_support: evidence from different source types overlaps or is temporally related (source agreement only, never confirmation).
- persistent_event: compatible event evidence persists across adjacent or nearby temporal windows.

Keep evidence from different videos separate. Never create a correlation
between different videos.

Be concise. Timeline entries should represent meaningful temporal
segments, not necessarily every individual evidence window: adjacent
windows describing persistent activity SHOULD be consolidated into a
single timeline item citing all of their evidence IDs. Do not repeat
identical observations per window, and keep correlations, inferences,
and limitations brief. Consolidation never changes the underlying
evidence: keep every timestamp inside the union of the cited evidence,
cite every ID the claim relies on, and never drop grounding IDs to
shorten the response.

If the supplied evidence is insufficient, say so in limitations rather
than guessing.

The output MUST contain exactly these five top-level keys: timeline,
correlations, inferences, limitations, schema_version. Do not add
temporal_relationships or any other key.

Return only the required JSON structure."""


class TimelineValidationError(ValueError):
    """A model-produced timeline failed structural validation."""


def _strip_fences(text: str) -> str:
    stripped = str(text).strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


#: JSON Schema for providers with `response_format: {type: json_schema}`.
#: Mirrors CORRELATION_TYPES; Python validation remains authoritative.
TIMELINE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "enum": [SCHEMA_VERSION]},
        "timeline": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "start_time": {"type": "number"},
                "end_time": {"type": "number"},
                "evidence_ids": {"type": "array", "minItems": 1,
                                 "items": {"type": "string", "minLength": 1}},
                "observation": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "minLength": 1},
                        "evidence_ids": {"type": "array", "minItems": 1,
                                         "items": {"type": "string", "minLength": 1}},
                    },
                    "required": ["text", "evidence_ids"],
                    "additionalProperties": False},
            },
            "required": ["start_time", "end_time", "evidence_ids", "observation"],
            "additionalProperties": False}},
        "correlations": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": list(CORRELATION_TYPES)},
                "evidence_ids": {"type": "array", "minItems": 1,
                                 "items": {"type": "string", "minLength": 1}},
                "description": {"type": "string", "minLength": 1},
            },
            "required": ["type", "evidence_ids", "description"],
            "additionalProperties": False}},
        "inferences": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "minLength": 1},
                "evidence_ids": {"type": "array", "minItems": 1,
                                 "items": {"type": "string", "minLength": 1}},
            },
            "required": ["text", "evidence_ids"],
            "additionalProperties": False}},
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["schema_version", "timeline", "correlations", "inferences",
                 "limitations"],
    "additionalProperties": False,
}


def timeline_response_format() -> dict:
    """OpenRouter structured-output request for phase3e/v1 outputs."""
    return {"type": "json_schema",
            "json_schema": {"name": "phase3e_timeline", "strict": True,
                            "schema": TIMELINE_JSON_SCHEMA}}


def _record_sources(record: dict) -> set:
    sources = set()
    if record.get("object_evidence"):
        sources.add("object")
    if record.get("generic_action_evidence"):
        sources.add("generic_action")
    if record.get("surveillance_event_evidence"):
        sources.add("surveillance_event")
    for hit in record.get("matched_hits", []) or []:
        if hit.get("matched_source") in ("object", "generic_action",
                                         "surveillance_event", "record"):
            sources.add(hit["matched_source"])
    return sources


def collect_evidence_index(result_3d: dict) -> dict:
    """Map every Phase 3D evidence_id to its video/incident/interval/sources."""
    index = {}
    for group in result_3d.get("merged_results", {}).get("groups", []) or []:
        for record in ((group.get("matched_evidence", []) or [])
                       + (group.get("contextual_evidence", []) or [])):
            index.setdefault(record["evidence_id"], {
                "evidence_id": record["evidence_id"],
                "video_id": record.get("video_id", ""),
                "incident_id": group.get("incident_id"),
                "start_time": record.get("start_time"),
                "end_time": record.get("end_time"),
                "sources": _record_sources(record)})
    for hit in result_3d.get("merged_results", {}).get("unmapped_hits", []) or []:
        index.setdefault(hit["evidence_id"], {
            "evidence_id": hit["evidence_id"],
            "video_id": hit.get("video_id", ""),
            "incident_id": None,
            "start_time": hit.get("start_time"),
            "end_time": hit.get("end_time"),
            "sources": {hit["matched_source"]} if hit.get("matched_source") else set()})
    return index


def _summarize_record(record: dict) -> dict:
    objects: dict = {}
    for det in record.get("object_evidence", []) or []:
        cls = str(det.get("class_name", ""))
        slot = objects.setdefault(cls, {"count": 0, "max_confidence": 0.0})
        slot["count"] += 1
        slot["max_confidence"] = max(slot["max_confidence"],
                                     float(det.get("confidence", 0.0)))
    summary = {"evidence_id": record.get("evidence_id", ""),
               "start_time": record.get("start_time"),
               "end_time": record.get("end_time"),
               "source_references": list(record.get("source_references", []) or []),
               "sources": {
                   "object": sorted(
                       [{"label": k, **v} for k, v in objects.items()],
                       key=lambda e: e["label"]),
                   "generic_action": sorted(
                       [{"label": str(o.get("label", "")),
                         "confidence": float(o.get("confidence", 0.0))}
                        for o in record.get("generic_action_evidence", []) or []],
                       key=lambda e: (-e["confidence"], e["label"])),
                   "surveillance_event": sorted(
                       [{"label": str(o.get("label", "")),
                         "confidence": float(o.get("confidence", 0.0))}
                        for o in record.get("surveillance_event_evidence", []) or []],
                       key=lambda e: (-e["confidence"], e["label"]))}}
    return summary


def serialize_for_llm(result_3d: dict) -> dict:
    """Deterministic compact Phase 3D representation for the LLM prompt."""
    groups = sorted(result_3d.get("merged_results", {}).get("groups", []) or [],
                    key=lambda g: (str(g.get("video_id", "")),
                                   float(g.get("incident_start_time") or 0),
                                   str(g.get("incident_id", ""))))
    incidents = []
    for group in groups:
        evidence = sorted(
            group.get("matched_evidence", []) + group.get("contextual_evidence", []),
            key=lambda r: (float(r.get("start_time", 0)),
                           str(r.get("evidence_id", ""))))
        matched_ids = {r["evidence_id"] for r in group.get("matched_evidence", []) or []}
        incidents.append({
            "incident_id": group.get("incident_id", ""),
            "video_id": group.get("video_id", ""),
            "start_time": group.get("incident_start_time"),
            "end_time": group.get("incident_end_time"),
            "event_hypotheses": list(group.get("event_hypotheses", []) or []),
            "evidence": [{**_summarize_record(r),
                          "matched": r["evidence_id"] in matched_ids}
                         for r in evidence]})
    return {"incidents": incidents,
            "unmapped_evidence_ids": sorted(
                {h["evidence_id"] for h in
                 result_3d.get("merged_results", {}).get("unmapped_hits", []) or []})}


def _check_ids(ids, index: dict, what: str) -> list:
    if not isinstance(ids, list) or not ids:
        raise TimelineValidationError(f"{what} evidence_ids must be non-empty")
    if any(not isinstance(e, str) or not e for e in ids):
        raise TimelineValidationError(f"{what} evidence_ids must be non-empty strings")
    if len(set(ids)) != len(ids):
        raise TimelineValidationError(f"{what} has duplicate evidence_ids")
    missing = [e for e in ids if e not in index]
    if missing:
        raise TimelineValidationError(f"{what} cites unknown evidence: {missing}")
    videos = {index[e]["video_id"] for e in ids}
    if len(videos) > 1:
        raise TimelineValidationError(
            f"{what} mixes videos {sorted(videos)}: cross-video correlation is not permitted")
    return [index[e] for e in ids]


def _check_range(start, end, entries: list, what: str) -> None:
    if not _is_number(start) or start < 0:
        raise TimelineValidationError(f"{what} start_time must be numeric and >= 0")
    if not _is_number(end) or end < start:
        raise TimelineValidationError(f"{what} requires end_time >= start_time")
    lo = min(float(e["start_time"]) for e in entries)
    hi = max(float(e["end_time"]) for e in entries)
    if not (float(start) >= lo and float(end) <= hi):
        raise TimelineValidationError(
            f"{what} range [{start}, {end}] extends outside referenced "
            f"evidence [{lo}, {hi}]")


def _check_relationship(corr_type: str, entries: list, index: dict, ids: list) -> None:
    starts = [float(e["start_time"]) for e in entries]
    ends = [float(e["end_time"]) for e in entries]
    if corr_type == "temporal_overlap":
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                if not (starts[i] <= ends[j] and starts[j] <= ends[i]):
                    raise TimelineValidationError(
                        f"temporal_overlap contradicted by {ids[i]} vs {ids[j]}")
    elif corr_type == "temporal_sequence":
        if not max(starts) > min(starts):
            raise TimelineValidationError(
                "temporal_sequence needs a chronological relationship")
    elif corr_type == "same_incident":
        incidents = {e["incident_id"] for e in entries}
        if len(incidents) != 1 or None in incidents:
            raise TimelineValidationError(
                "same_incident requires one shared Phase 2D incident")
    elif corr_type == "cross_source_support":
        sources = set().union(*[e["sources"] for e in entries]) - {"record"}
        if len(sources) < 2:
            raise TimelineValidationError(
                "cross_source_support needs >= 2 distinct source types")
    elif corr_type == "persistent_event":
        if len(entries) < 2 or any(
                not (e["sources"] & {"surveillance_event", "generic_action"})
                for e in entries):
            raise TimelineValidationError(
                "persistent_event needs >= 2 related event evidence records")
        ordered = sorted(zip(starts, ends))
        for (s0, e0), (s1, _e1) in zip(ordered, ordered[1:]):
            if s1 - e0 > ADJACENCY_GAP_SECONDS:
                raise TimelineValidationError(
                    "persistent_event windows are not adjacent or nearby")


def parse_and_validate_timeline(text: str, evidence_index: dict) -> dict:
    """Parse model text as JSON and validate the phase3e/v1 output."""
    if text is None or not str(text).strip():
        raise TimelineValidationError("empty model response")
    try:
        output = json.loads(_strip_fences(str(text)))
    except ValueError as exc:
        raise TimelineValidationError(f"output is not valid JSON: {exc}") from exc
    if not isinstance(output, dict):
        raise TimelineValidationError("output must be a JSON object")
    allowed = {"schema_version", "timeline", "correlations", "inferences", "limitations"}
    unknown = set(output) - allowed
    if unknown:
        raise TimelineValidationError(f"unknown output fields: {sorted(unknown)}")
    if output.get("schema_version") != SCHEMA_VERSION:
        raise TimelineValidationError("schema_version must be 'phase3e/v1'")
    for field in ("timeline", "correlations", "inferences", "limitations"):
        if not isinstance(output.get(field), list):
            raise TimelineValidationError(f"{field} must be an array")
        if field == "limitations" and any(not isinstance(e, str) for e in output[field]):
            raise TimelineValidationError("limitations must be strings")

    timeline = []
    for pos, item in enumerate(output["timeline"]):
        what = f"timeline[{pos}]"
        if not isinstance(item, dict) or set(item) - {
                "start_time", "end_time", "evidence_ids", "observation"}:
            raise TimelineValidationError(f"{what} has an invalid structure")
        entries = _check_ids(item.get("evidence_ids"), evidence_index, what)
        _check_range(item.get("start_time"), item.get("end_time"), entries, what)
        obs = item.get("observation")
        if (not isinstance(obs, dict) or set(obs) - {"text", "evidence_ids"}
                or not isinstance(obs.get("text"), str) or not obs["text"].strip()):
            raise TimelineValidationError(f"{what} needs a non-empty observation")
        obs_entries = _check_ids(obs.get("evidence_ids"), evidence_index,
                                 f"{what} observation")
        if not set(obs["evidence_ids"]).issubset(set(item["evidence_ids"])):
            raise TimelineValidationError(
                f"{what} observation cites evidence outside the item")
        _ = obs_entries
        timeline.append({"start_time": item["start_time"], "end_time": item["end_time"],
                         "evidence_ids": list(item["evidence_ids"]),
                         "observation": {"text": obs["text"].strip(),
                                         "evidence_ids": list(obs["evidence_ids"])}})

    correlations = []
    for pos, item in enumerate(output["correlations"]):
        what = f"correlations[{pos}]"
        if not isinstance(item, dict) or set(item) - {
                "type", "evidence_ids", "description"}:
            raise TimelineValidationError(f"{what} has an invalid structure")
        if item.get("type") not in CORRELATION_TYPES:
            raise TimelineValidationError(f"{what} has unknown type: {item.get('type')!r}")
        entries = _check_ids(item.get("evidence_ids"), evidence_index, what)
        if not isinstance(item.get("description"), str) or not item["description"].strip():
            raise TimelineValidationError(f"{what} needs a non-empty description")
        _check_relationship(item["type"], entries, evidence_index, item["evidence_ids"])
        correlations.append({"type": item["type"],
                             "evidence_ids": list(item["evidence_ids"]),
                             "description": item["description"].strip()})

    inferences = []
    for pos, item in enumerate(output["inferences"]):
        what = f"inferences[{pos}]"
        if not isinstance(item, dict) or set(item) - {"text", "evidence_ids"}:
            raise TimelineValidationError(f"{what} has an invalid structure")
        _check_ids(item.get("evidence_ids"), evidence_index, what)
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            raise TimelineValidationError(f"{what} needs non-empty text")
        inferences.append({"text": item["text"].strip(),
                           "evidence_ids": list(item["evidence_ids"])})

    return {"schema_version": SCHEMA_VERSION, "timeline": timeline,
            "correlations": correlations, "inferences": inferences,
            "limitations": list(output["limitations"])}


def run_timeline(client, result_3d: dict, investigator_question: str = "",
                 temperature: float = 0.0) -> dict:
    """Reason over a Phase 3D result with the LLM; validate the timeline."""
    if not isinstance(result_3d, dict) or result_3d.get("schema_version") != EXPECTED_3D_SCHEMA:
        raise TimelineValidationError("input must be a validated phase3d/v1 result")
    index = collect_evidence_index(result_3d)
    if not index:
        return {"schema_version": SCHEMA_VERSION, "timeline": [], "correlations": [],
                "inferences": [],
                "limitations": ["No retrieved evidence was supplied, so no timeline "
                                "or correlations could be constructed."]}
    serialized = serialize_for_llm(result_3d)
    user_message = "Retrieved evidence (JSON):\n" + json.dumps(serialized, indent=2)
    if investigator_question and investigator_question.strip():
        user_message += ("\nInvestigator question (context only, not evidence): "
                         + investigator_question.strip())
    raw = client.generate_structured(SYSTEM_PROMPT, user_message,
                                     temperature=temperature,
                                     response_format=timeline_response_format(),
                                     max_tokens=MAX_TOKENS)
    return parse_and_validate_timeline(raw, index)


def _mock_response_for(result_3d: dict) -> str:
    groups = sorted(result_3d.get("merged_results", {}).get("groups", []) or [],
                    key=lambda g: (float(g.get("incident_start_time") or 0),
                                   str(g.get("incident_id", ""))))
    if not groups:
        return json.dumps({"schema_version": SCHEMA_VERSION, "timeline": [],
                           "correlations": [], "inferences": [],
                           "limitations": ["No incident groups in the input."]})
    group = groups[0]
    records = sorted(group.get("matched_evidence", []) or [],
                     key=lambda r: (float(r.get("start_time", 0)),
                                    str(r.get("evidence_id", ""))))
    if not records:
        records = sorted(group.get("contextual_evidence", []) or [],
                         key=lambda r: (float(r.get("start_time", 0)),
                                        str(r.get("evidence_id", ""))))
    pick = records[:2]
    ids = [r["evidence_id"] for r in pick]
    lo, hi = min(float(r["start_time"]) for r in pick), max(float(r["end_time"]) for r in pick)
    return json.dumps({
        "schema_version": SCHEMA_VERSION,
        "timeline": [{"start_time": lo, "end_time": hi, "evidence_ids": ids,
                      "observation": {"text": "The evidence indicates activity "
                                              "across adjacent windows.",
                                      "evidence_ids": ids}}],
        "correlations": ([{"type": "same_incident", "evidence_ids": ids,
                           "description": "The records belong to the same "
                                          "Phase 2D incident."}] if len(ids) > 1 else []),
        "inferences": [{"text": "The available evidence suggests persistent "
                                "activity during this interval.",
                        "evidence_ids": ids}],
        "limitations": ["Surveillance-event labels are model hypotheses, not "
                        "independently verified facts."]})


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3E: timeline/correlation agent")
    parser.add_argument("--input", required=True, help="phase3d/v1 result JSON file")
    parser.add_argument("--question", default="")
    parser.add_argument("--model", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--mock", action="store_true",
                        help="offline mode: deterministic mock LLM, no API key needed")
    args = parser.parse_args(argv)

    try:
        with Path(args.input).open("r", encoding="utf-8") as fh:
            result_3d = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"timeline error: bad input file: {exc}")
        return 2

    try:
        if args.mock:
            output = run_timeline(MockLLMClient(_mock_response_for(result_3d)),
                                  result_3d, args.question)
        else:
            from src.agents.query_planner import create_client, load_llm_settings

            settings = load_llm_settings()
            if args.model:
                settings["model"] = args.model
            output = run_timeline(create_client(settings), result_3d, args.question,
                                  settings.get("temperature", 0.0))
    except (TimelineValidationError, LLMError) as exc:
        print(f"timeline error: {exc}")
        return 2

    print(json.dumps(output, indent=2))
    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2)
        print(f"Wrote timeline -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
