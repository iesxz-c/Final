"""Phase 3C - Query Planning Agent (first LLM-enabled phase).

Converts an investigator's natural-language question into a validated
structured JSON retrieval plan. The LLM never sees evidence and must not
invent it; Python validates the plan before acceptance. Retrieval itself
is executed deterministically by later phases, never inside the planner.

Usage:
    python -m src.agents.query_planner --query "What happened around the fighting incident?"
    python -m src.agents.query_planner --query "Find fighting" --mock
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from src.agents.llm_client import (
    DEFAULT_MODEL,
    LLMError,
    MetaDirectClient,
    MockLLMClient,
)
from src.env_file import load_env_file

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SCHEMA_VERSION = "phase3c/v1"
MAX_CONTEXT_SECONDS = 300.0

#: Output cap for planner calls: comfortably fits a plan JSON while
#: staying inside modest per-call token budgets.
PLAN_MAX_TOKENS = 2048

INTENTS = ("search_evidence", "investigate_incident", "find_person",
           "find_object", "find_event", "compare_events", "unknown")
SOURCES = ("object", "generic_action", "surveillance_event", "record")

MODEL_ENV = "CCTV_LLM_MODEL"
PROVIDER_ENV = "CCTV_LLM_PROVIDER"

SYSTEM_PROMPT = """You are a query planning component for a CCTV investigation system.

Your task is to translate an investigator's natural-language question into a structured retrieval plan.

You do not have access to CCTV footage.
You do not have access to evidence.
You must not claim that an event occurred.
You must not invent timestamps, evidence IDs, detections, confidence values, or incident IDs.
You only specify what evidence should be searched for.

Return only the requested JSON structure.

Controlled intents (use exactly one): search_evidence, investigate_incident, find_person, find_object, find_event, compare_events, unknown.

Supported sources (use exactly one per query, or null for no filter): object, generic_action, surveillance_event, record.

Required JSON structure:
{
  "schema_version": "phase3c/v1",
  "intent": "<one controlled intent>",
  "queries": [{"query": "<non-empty search phrase>", "source": "<supported source or null>"}],
  "video_id": null,
  "start_time": null,
  "end_time": null,
  "temporal_context_seconds": 0,
  "needs_timeline": false,
  "needs_cross_evidence": false
}

Rules: queries must be non-empty; video_id only when explicitly mentioned; start_time/end_time only when explicitly stated (seconds, non-negative, end >= start); temporal_context_seconds between 0 and 300; booleans must be booleans.

