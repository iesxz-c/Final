"""Retrieval evaluation infrastructure (lexical / vector / hybrid).

Evaluates ranked evidence-ID retrieval against a manually authored
benchmark of relevance judgments. Pure functions only; no models, no LLM,
no vector database here.

SAFETY AGAINST CIRCULAR EVALUATION (binding rule for all future use):

Relevance judgments must be authored independently from retrieval
outputs. This module must never:
- generate relevance judgments from retrieved results,
- use model predictions as relevance ground truth,
- use LLM answers as ground truth,
- select ground truth based on which method retrieved an item.

Judgments describe which stored evidence a human considers relevant to a
query. Retrieval methods are scored against those judgments, never the
reverse.

Usage:
    python -m src.pipeline.retrieval_eval --help
    python -m src.pipeline.retrieval_eval --benchmark eval/retrieval_benchmark_v1.json \\
        --evidence data/data_155n/fused_155/evidence.json --output /tmp/lexical.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.pipeline import retrieve_evidence as R

SCHEMA_VERSION = "retrieval_eval/v1"
BENCHMARK_VERSION = "retrieval_eval/v1"


@dataclass(frozen=True)
class Judgment:
    """One manually authored relevance judgment (NOT generated)."""

    query_id: str
    query: str
    relevant_evidence_ids: tuple
    empty_intended: bool = False


@dataclass(frozen=True)
class RetrievalResult:
    """One ranked retrieval hit (minimal fields; no record duplication)."""

    evidence_id: str
    rank: int
    score: float
    retrieval_method: str


def _ordered_unique(values: list) -> list:
    seen, out = set(), []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def build_record_text(record: dict) -> str:
    """Deterministic searchable text for one fused evidence record.

    Uses only information already stored in the record: video_id, YOLO
    object class names, generic-action labels (+ top-k), surveillance-event
    labels (+ top-k), and source references. No ground-truth labels, no
    inferred crime names, no LLM text, no identities, no causality.
    """
    tokens: list = []

    def _add(value) -> None:
        text = str(value).strip()
        if text:
            tokens.append(text)

    _add(record.get("video_id", ""))
    for det in record.get("object_evidence", []) or []:
        _add(det.get("class_name", ""))
    for key in ("generic_action_evidence", "surveillance_event_evidence"):
        for entry in record.get(key, []) or []:
            _add(entry.get("label", ""))
            for top in entry.get("top_k", []) or []:
                _add(top.get("label", ""))
    for ref in record.get("source_references", []) or []:
        _add(ref)
    return " ".join(_ordered_unique(tokens))


def _dedup_ids(retrieved_ids: list) -> list:
    return _ordered_unique([str(v) for v in retrieved_ids])


def recall_at_k(retrieved_ids: list, relevant_ids: list, k: int) -> float | None:
    """Relevant-in-top-K / total-relevant.

    Empty relevance set -> None (undefined; never manufactured). Callers
    must exclude None from macro averages and report the n used.
    """
    relevant = set(str(v) for v in relevant_ids)
    if not relevant:
        return None
    top = set(_dedup_ids(retrieved_ids)[:max(0, k)])
    return len(top & relevant) / len(relevant)


def mrr(retrieved_ids: list, relevant_ids: list) -> float | None:
    """1 / rank of the first relevant result; 0.0 when none is retrieved.

    Empty relevance set -> None (undefined; never manufactured).
    """
    relevant = set(str(v) for v in relevant_ids)
    if not relevant:
        return None
    for rank, evidence_id in enumerate(_dedup_ids(retrieved_ids), 1):
        if evidence_id in relevant:
            return 1.0 / rank
    return 0.0


def evaluate_query(retrieved_ids: list, relevant_ids: list) -> dict:
    """Per-query Recall@5, Recall@10, MRR (None where undefined)."""
    return {"recall@5": recall_at_k(retrieved_ids, relevant_ids, 5),
            "recall@10": recall_at_k(retrieved_ids, relevant_ids, 10),
            "mrr": mrr(retrieved_ids, relevant_ids)}


def _mean(values: list) -> float | None:
    return sum(values) / len(values) if values else None


def evaluate_benchmark(results: dict, judgments: list) -> dict:
    """Score every judgment; macro-average over defined values only."""
    per_query = {}
    for judgment in judgments:
        retrieved = results.get(judgment.query_id, [])
        per_query[judgment.query_id] = evaluate_query(retrieved,
                                                      list(judgment.relevant_evidence_ids))
    aggregate = {}
    for metric in ("recall@5", "recall@10", "mrr"):
        defined = [s[metric] for s in per_query.values() if s[metric] is not None]
        aggregate[metric] = {"value": _mean(defined), "n": len(defined),
                             "n_queries": len(per_query)}
    return {"schema_version": SCHEMA_VERSION, "per_query": per_query,
            "aggregate": aggregate}


def lexical_search(records: list, query: str, top_k: int = 10,
                   video_id: str | None = None,
                   start_time: float | None = None,
                   end_time: float | None = None,
                   sources: list | tuple | None = None) -> list:
    """Thin evaluation adapter over the frozen Phase 3A implementation.

    Matching/ranking semantics belong to retrieve_evidence.retrieve and
    are NOT reimplemented here. Hit confidence becomes the result score.
    """
    hits = R.retrieve(records, query, video_id=video_id, start_time=start_time,
                      end_time=end_time, sources=sources, limit=top_k)
    return [RetrievalResult(evidence_id=h["evidence_id"], rank=pos,
                            score=float(h["confidence"]), retrieval_method="lexical")
            for pos, h in enumerate(hits, 1)]


class VectorRetriever(Protocol):
    """Pluggable vector backend (embeddings + index arrive later).

    A future implementation (e.g. Qdrant) must implement search() with
    this exact signature; metric code stays unchanged.
    """

    def search(self, query: str, top_k: int = 10) -> list:
        """Return up to top_k RetrievalResults ranked best-first."""
        ...  # pragma: no cover - interface only


def rrf_fuse(ranked_lists: list, constant: int = 60) -> list:
    """Deterministic reciprocal-rank fusion baseline (NOT a final algorithm).

    score(e) = sum over lists of 1 / (constant + rank(e)). Ties break by
    evidence_id ascending, so output order is fully deterministic. No LLM,
    no learned weights. Ranks are reassigned 1..N on the fused list.
    """
    totals: dict = {}
    for results in ranked_lists:
        for item in results:
            totals[item.evidence_id] = totals.get(item.evidence_id, 0.0) \
                + 1.0 / (constant + max(1, int(item.rank)))
    ordered = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    return [RetrievalResult(evidence_id=eid, rank=pos, score=score,
                            retrieval_method="hybrid-rrf")
            for pos, (eid, score) in enumerate(ordered, 1)]


def load_benchmark(path: str | Path, corpus_ids: set | None = None) -> list:
    """Load and validate a retrieval benchmark file (no judgments created)."""
    with Path(path).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or data.get("schema_version") != BENCHMARK_VERSION:
        raise ValueError(f"benchmark schema_version must be {BENCHMARK_VERSION!r}")
    queries = data.get("queries")
    if not isinstance(queries, list) or not queries:
        raise ValueError("benchmark needs a non-empty queries list")
    seen, judgments = set(), []
    for i, entry in enumerate(queries):
        if not isinstance(entry, dict):
            raise ValueError(f"query {i} must be an object")
        qid = entry.get("query_id")
        if not isinstance(qid, str) or not qid.strip():
            raise ValueError(f"query {i} needs a non-empty query_id")
        if qid in seen:
            raise ValueError(f"duplicate query_id: {qid!r}")
        seen.add(qid)
        if not isinstance(entry.get("query"), str) or not entry["query"].strip():
            raise ValueError(f"query {qid!r} needs non-empty query text")
        relevant = entry.get("relevant_evidence_ids")
        if not isinstance(relevant, list):
            raise ValueError(f"query {qid!r} needs a relevant_evidence_ids list")
        if any(not isinstance(v, str) for v in relevant):
            raise ValueError(f"query {qid!r} relevant IDs must be strings")
        if len(set(relevant)) != len(relevant):
            raise ValueError(f"query {qid!r} has duplicate relevant IDs")
        empty_intended = entry.get("empty_relevance_intended", False)
        if not relevant and empty_intended is not True:
            raise ValueError(
                f"query {qid!r} has an empty relevance list and is not marked "
                f"empty_relevance_intended=true; the benchmark is incomplete")
        if corpus_ids is not None:
            unknown = [v for v in relevant if v not in corpus_ids]
            if unknown:
                raise ValueError(f"query {qid!r} cites unknown evidence IDs: "
                                 f"{unknown[:5]}")
        judgments.append(Judgment(query_id=qid, query=entry["query"].strip(),
                                  relevant_evidence_ids=tuple(relevant),
                                  empty_intended=empty_intended is True))
    return judgments


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Retrieval evaluation (lexical-ready)")
    parser.add_argument("--benchmark", default=None,
                        help="benchmark JSON with human-authored judgments")
    parser.add_argument("--evidence", default=None,
                        help="fused evidence.json corpus")
    parser.add_argument("--output", default=None, help="write metrics JSON to PATH")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--record-text", default=None,
                        help="print deterministic search text for one evidence_id")
    args = parser.parse_args(argv)

    evidence_path = Path(args.evidence) if args.evidence else None
    records = None
    if evidence_path is not None:
        try:
            records = R.load_evidence(evidence_path)
        except (OSError, ValueError) as exc:
            print(f"retrieval eval error: bad evidence: {exc}")
            return 2

    if args.record_text is not None:
        if records is None:
            print("retrieval eval error: --record-text needs --evidence")
            return 2
        matches = [r for r in records if r.get("evidence_id") == args.record_text]
        if not matches:
            print(f"retrieval eval error: unknown evidence_id: {args.record_text}")
            return 2
        print(build_record_text(matches[0]))
        return 0

    if args.benchmark is None:
        print("lexical adapter ready; vector backend not built yet. "
              "Supply --benchmark with authored judgments to evaluate.")
        return 0
    try:
        judgments = load_benchmark(
            args.benchmark,
            {r.get("evidence_id") for r in records} if records is not None else None)
    except (OSError, ValueError) as exc:
        print(f"retrieval eval error: bad benchmark: {exc}")
        return 2
    if records is None:
        print("retrieval eval error: --benchmark needs --evidence")
        return 2
    results = {j.query_id: [h.evidence_id for h in
                            lexical_search(records, j.query, top_k=args.top_k)]
               for j in judgments}
    metrics = evaluate_benchmark(results, judgments)
    metrics["method"] = "lexical"
    print(json.dumps(metrics["aggregate"], indent=2, sort_keys=True))
    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2, sort_keys=True)
        print(f"Wrote metrics -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
