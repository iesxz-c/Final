"""Phase 3F - Verification + Report Agent (LLM drafts, Python validates).

Verifies Phase 3E claims against the Phase 3D evidence and produces an
investigator-facing report from verified information only. The LLM
receives 3E claims plus the underlying 3D evidence; it never retrieves,
never sees footage, and never invents. Python validation is fail-closed:
unknown fields, ungrounded IDs/timestamps, forbidden identity/causality
language, and unsupported findings are rejected, never repaired.

Usage:
    python -m src.agents.verification_report --input3e phase3e.json --input3d phase3d.json
    python -m src.agents.verification_report --input3e phase3e.json --input3d phase3d.json --mock
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from src.agents.llm_client import LLMError, MockLLMClient
from src.agents.timeline_correlation import collect_evidence_index, serialize_for_llm

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SCHEMA_VERSION = "phase3f/v1"
EXPECTED_3E_SCHEMA = "phase3e/v1"
EXPECTED_3D_SCHEMA = "phase3d/v1"

#: Report output is verification + prose; 6000 tokens fits the full
#: Shooting001-scale report inside the affordable OpenRouter balance.
REPORT_MAX_TOKENS = 6000

STATUSES = ("supported", "partially_supported", "unsupported")

#: Conservative denylist for identity/causality language in report prose.
#: The model is instructed to avoid these; Python rejects them regardless.
FORBIDDEN_PHRASES = ("suspect", "perpetrator", "victim", "offender",
                      "definitely occurred", "this proves", "proves that",
                      "caused", "led to", "guilty", "proves")

SYSTEM_PROMPT = """You are the Verification and Report Agent in a CCTV investigation system.

You receive claims produced by a Timeline Agent together with the underlying retrieved evidence.

You do not have access to CCTV footage. You do not retrieve evidence.

Your two tasks:
1. VERIFY each listed claim against the supplied evidence, judging it supported, partially_supported, or unsupported.
2. PRODUCE an investigator-facing report using only verified or appropriately qualified information.

Verification rules:
- A claim is supported only when the supplied evidence directly supports it.
- A claim is partially_supported when some factual components hold but the full claim is too strong or contains an unsupported interpretation. Qualify such findings in the report.
- A claim is unsupported when the evidence does not support it. Unsupported claims must NOT appear as factual findings.
- Verify every listed claim_id exactly once. Do not add, drop, or rename claims.
- Every verification entry must cite the supporting evidence IDs, unless the claim is unsupported by anything.

Grounding rules:
- Cite only evidence IDs present in the input. Never invent evidence IDs, timestamps, video IDs, detections, or confidence values.
- Keep every timestamp inside the time range of the cited evidence.
- Model crime/event labels are hypotheses, never confirmed crimes.

Language rules:
- Do not describe anyone as suspect, perpetrator, victim, or offender unless explicitly established by the evidence.
- Do not claim this proves, definitely occurred, intentional actions, causality, guilt, or identity unless directly established.
- Prefer: "The evidence indicates...", "The retrieved evidence supports...", "The surveillance-event model produced a ... hypothesis.", "The available evidence is consistent with...", "The evidence does not establish...".

Report rules:
- Title, summary, timeline, findings, limitations. Concise and investigator-oriented.
- Every finding and timeline item must cite evidence IDs. Unsupported claims stay out of findings.
- Reflect the verification results; do not merely copy the Timeline Agent output.
- If evidence is insufficient, say so in limitations rather than guessing.

The output MUST contain exactly these three top-level keys: schema_version, verification, report. Do not add any other key.