Output contract (any violation causes rejection, so follow it exactly):
- queries MUST be a non-empty array.
- EVERY queries[] item MUST contain a "query" key whose value is a non-empty string.
- The query string MUST be an actual searchable phrase derived from the investigator's question (for example "fighting" or "person").
- Never output an empty string for query. Do not output null for query. Do not output whitespace-only text for query.
- Output EXACTLY the JSON object above and nothing else: no Markdown, no code fences, no preamble, no commentary, no trailing prose."""


#: JSON Schema describing phase3c/v1 for the Meta Responses `text.format`
#: structured-output parameter. It mirrors the INTENTS/SOURCES vocabularies
#: and the numeric ranges, but Python validation in parse_and_validate_plan()
#: remains authoritative: the schema cannot express blank-string, end>=start,
#: or unknown-field rejection.
PLAN_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "schema_version": {"type": "string", "enum": [SCHEMA_VERSION]},
        "intent": {"type": "string", "enum": list(INTENTS)},
        "queries": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "minLength": 1},
                    "source": {"type": ["string", "null"],
                               "enum": [*SOURCES, None]},
                },
                "required": ["query", "source"],
                "additionalProperties": False,
            },
        },
        "video_id": {"type": ["string", "null"]},
        "start_time": {"type": ["number", "null"], "minimum": 0},
        "end_time": {"type": ["number", "null"], "minimum": 0},
        "temporal_context_seconds": {"type": "number", "minimum": 0,
                                     "maximum": MAX_CONTEXT_SECONDS},
        "needs_timeline": {"type": "boolean"},
        "needs_cross_evidence": {"type": "boolean"},
    },
    "required": ["schema_version", "intent", "queries", "video_id",
                 "start_time", "end_time", "temporal_context_seconds",
                 "needs_timeline", "needs_cross_evidence"],
    "additionalProperties": False,
}


def plan_response_format() -> dict:
    """Structured-output request for phase3c/v1 plans (Meta text.format)."""
    return {"type": "json_schema",
            "json_schema": {"name": "phase3c_plan", "strict": True,
                            "schema": PLAN_JSON_SCHEMA}}


class PlanValidationError(ValueError):
    """A model-produced plan failed structural validation."""


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def parse_and_validate_plan(text: str) -> dict:
    """Parse model text as JSON and validate the phase3c/v1 plan schema."""
    if text is None or not str(text).strip():
        raise PlanValidationError("empty model response")
    try:
        plan = json.loads(_strip_fences(str(text)))
    except ValueError as exc:
        raise PlanValidationError(f"plan is not valid JSON: {exc}") from exc
    if not isinstance(plan, dict):
        raise PlanValidationError("plan must be a JSON object")
    allowed = {"schema_version", "intent", "queries", "video_id", "start_time",
               "end_time", "temporal_context_seconds", "needs_timeline",
               "needs_cross_evidence"}
    unknown = set(plan) - allowed
    if unknown:
        raise PlanValidationError(f"unknown plan fields: {sorted(unknown)}")
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise PlanValidationError("plan schema_version must be 'phase3c/v1'")
    if plan.get("intent") not in INTENTS:
        raise PlanValidationError(f"unknown intent: {plan.get('intent')!r}")
    queries = plan.get("queries")
    if not isinstance(queries, list) or not queries:
        raise PlanValidationError("queries must be a non-empty list")
    clean_queries = []
    for item in queries:
        if not isinstance(item, dict) or set(item) - {"query", "source"}:
            raise PlanValidationError("each query must be {query, source}")
        phrase = item.get("query")
        if not isinstance(phrase, str) or not phrase.strip():
            raise PlanValidationError("query phrases must be non-empty strings")
        source = item.get("source")
        if source is not None and source not in SOURCES:
            raise PlanValidationError(f"unsupported source: {source!r}")
        clean_queries.append({"query": phrase.strip(), "source": source})
    video_id = plan.get("video_id")
    if video_id is not None and (not isinstance(video_id, str) or not video_id.strip()):
        raise PlanValidationError("video_id must be null or a non-empty string")
    for field in ("start_time", "end_time"):
        value = plan.get(field)
        if value is not None and (not _is_number(value) or value < 0):
            raise PlanValidationError(f"{field} must be null or >= 0")
    start, end = plan.get("start_time"), plan.get("end_time")
    if start is not None and end is not None and end < start:
        raise PlanValidationError("end_time must be >= start_time")
    context = plan.get("temporal_context_seconds", 0)
    if not _is_number(context) or context < 0 or context > MAX_CONTEXT_SECONDS:
        raise PlanValidationError(
            f"temporal_context_seconds must be within [0, {MAX_CONTEXT_SECONDS:g}]")
    for field in ("needs_timeline", "needs_cross_evidence"):
        if type(plan.get(field)) is not bool:
            raise PlanValidationError(f"{field} must be a boolean")
    return {"schema_version": SCHEMA_VERSION, "intent": plan["intent"],
            "queries": clean_queries,
            "video_id": video_id.strip() if video_id is not None else None,
            "start_time": start, "end_time": end,
            "temporal_context_seconds": context,
            "needs_timeline": plan["needs_timeline"],
            "needs_cross_evidence": plan["needs_cross_evidence"]}


def plan_query(client, investigator_query: str,
               temperature: float = 0.0) -> dict:
    """Run the planner: LLM proposes, Python validates. Returns the plan."""
    if not investigator_query or not investigator_query.strip():
        raise PlanValidationError("investigator query must be non-empty")
    raw = client.generate_structured(SYSTEM_PROMPT, investigator_query.strip(),
                                     temperature=temperature,
                                     response_format=plan_response_format(),
                                     max_tokens=PLAN_MAX_TOKENS)
    return parse_and_validate_plan(raw)


def load_llm_settings(config_path: str | os.PathLike | None = None) -> dict:
    """Read llm.{provider,model,temperature} without touching other config."""
    load_env_file()  # repo-root .env fills gaps only; real env always wins
    from src.settings import load_config

    try:
        config = load_config(config_path)
    except Exception:
        config = {}
    llm = (config.get("llm") or {}) if isinstance(config, dict) else {}
    return {"provider": os.environ.get(PROVIDER_ENV) or llm.get("provider") or "meta",
            "model": os.environ.get(MODEL_ENV) or llm.get("model") or DEFAULT_MODEL,
            "temperature": float(llm.get("temperature", 0.0) or 0.0)}


def create_client(settings: dict | None = None,
                  config_path: str | os.PathLike | None = None,
                  api_key: str | None = None):
    """Build the configured LLM client (Meta Model API DIRECT only).

    The project is frozen to a single model: any explicitly configured
    model other than DEFAULT_MODEL fails closed instead of routing
    elsewhere.
    """
    settings = settings or load_llm_settings(config_path)
    provider = (settings.get("provider") or "meta").lower()
    if provider == "openrouter":
        raise LLMError("OpenRouter is retired; the sole provider is Meta Model API DIRECT")
    if provider != "meta":
        raise LLMError(f"unsupported LLM provider: {provider!r}")
    model = settings.get("model") or DEFAULT_MODEL
    if model != DEFAULT_MODEL:
        raise LLMError(f"only {DEFAULT_MODEL} is supported; got {model!r}")
    return MetaDirectClient(api_key=api_key, model=DEFAULT_MODEL,
                            temperature=settings.get("temperature", 0.0))


def _mock_response(investigator_query: str) -> str:
    return json.dumps({"schema_version": SCHEMA_VERSION, "intent": "search_evidence",
                       "queries": [{"query": investigator_query.strip(), "source": None}],
                       "video_id": None, "start_time": None, "end_time": None,
                       "temporal_context_seconds": 0, "needs_timeline": False,
                       "needs_cross_evidence": False})


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3C: query planning agent")
    parser.add_argument("--query", required=True)
    parser.add_argument("--config", default=None)
    parser.add_argument("--model", default=None,
                        help="must be muse-spark-1.3-contributor; anything else fails closed")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--mock", action="store_true",
                        help="offline mode: deterministic mock LLM, no API key needed")
    args = parser.parse_args(argv)

    print(f"planner request: {args.query!r}")
    try:
        if args.mock:
            plan = plan_query(MockLLMClient(_mock_response(args.query)), args.query)
        else:
            settings = load_llm_settings(args.config)
            if args.model:
                settings["model"] = args.model
            temperature = settings["temperature"] if args.temperature is None else args.temperature
            plan = plan_query(create_client(settings), args.query, temperature)
    except (PlanValidationError, LLMError) as exc:
        print(f"planner error: {exc}")
        return 2

    print("validated plan:")
    print(json.dumps(plan, indent=2))
    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as fh:
            json.dump(plan, fh, indent=2)
        print(f"Wrote plan -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
