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
import math
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.pipeline import retrieve_evidence as R
from src.pipeline.prepare_judgments import parse_rule

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


#: Rule field -> Phase 3A source restriction. Mirrors production, where the
#: planner emits source-typed queries: an object-label term searches object
#: hits only, so it cannot match video_ids or unrelated label kinds.
FIELD_SOURCES = {
    "object_evidence class names": ("object",),
    "generic_action_evidence labels": ("generic_action",),
    "surveillance_event_evidence labels": ("surveillance_event",),
}


def build_lexical_queries(relevance_rule: str) -> dict:
    """Derive lexical content terms from a structured relevance rule.

    Returns {"operator": SINGLE|AND|OR,
             "terms": [(text, sources), ...],
             "window": (lo, hi) | None}. Temporal atoms become filter
    windows, never lexical text. No synonyms or expansions are invented;
    unknown structures raise instead of guessing.
    """
    parsed = parse_rule(relevance_rule)
    terms, lo, hi = [], None, None
    for term in parsed["terms"]:
        if term["kind"] == "label":
            field = term["field"]
            if field not in FIELD_SOURCES:
                raise ValueError(f"no lexical source for field: {field!r}")
            terms.append((term["label"], FIELD_SOURCES[field]))
        elif term["kind"] == "overlap":
            lo = term["lo"] if lo is None else max(lo, term["lo"])
            hi = term["hi"] if hi is None else min(hi, term["hi"])
        elif term["kind"] == "end_after":
            lo = term["lo"] if lo is None else max(lo, term["lo"])
        else:  # pragma: no cover - parse_rule already rejects these
            raise ValueError(f"unsupported term kind: {term['kind']!r}")
    window = (lo, hi) if lo is not None or hi is not None else None
    if window is not None and lo is not None and hi is not None and lo > hi:
        window = "empty"
    return {"operator": parsed["operator"], "terms": terms, "window": window}


def hybrid_search_for_judgment(records: list, entry: dict, retriever,
                               top_k: int = 10, constant: int = 60) -> list:
    """Hybrid baseline: frozen lexical + frozen vector fused with RRF.

    Both branches run with their existing representations and scope
    behavior (lexical rule-driven, vector verbatim). Branch rankings are
    full (no truncation) so fusion sees every in-scope candidate; only
    the fused list is cut to top_k. RRF constant is the documented
    default; never tuned here. Scope comes from the entry, never from
    relevance     judgments.
    """
    lexical = lexical_search_for_judgment(records, entry, top_k=None)
    vector = vector_search_for_judgment(records, entry, retriever, top_k=None)
    fused = rrf_fuse([lexical, vector], constant=constant)
    return [RetrievalResult(evidence_id=h.evidence_id, rank=pos,
                            score=h.score, retrieval_method="hybrid")
            for pos, h in enumerate(fused[:max(0, top_k)], 1)]


def vector_search_for_judgment(records: list, entry: dict, retriever,
                               top_k: int = 10) -> list:
    """Vector baseline for one benchmark judgment (evaluation adapter).

    The ORIGINAL query text goes to the encoder verbatim. The collection
    is searched globally; the entry scope (video/time) then filters the
    ranking with order preserved, mirroring lexical scope filtering.
    Filtering uses scope fields only, never relevance judgments.
    """
    scope = entry.get("scope") or {}
    start, end = scope.get("start_time"), scope.get("end_time")
    ranked = retriever.search(entry.get("query", ""), top_k=len(records))
    by_id = {r.get("evidence_id"): r for r in records}
    kept = []
    for hit in ranked:
        record = by_id.get(hit.evidence_id)
        if record is None:
            continue
        if scope.get("video_id") is not None \
                and record.get("video_id") != scope.get("video_id"):
            continue
        if start is not None and float(record.get("end_time", 0)) < start:
            continue
        if end is not None and float(record.get("start_time", 0)) > end:
            continue
        kept.append(hit)
        if top_k is not None and len(kept) >= max(0, top_k):
            break
    return [RetrievalResult(evidence_id=h.evidence_id, rank=pos,
                            score=h.score, retrieval_method=h.retrieval_method)
            for pos, h in enumerate(kept, 1)]


