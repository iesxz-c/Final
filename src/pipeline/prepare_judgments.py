"""Read-only benchmark judgment assistant (deterministic rule application).

For one benchmark query, mechanically applies its frozen relevance_rule
to every fused record inside its scope and prints the candidate IDs.

This is NOT retrieval, NOT ranking, NOT interpretation: the rule text
was authored by a human, and this tool only checks stored record fields
against it. Unknown rule structures fail closed instead of guessing.

Never writes the benchmark, never fills relevant_evidence_ids, never
calls retrieval/LLM/embeddings, never uses confidence or folder labels.

Usage:
    python -m src.pipeline.prepare_judgments --query-id Q01
    python -m src.pipeline.prepare_judgments --query-id Q01 --json
    python -m src.pipeline.prepare_judgments --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.pipeline.annotate_retrieval import scope_records

DEFAULT_BENCHMARK = "eval/retrieval_benchmark_v1.json"
DEFAULT_EVIDENCE = "data/data_155n/fused_155/evidence.json"

_LABEL_ATOM = re.compile(
    r"'(?P<label>.+?)' is present in "
    r"(?P<field>object_evidence class names|generic_action_evidence labels|"
    r"surveillance_event_evidence labels)")
_OVERLAP_ATOM = re.compile(
    r"(?:the evidence interval )?overlaps \[(?P<lo>[\d.]+),\s*(?P<hi>[\d.]+)\]"
    r"(?: seconds)?")
_END_AFTER_ATOM = re.compile(r"end_time >= (?P<lo>[\d.]+)")


def _labels(record: dict, field: str) -> set:
    if field == "object_evidence class names":
        return {str(d.get("class_name", "")) for d in
                record.get("object_evidence", []) or [] if d.get("class_name")}
    key = ("generic_action_evidence" if field.startswith("generic_action")
           else "surveillance_event_evidence")
    return {str(e.get("label", "")) for e in record.get(key, []) or []
            if e.get("label")}


_BARE_LABEL = re.compile(r"'(?P<label>.+?)'")


def _eval_atom(atom: str, record: dict, default_field: str | None = None) -> bool:
    """Evaluate one atomic condition against stored fields (pure)."""
    atom = atom.strip()
    match = _LABEL_ATOM.fullmatch(atom)
    if match:
        return match.group("label") in _labels(record, match.group("field"))
    if default_field is not None:
        bare = _BARE_LABEL.fullmatch(atom)
        if bare:
            return bare.group("label") in _labels(record, default_field)
    match = _OVERLAP_ATOM.fullmatch(atom)
    if match:
        lo, hi = float(match.group("lo")), float(match.group("hi"))
        return float(record.get("start_time", 0)) <= hi \
            and float(record.get("end_time", 0)) >= lo
    match = _END_AFTER_ATOM.fullmatch(atom)
    if match:
        return float(record.get("end_time", 0)) >= float(match.group("lo"))
    raise ValueError(f"unsupported rule atom (refusing to guess): {atom!r}")


def _split_top(rule: str) -> tuple:
    """Split a rule body into (operator, atoms); fail closed on mixing."""
    if " OR " in rule and " AND " in rule:
        raise ValueError("mixed AND/OR rules are not supported")
    if " OR " in rule:
        return "OR", [a.strip() for a in rule.split(" OR ")]
    if " AND " in rule:
        return "AND", [a.strip() for a in rule.split(" AND ")]
    return "SINGLE", [rule.strip()]


def rule_matches(relevance_rule: str, record: dict) -> bool:
    """Apply a frozen benchmark rule to one record (pure, deterministic)."""
    body = relevance_rule.strip()
    prefix = "relevant iff "
    if not body.startswith(prefix):
        raise ValueError(f"rule must start with {prefix!r}")
    operator, atoms = _split_top(body[len(prefix):])
    if operator == "OR":
        # Elided form "'A' OR 'B' is present in F": bare labels inherit the
        # single field used by the complete siblings. Complete atoms may use
        # different fields (e.g. event OR action); bare labels with no
        # field to inherit, or conflicting inheritances, fail closed.
        fields = set()
        for atom in atoms:
            match = _LABEL_ATOM.fullmatch(atom.strip())
            if match:
                fields.add(match.group("field"))
        bare = [a for a in atoms if _BARE_LABEL.fullmatch(a.strip())
                and not _LABEL_ATOM.fullmatch(a.strip())]
        if bare and len(fields) != 1:
            raise ValueError("bare OR label with no unique field to inherit")
        default = next(iter(fields), None)
        results = [_eval_atom(atom, record, default) for atom in atoms]
        return any(results)
    results = [_eval_atom(atom, record) for atom in atoms]
    return all(results)


def candidates_for(entry: dict, records: list) -> list:
    """Evidence IDs in scope satisfying the entry's rule, scope-ordered."""
    scope = entry.get("scope") or {}
    scoped = scope_records(records, scope.get("video_id"),
                           scope.get("start_time"), scope.get("end_time"))
    rule = entry.get("relevance_rule", "")
    if not isinstance(rule, str) or not rule.strip():
        raise ValueError(f"query {entry.get('query_id')!r} has no relevance_rule")
    return [r["evidence_id"] for r in scoped if rule_matches(rule, r)]


def _load_entries(benchmark_path: Path) -> list:
    with Path(benchmark_path).open("r", encoding="utf-8") as fh:
        return json.load(fh).get("queries", [])


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only judgment assistant")
    parser.add_argument("--benchmark", default=None)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--query-id", default=None)
    parser.add_argument("--all", action="store_true",
                        help="candidate counts for every query")
    parser.add_argument("--json", action="store_true",
                        help="machine-readable output")
    args = parser.parse_args(argv)

    benchmark = Path(args.benchmark) if args.benchmark else PROJECT_ROOT / DEFAULT_BENCHMARK
    evidence_path = Path(args.evidence) if args.evidence else PROJECT_ROOT / DEFAULT_EVIDENCE
    try:
        entries = _load_entries(benchmark)
        with evidence_path.open("r", encoding="utf-8") as fh:
            records = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"judgment error: bad input: {exc}")
        return 2

    if args.query_id is not None:
        matches = [q for q in entries if q.get("query_id") == args.query_id]
        if not matches:
            print(f"judgment error: unknown query_id: {args.query_id}")
            return 2
        entries = matches
    elif not args.all:
        print("judgment error: provide --query-id or --all")
        return 2

    payload = []
    for entry in entries:
        try:
            candidates = candidates_for(entry, records)
        except ValueError as exc:
            print(f"judgment error: {exc}")
            return 2
        scope = entry.get("scope") or {}
        payload.append({"query_id": entry.get("query_id"),
                        "query": entry.get("query"),
                        "relevance_rule": entry.get("relevance_rule"),
                        "scope": scope,
                        "candidate_count": len(candidates),
                        "candidate_evidence_ids": candidates})
    if args.json:
        print(json.dumps(payload if len(payload) != 1 else payload[0], indent=2))
        return 0
    for item in payload:
        print(f"query_id: {item['query_id']}")
        print(f"query: {item['query']}")
        print(f"rule: {item['relevance_rule']}")
        print(f"scope: {item['scope']}")
        print(f"candidate_count: {item['candidate_count']}")
        for eid in item["candidate_evidence_ids"]:
            print(f"  {eid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