Return only the required JSON structure."""


class ReportValidationError(ValueError):
    """A model-produced report failed structural validation."""


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


#: JSON Schema for strict structured output. Python validation is authoritative.
REPORT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "enum": [SCHEMA_VERSION]},
        "verification": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "claim_id": {"type": "string", "minLength": 1},
                "claim": {"type": "string", "minLength": 1},
                "status": {"type": "string", "enum": list(STATUSES)},
                "evidence_ids": {"type": "array",
                                 "items": {"type": "string", "minLength": 1}},
                "reason": {"type": "string", "minLength": 1},
            },
            "required": ["claim_id", "claim", "status", "evidence_ids", "reason"],
            "additionalProperties": False}},
        "report": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 1},
                "summary": {"type": "string", "minLength": 1},
                "timeline": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "start_time": {"type": "number"},
                        "end_time": {"type": "number"},
                        "description": {"type": "string", "minLength": 1},
                        "evidence_ids": {"type": "array", "minItems": 1,
                                         "items": {"type": "string", "minLength": 1}},
                    },
                    "required": ["start_time", "end_time", "description",
                                 "evidence_ids"],
                    "additionalProperties": False}},
                "findings": {"type": "array", "items": {
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
            "required": ["title", "summary", "timeline", "findings", "limitations"],
            "additionalProperties": False},
    },
    "required": ["schema_version", "verification", "report"],
    "additionalProperties": False,
}


def report_response_format() -> dict:
    """OpenRouter structured-output request for phase3f/v1 outputs."""
    return {"type": "json_schema",
            "json_schema": {"name": "phase3f_report", "strict": True,
                            "schema": REPORT_JSON_SCHEMA}}


def derive_claims(result_3e: dict) -> list:
    """Deterministic claim set from 3E: observations, correlations, inferences."""
    claims = []
    for pos, item in enumerate(result_3e.get("timeline", []) or []):
        obs = item.get("observation", {}) or {}
        claims.append({"claim_id": f"claim_{len(claims) + 1:03d}",
                       "kind": "timeline_observation",
                       "text": obs.get("text", ""),
                       "evidence_ids": list(obs.get("evidence_ids", []) or []),
                       "_pos": pos})
    for pos, item in enumerate(result_3e.get("correlations", []) or []):
        claims.append({"claim_id": f"claim_{len(claims) + 1:03d}",
                       "kind": "correlation",
                       "text": f"{item.get('type', '')}: {item.get('description', '')}",
                       "evidence_ids": list(item.get("evidence_ids", []) or []),
                       "_pos": pos})
    for pos, item in enumerate(result_3e.get("inferences", []) or []):
        claims.append({"claim_id": f"claim_{len(claims) + 1:03d}",
                       "kind": "inference",
                       "text": item.get("text", ""),
                       "evidence_ids": list(item.get("evidence_ids", []) or []),
                       "_pos": pos})
    return claims


def _check_ids(ids, index: dict, what: str, allow_empty: bool = False) -> list:
    if not isinstance(ids, list) or (not ids and not allow_empty):
        raise ReportValidationError(f"{what} needs a non-empty evidence list")
    if any(not isinstance(e, str) or not e for e in ids):
        raise ReportValidationError(f"{what} evidence IDs must be non-empty strings")
    if len(set(ids)) != len(ids):
        raise ReportValidationError(f"{what} has duplicate evidence IDs")
    missing = [e for e in ids if e not in index]
    if missing:
        raise ReportValidationError(f"{what} cites unknown evidence: {missing}")
    videos = {index[e]["video_id"] for e in ids}
    if len(videos) > 1:
        raise ReportValidationError(f"{what} mixes videos {sorted(videos)}")
    return [index[e] for e in ids]


def _check_prose(text: str, what: str) -> str:
    lowered = text.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in lowered:
            raise ReportValidationError(
                f"{what} contains unsupported language: {phrase!r}")
    return text


def parse_and_validate_report(text: str, evidence_index: dict,
                              expected_claim_ids: list) -> dict:
    """Parse model text as JSON and validate the phase3f/v1 output."""
    if text is None or not str(text).strip():
        raise ReportValidationError("empty model response")
    try:
        output = json.loads(_strip_fences(str(text)))
    except ValueError as exc:
        raise ReportValidationError(f"output is not valid JSON: {exc}") from exc
    if not isinstance(output, dict):
        raise ReportValidationError("output must be a JSON object")
    if set(output) != {"schema_version", "verification", "report"}:
        raise ReportValidationError(
            f"top level must be exactly schema_version/verification/report, "
            f"got {sorted(output)}")
    if output.get("schema_version") != SCHEMA_VERSION:
        raise ReportValidationError("schema_version must be 'phase3f/v1'")
    if not isinstance(output.get("verification"), list):
        raise ReportValidationError("verification must be an array")

    seen: dict = {}
    verification = []
    for pos, item in enumerate(output["verification"]):
        what = f"verification[{pos}]"
        if not isinstance(item, dict) or set(item) != {
                "claim_id", "claim", "status", "evidence_ids", "reason"}:
            raise ReportValidationError(f"{what} has an invalid structure")
        claim_id = item["claim_id"]
        if not isinstance(claim_id, str) or not claim_id:
            raise ReportValidationError(f"{what} needs a claim_id")
        if claim_id in seen:
            raise ReportValidationError(f"duplicate claim_id: {claim_id}")
        if claim_id not in expected_claim_ids:
            raise ReportValidationError(f"unknown claim_id: {claim_id}")
        if not isinstance(item.get("claim"), str) or not item["claim"].strip():
            raise ReportValidationError(f"{what} needs a non-empty claim")
        if item.get("status") not in STATUSES:
            raise ReportValidationError(f"{what} has illegal status: {item.get('status')!r}")
        allow_empty = item["status"] == "unsupported"
        _check_ids(item.get("evidence_ids"), evidence_index, what,
                   allow_empty=allow_empty)
        if not isinstance(item.get("reason"), str) or not item["reason"].strip():
            raise ReportValidationError(f"{what} needs a non-empty reason")
        seen[claim_id] = item
        verification.append({"claim_id": claim_id, "claim": item["claim"].strip(),
                             "status": item["status"],
                             "evidence_ids": list(item["evidence_ids"]),
                             "reason": item["reason"].strip()})
    missing = [c for c in expected_claim_ids if c not in seen]
    if missing:
        raise ReportValidationError(f"unverified claims: {missing}")

    report = output.get("report")
    if not isinstance(report, dict) or set(report) != {
            "title", "summary", "timeline", "findings", "limitations"}:
        raise ReportValidationError("report has an invalid structure")
    if not isinstance(report.get("title"), str) or not report["title"].strip():
        raise ReportValidationError("report needs a non-empty title")
    if not isinstance(report.get("summary"), str) or not report["summary"].strip():
        raise ReportValidationError("report needs a non-empty summary")
    _check_prose(report["title"], "report title")
    _check_prose(report["summary"], "report summary")
    if not isinstance(report.get("timeline"), list) or not isinstance(
            report.get("findings"), list) or not isinstance(
            report.get("limitations"), list):
        raise ReportValidationError("report timeline/findings/limitations must be arrays")
    if any(not isinstance(e, str) for e in report["limitations"]):
        raise ReportValidationError("limitations must be strings")

    unsupported_texts = {re.sub(r"\s+", " ", v["claim"]).strip().lower()
                         for v in verification if v["status"] == "unsupported"}
    timeline = []
    for pos, item in enumerate(report["timeline"]):
        what = f"report timeline[{pos}]"
        if not isinstance(item, dict) or set(item) != {
                "start_time", "end_time", "description", "evidence_ids"}:
            raise ReportValidationError(f"{what} has an invalid structure")
        entries = _check_ids(item.get("evidence_ids"), evidence_index, what)
        if not _is_number(item.get("start_time")) or item["start_time"] < 0:
            raise ReportValidationError(f"{what} start_time must be numeric and >= 0")
        if not _is_number(item.get("end_time")) or item["end_time"] < item["start_time"]:
            raise ReportValidationError(f"{what} requires end_time >= start_time")
        lo = min(float(e["start_time"]) for e in entries)
        hi = max(float(e["end_time"]) for e in entries)
        if not (float(item["start_time"]) >= lo and float(item["end_time"]) <= hi):
            raise ReportValidationError(
                f"{what} range extends outside referenced evidence [{lo}, {hi}]")
        if not isinstance(item.get("description"), str) or not item["description"].strip():
            raise ReportValidationError(f"{what} needs a non-empty description")
        _check_prose(item["description"], what)
        timeline.append({"start_time": item["start_time"], "end_time": item["end_time"],
                         "description": item["description"].strip(),
                         "evidence_ids": list(item["evidence_ids"])})

    findings = []
    for pos, item in enumerate(report["findings"]):
        what = f"report findings[{pos}]"
        if not isinstance(item, dict) or set(item) != {"text", "evidence_ids"}:
            raise ReportValidationError(f"{what} has an invalid structure")
        _check_ids(item.get("evidence_ids"), evidence_index, what)
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ReportValidationError(f"{what} needs non-empty text")
        _check_prose(item["text"], what)
        normalized = re.sub(r"\s+", " ", item["text"]).strip().lower()
        if normalized in unsupported_texts:
            raise ReportValidationError(
                f"{what} restates an unsupported claim as a finding")
        findings.append({"text": item["text"].strip(),
                         "evidence_ids": list(item["evidence_ids"])})

    return {"schema_version": SCHEMA_VERSION, "verification": verification,
            "report": {"title": report["title"].strip(),
                       "summary": report["summary"].strip(),
                       "timeline": timeline, "findings": findings,
                       "limitations": list(report["limitations"])}}


def run_verification_report(client, result_3e: dict, result_3d: dict,
                            investigator_question: str = "",
                            temperature: float = 0.0,
                            max_tokens: int = REPORT_MAX_TOKENS) -> dict:
    """Verify 3E claims against 3D evidence; report verified info only."""
    if not isinstance(result_3e, dict) or result_3e.get("schema_version") != "phase3e/v1":
        raise ReportValidationError("input 3E must be a validated phase3e/v1 result")
    if not isinstance(result_3d, dict) or result_3d.get("schema_version") != "phase3d/v1":
        raise ReportValidationError("input 3D must be a validated phase3d/v1 result")
    index = collect_evidence_index(result_3d)
    claims = [{k: v for k, v in c.items() if not k.startswith("_")}
              for c in derive_claims(result_3e)]
    if not claims or not index:
        return {"schema_version": SCHEMA_VERSION, "verification": [],
                "report": {"title": "No verifiable claims",
                           "summary": "The supplied analysis contained no claims "
                                      "groundable in retrieved evidence.",
                           "timeline": [], "findings": [],
                           "limitations": ["No retrieved evidence was available "
                                           "for verification."]}}
    user_message = {
        "investigator_question": investigator_question.strip(),
        "claims_to_verify": claims,
        "prior_limitations": list(result_3e.get("limitations", []) or []),
        "evidence": serialize_for_llm(result_3d),
    }
    raw = client.generate_structured(SYSTEM_PROMPT, json.dumps(user_message, indent=2),
                                     temperature=temperature,
                                     response_format=report_response_format(),
                                     max_tokens=max_tokens)
    return parse_and_validate_report(raw, index, [c["claim_id"] for c in claims])


def _mock_response_for(claims: list, index: dict) -> str:
    supported = [c for c in claims if c["evidence_ids"] and all(
        e in index for e in c["evidence_ids"])]
    verification = [
        {"claim_id": c["claim_id"], "claim": c["text"] or "(empty)",
         "status": "supported" if c in supported else "unsupported",
         "evidence_ids": [e for e in c["evidence_ids"] if e in index],
         "reason": "The mock evidence directly supports the claim."
                   if c in supported else "No supplied evidence supports the claim."}
        for c in claims]
    first = supported[0] if supported else None
    if first is not None:
        entries = [index[e] for e in first["evidence_ids"]]
        lo, hi = min(float(e["start_time"]) for e in entries), max(
            float(e["end_time"]) for e in entries)
        timeline = [{"start_time": lo, "end_time": hi,
                     "description": "The evidence indicates activity in this interval.",
                     "evidence_ids": list(first["evidence_ids"])}]
        findings = [{"text": "The retrieved evidence supports the verified claim.",
                     "evidence_ids": list(first["evidence_ids"])}]
    else:
        timeline, findings = [], []
    return json.dumps({"schema_version": SCHEMA_VERSION, "verification": verification,
                       "report": {"title": "Mock verification report",
                                  "summary": "The evidence indicates the verified claims.",
                                  "timeline": timeline, "findings": findings,
                                  "limitations": ["Model labels are hypotheses."]}})


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3F: verification + report agent")
    parser.add_argument("--input3e", required=True)
    parser.add_argument("--input3d", required=True)
    parser.add_argument("--question", default="")
    parser.add_argument("--model", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--mock", action="store_true",
                        help="offline mode: deterministic mock LLM, no API key needed")
    args = parser.parse_args(argv)

    try:
        with Path(args.input3e).open("r", encoding="utf-8") as fh:
            result_3e = json.load(fh)
        with Path(args.input3d).open("r", encoding="utf-8") as fh:
            result_3d = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"report error: bad input file: {exc}")
        return 2

    try:
        if args.mock:
            claims = [{k: v for k, v in c.items() if not k.startswith("_")}
                      for c in derive_claims(result_3e)]
            index = collect_evidence_index(result_3d)
            if not claims or not index:
                output = run_verification_report(MockLLMClient("{}"), result_3e, result_3d,
                                                 args.question)
            else:
                raw = _mock_response_for(
                    [{k: v for k, v in c.items() if not k.startswith("_")}
                     for c in claims], index)
                output = parse_and_validate_report(
                    raw, index, [c["claim_id"] for c in claims])
        else:
            from src.agents.query_planner import create_client, load_llm_settings

            settings = load_llm_settings()
            if args.model:
                settings["model"] = args.model
            output = run_verification_report(create_client(settings), result_3e,
                                             result_3d, args.question,
                                             settings.get("temperature", 0.0))
    except (ReportValidationError, LLMError) as exc:
        print(f"report error: {exc}")
        return 2

    print(json.dumps(output, indent=2))
    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2)
        print(f"Wrote report -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