def lexical_search_for_judgment(records: list, entry: dict,
                                top_k: int = 10) -> list:
    """Lexical baseline for one benchmark judgment (evaluation adapter).

    Content terms come from the judgment's relevance_rule; the entry scope
    (video/time) is preserved as a filter. AND intersects per-term hit
    sets (ordered by summed rank, then evidence_id); OR/SINGLE unions them
    (ordered by best rank, then evidence_id). Temporal-only rules carry no
    lexical text, so they deterministically return [] — substring
    retrieval cannot express time, and no ranking is invented for it.
    """
    spec = build_lexical_queries(entry.get("relevance_rule", ""))
    scope = entry.get("scope") or {}
    start = scope.get("start_time")
    end = scope.get("end_time")
    window = spec["window"]
    if window == "empty":
        return []
    if window is not None:
        start = max([s for s in (start, window[0]) if s is not None],
                    default=None)
        end = min([e for e in (end, window[1]) if e is not None], default=None)
        if start is not None and end is not None and start > end:
            return []
    if not spec["terms"]:
        return []
    per_term = []
    for text, sources in spec["terms"]:
        hits = R.retrieve(records, text, video_id=scope.get("video_id"),
                          start_time=start, end_time=end, sources=list(sources),
                          limit=None)
        per_term.append({h["evidence_id"]: (pos, float(h["confidence"]))
                         for pos, h in enumerate(hits)})
    if spec["operator"] == "AND":
        common = set(per_term[0])
        for table in per_term[1:]:
            common &= set(table)
        scored = [(sum(table[e][0] for table in per_term),
                   max(table[e][1] for table in per_term), e) for e in common]
    else:
        best: dict = {}
        for table in per_term:
            for e, (pos, conf) in table.items():
                if e not in best or pos < best[e][0]:
                    best[e] = (pos, conf)
        scored = [(pos, conf, e) for e, (pos, conf) in best.items()]
    scored.sort(key=lambda t: (t[0], t[2]))
    ranked = [RetrievalResult(evidence_id=e, rank=pos, score=conf,
                              retrieval_method="lexical")
              for pos, (_, conf, e) in enumerate(scored, 1)]
    return ranked if top_k is None else ranked[:max(0, top_k)]


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
    parser.add_argument("--method", default="lexical",
                        choices=("lexical", "vector", "hybrid"),
                        help="retrieval method (default: lexical)")
    parser.add_argument("--vector-store", default=None,
                        help="Qdrant local path (vector method only)")
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
        print("lexical and vector adapters ready. "
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
    with Path(args.benchmark).open("r", encoding="utf-8") as fh:
        raw_entries = {q.get("query_id"): q
                       for q in json.load(fh).get("queries", [])}
    entries = [{"query_id": j.query_id,
                "query": j.query,
                "scope": (raw_entries.get(j.query_id) or {}).get("scope") or {},
                "relevance_rule": (raw_entries.get(j.query_id) or {}).get(
                    "relevance_rule", "")}
               for j in judgments]
    try:
        latencies: dict = {}
        if args.method in ("vector", "hybrid"):
            from src.pipeline.vector_store import QdrantVectorRetriever

            store = Path(args.vector_store) if args.vector_store else \
                PROJECT_ROOT / "data/vector_155"
            retriever = QdrantVectorRetriever(store)
            try:
                results = {}
                for e in entries:
                    start = time.perf_counter()
                    if args.method == "hybrid":
                        hits = hybrid_search_for_judgment(records, e, retriever,
                                                          top_k=args.top_k)
                    else:
                        hits = vector_search_for_judgment(records, e, retriever,
                                                          top_k=args.top_k)
                    latencies[e["query_id"]] = round(time.perf_counter() - start, 3)
                    results[e["query_id"]] = [h.evidence_id for h in hits]
            finally:
                retriever.close()
        else:
            results = {}
            for e in entries:
                start = time.perf_counter()
                hits = lexical_search_for_judgment(records, e, top_k=args.top_k)
                latencies[e["query_id"]] = round(time.perf_counter() - start, 3)
                results[e["query_id"]] = [h.evidence_id for h in hits]
    except ValueError as exc:
        print(f"retrieval eval error: {exc}")
        return 2
    metrics = evaluate_benchmark(results, judgments)
    metrics["method"] = args.method
    metrics["latency_seconds"] = {
        "per_query": dict(sorted(latencies.items())),
        "mean": round(statistics.mean(latencies.values()), 3) if latencies else 0.0,
        "median": round(statistics.median(latencies.values()), 3) if latencies else 0.0,
        "p95": round(sorted(latencies.values())[
            max(0, math.ceil(0.95 * len(latencies)) - 1)], 3) if latencies else 0.0,
        "n": len(latencies),
    }
    print(json.dumps(metrics["aggregate"], indent=2, sort_keys=True))
    if args.output:
        with Path(args.output).open("w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2, sort_keys=True)
        print(f"Wrote metrics -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
