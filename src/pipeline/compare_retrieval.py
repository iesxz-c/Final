"""Phase 5A.4 - Frozen lexical-vs-vector comparison (analysis only).

Reads the two frozen result files plus the benchmark, verifies they are
comparable (same queries, same positive/empty partition, same judgments),
and writes a comparison artifact plus a human-readable markdown report.
No retriever, benchmark, judgment, or metric is modified here. Per-query
'winner' fields are descriptive only (higher measured value per metric);
no overall winner, ranking, score, or recommendation is produced.

Usage:
    python -m src.pipeline.compare_retrieval
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

LEXICAL_PATH = "eval/results_lexical_v2.json"
VECTOR_PATH = "eval/results_vector_v1.json"
BENCHMARK_PATH = "eval/retrieval_benchmark_v1.json"
OUTPUT_JSON = "eval/results_retrieval_comparison_v1.json"
OUTPUT_MD = "eval/results_retrieval_comparison_v1.md"

METRICS = ("recall@5", "recall@10", "mrr")

EXPECTED_LEXICAL = {"recall@5": 0.4315, "recall@10": 0.6045, "mrr": 0.8182}
EXPECTED_VECTOR = {"recall@5": 0.4743, "recall@10": 0.6917, "mrr": 0.8565}


def _load(path: Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def verify_comparable(lexical: dict, vector: dict, benchmark: dict) -> dict:
    """Check both results cover the same queries/judgments (pure)."""
    lex_q = set(lexical.get("per_query", {}))
    vec_q = set(vector.get("per_query", {}))
    bench_q = {q.get("query_id") for q in benchmark.get("queries", [])}
    if not (lex_q == vec_q == bench_q):
        raise ValueError("query sets differ between inputs")
    lex_pos = {q for q, s in lexical["per_query"].items()
               if s.get("recall@5") is not None}
    vec_pos = {q for q, s in vector["per_query"].items()
               if s.get("recall@5") is not None}
    if lex_pos != vec_pos:
        raise ValueError("positive-query partitions differ")
    return {"queries": len(bench_q), "positive": len(lex_pos),
            "empty": len(bench_q) - len(lex_pos)}


def _winner(lexical_value, vector_value) -> str:
    if lexical_value is None or vector_value is None:
        return "n/a"
    if abs(vector_value - lexical_value) < 1e-12:
        return "tie"
    return "vector" if vector_value > lexical_value else "lexical"


def compare(lexical: dict, vector: dict) -> dict:
    """Per-query metric pairs plus descriptive per-metric winners (pure)."""
    per_query = {}
    for qid in sorted(lexical["per_query"]):
        entry = {"lexical": lexical["per_query"][qid],
                 "vector": vector["per_query"][qid], "winner": {}}
        for metric in METRICS:
            entry["winner"][metric] = _winner(
                lexical["per_query"][qid].get(metric),
                vector["per_query"][qid].get(metric))
        per_query[qid] = entry
    differences = {}
    for metric in METRICS:
        lex_val = lexical["aggregate"][metric]["value"]
        vec_val = vector["aggregate"][metric]["value"]
        differences[metric] = round(vec_val - lex_val, 4)
    return {"per_query": per_query, "vector_minus_lexical": differences}


def build_artifact(lexical: dict, vector: dict, benchmark: dict,
                   lexical_latency: dict | None = None) -> dict:
    """Assemble the comparison artifact (pure)."""
    comparability = verify_comparable(lexical, vector, benchmark)
    comparison = compare(lexical, vector)
    return {
        "schema_version": "retrieval-comparison/v1",
        "corpus": {"evidence": "data/data_155n/fused_155/evidence.json",
                   "records": 7927, "videos": 155},
        "benchmark": {"file": BENCHMARK_PATH,
                      "queries": comparability["queries"],
                      "positive_queries": comparability["positive"],
                      "empty_queries": comparability["empty"],
                      "relevance_judgments": sum(
                          len(q.get("relevant_evidence_ids", []))
                          for q in benchmark.get("queries", []))},
        "lexical": {"source": LEXICAL_PATH,
                    "aggregate": lexical["aggregate"]},
        "vector": {"source": VECTOR_PATH,
                   "aggregate": vector["aggregate"]},
        "vector_minus_lexical": comparison["vector_minus_lexical"],
        "per_query": comparison["per_query"],
        "latency_seconds": {
            "lexical": lexical_latency or lexical.get("latency_seconds"),
            "vector": vector.get("latency_seconds")},
        "empty_query_handling": "queries with empty relevance sets are null "
                                "in both result files and excluded from all "
                                "aggregates (n=22 of 30)",
        "temporal_scope_note": "temporal-only queries succeed via the shared "
                               "evaluation scope filter, not via semantic "
                               "temporal understanding",
        "scope": "descriptive comparison only; no overall winner is computed",
    }


def verify_expected(artifact: dict) -> list:
    """Check frozen aggregate values to 4dp; return discrepancy strings."""
    problems = []
    for name, expected in (("lexical", EXPECTED_LEXICAL),
                           ("vector", EXPECTED_VECTOR)):
        for metric, value in expected.items():
            actual = round(artifact[name]["aggregate"][metric]["value"], 4)
            if actual != value:
                problems.append(f"{name} {metric}: expected {value}, got {actual}")
    return problems


def render_markdown(artifact: dict) -> str:
    """Human-readable neutral report (pure)."""
    lines = ["# Lexical vs Vector Retrieval Comparison (v1)", ""]
    lines.append("## A. Experimental setup")
    lines.append(f"- Corpus: {artifact['corpus']['records']} fused records, "
                 f"{artifact['corpus']['videos']} videos "
                 f"({artifact['corpus']['evidence']})")
    lines.append(f"- Benchmark: {artifact['benchmark']['file']} — "
                 f"{artifact['benchmark']['queries']} queries, "
                 f"{artifact['benchmark']['positive_queries']} positive, "
                 f"{artifact['benchmark']['empty_queries']} intentionally empty, "
                 f"{artifact['benchmark']['relevance_judgments']} frozen judgments")
    lines.append("- Lexical: frozen Phase 3A substring retrieval via rule-derived "
                 "terms (results_lexical_v2.json)")
    lines.append("- Vector: all-MiniLM-L6-v2 + local Qdrant cosine, verbatim "
                 "queries (results_vector_v1.json)")
    lines.append("- Empty-relevance queries are null in both files and excluded "
                 "from aggregates (n=22).")
    lines.append("")
    lines.append("## B. Aggregate results")
    for metric in METRICS:
        lex_val = artifact["lexical"]["aggregate"][metric]["value"]
        vec_val = artifact["vector"]["aggregate"][metric]["value"]
        diff = artifact["vector_minus_lexical"][metric]
        lines.append(f"- {metric}: lexical {lex_val:.4f}, vector {vec_val:.4f} "
                     f"(vector-minus-lexical {diff:+.4f})")
    lines.append("")
    lines.append("## C. Per-query comparison")
    lines.append("| query | lexical R@5/R@10/MRR | vector R@5/R@10/MRR | "
                 "higher per metric (R@5/R@10/MRR) |")
    lines.append("|---|---|---|---|")
    fmt = lambda s, m: "null" if s.get(m) is None else f"{s[m]:.3f}"
    for qid, entry in artifact["per_query"].items():
        lex, vec, win = entry["lexical"], entry["vector"], entry["winner"]
        lines.append(f"| {qid} | {fmt(lex, 'recall@5')}/{fmt(lex, 'recall@10')}/"
                     f"{fmt(lex, 'mrr')} | {fmt(vec, 'recall@5')}/"
                     f"{fmt(vec, 'recall@10')}/{fmt(vec, 'mrr')} | "
                     f"{win['recall@5']}/{win['recall@10']}/{win['mrr']} |")
    lines.append("")
    lines.append("## D. Latency comparison")
    for name in ("lexical", "vector"):
        lat = artifact["latency_seconds"].get(name) or {}
        lines.append(f"- {name}: mean {lat.get('mean')}s, median "
                     f"{lat.get('median')}s, P95 {lat.get('p95')}s "
                     f"(n={lat.get('n')})")
    lines.append("")
    lines.append("## E. Observed complementary behavior")
    lines.append("- Lexical retrieval is strong on exact stored labels: every "
                 "content-bearing query returns a relevant record first "
                 "(lexical MRR 0.8182), reflecting deterministic exact-match "
                 "priority rather than semantic understanding.")
    lines.append("- Vector retrieval can recover semantically related evidence "
                 "where wording differs from stored labels (e.g. the Q27 "
                 "disjunction reaches R@10 1.000 where lexical substring "
                 "matching is exact-only).")
    lines.append("- Temporal-only success on both sides can involve the explicit "
                 "evaluation scope filter rather than semantic temporal "
                 "understanding.")
    lines.append("")
    lines.append("## F. Limitations")
    lines.append("- Single 155-video corpus; 22 scored queries; no significance "
                 "testing.")
    lines.append("- Recall@K is the more discriminating retrieval measure here; "
                 "MRR saturates because exact matches rank first.")
    lines.append("- Lexical temporal-only queries score 0.000 by construction "
                 "(substring retrieval cannot express time).")
    lines.append("- Vector truncation at top-10 with scope filtering mirrors, "
                 "but does not replicate, production retrieval conditions.")
    return "\n".join(lines) + "\n"


def build_hybrid_artifact(lexical: dict, vector: dict, hybrid: dict,
                          benchmark: dict) -> dict:
    """Three-method comparison artifact (pure, descriptive only)."""
    methods = {"lexical": lexical, "vector": vector, "hybrid": hybrid}
    base = set(methods["lexical"].get("per_query", {}))
    for name, results in methods.items():
        if set(results.get("per_query", {})) != base:
            raise ValueError(f"query set mismatch in {name}")
    bench_q = {q.get("query_id") for q in benchmark.get("queries", [])}
    if base != bench_q:
        raise ValueError("result queries differ from benchmark")
    null_sets = [{q for q, s in m["per_query"].items() if s.get("recall@5") is None}
                 for m in methods.values()]
    if not (null_sets[0] == null_sets[1] == null_sets[2]):
        raise ValueError("empty-query partitions differ")
    per_query = {}
    for qid in sorted(base):
        entry = {name: methods[name]["per_query"][qid] for name in methods}
        entry["descriptive"] = {
            metric: max(methods, key=lambda n: (
                methods[n]["per_query"][qid].get(metric) is not None,
                methods[n]["per_query"][qid].get(metric) or -1.0))
            if any(methods[n]["per_query"][qid].get(metric) is not None
                   for n in methods) else "n/a"
            for metric in METRICS}
        per_query[qid] = entry
    pairs = {}
    for first, second in (("lexical", "vector"), ("lexical", "hybrid"),
                          ("vector", "hybrid")):
        pairs[f"{second}_minus_{first}"] = {
            metric: round(methods[second]["aggregate"][metric]["value"]
                          - methods[first]["aggregate"][metric]["value"], 4)
            for metric in METRICS}
    differences = pairs
    return {
        "schema_version": "retrieval-comparison/v1",
        "corpus": {"evidence": "data/data_155n/fused_155/evidence.json",
                   "records": 7927, "videos": 155},
        "benchmark": {"file": BENCHMARK_PATH,
                      "queries": len(base),
                      "positive_queries": len(base) - len(null_sets[0]),
                      "empty_queries": len(null_sets[0])},
        "fusion": {"formula": "score = sum(1 / (constant + rank))",
                   "constant": 60, "method": "hybrid-rrf",
                   "note": "documented default constant; never tuned"},
        "aggregates": {name: methods[name]["aggregate"] for name in methods},
        "pairwise_differences": differences,
        "per_query": per_query,
        "latency_seconds": {name: methods[name].get("latency_seconds")
                            for name in methods},
        "empty_query_handling": "null in all three files; excluded (n=22 of 30)",
        "scope": "descriptive comparison only; no overall winner is computed",
    }


def render_hybrid_markdown(artifact: dict) -> str:
    """Neutral three-method report (pure)."""
    lines = ["# Lexical vs Vector vs Hybrid Retrieval Comparison (v1)", ""]
    lines.append("## Setup")
    lines.append(f"- Corpus: {artifact['corpus']['records']} fused records, "
                 f"{artifact['corpus']['videos']} videos")
    lines.append(f"- Benchmark: {artifact['benchmark']['queries']} queries, "
                 f"{artifact['benchmark']['positive_queries']} positive, "
                 f"{artifact['benchmark']['empty_queries']} intentionally empty")
    lines.append("- Lexical: frozen Phase 3A substring via rule-derived terms")
    lines.append("- Vector: all-MiniLM-L6-v2 + local Qdrant cosine, verbatim queries")
    f = artifact["fusion"]
    lines.append(f"- Hybrid: RRF ({f['formula']}, constant={f['constant']}); {f['note']}")
    lines.append("")
    lines.append("## Aggregates (n=22)")
    for name in ("lexical", "vector", "hybrid"):
        agg = artifact["aggregates"][name]
        lines.append(f"- {name}: " + ", ".join(
            f"{m} {agg[m]['value']:.4f}" for m in METRICS))
    lines.append("")
    lines.append("## Pairwise absolute differences")
    for key, diffs in sorted(artifact["pairwise_differences"].items()):
        lines.append(f"- {key}: " + ", ".join(
            f"{m} {v:+.4f}" for m, v in diffs.items()))
    lines.append("")
    lines.append("## Per-query metrics")
    lines.append("| query | lexical R@5/R@10/MRR | vector R@5/R@10/MRR | "
                 "hybrid R@5/R@10/MRR | highest per metric |")
    lines.append("|---|---|---|---|---|")
    fmt = lambda s, m: "null" if s.get(m) is None else f"{s[m]:.3f}"
    for qid, entry in artifact["per_query"].items():
        cells = []
        for name in ("lexical", "vector", "hybrid"):
            cells.append("/".join(fmt(entry[name], m) for m in METRICS))
        desc = entry["descriptive"]
        cells.append("/".join(desc[m] for m in METRICS))
        lines.append(f"| {qid} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("## Latency (seconds per query)")
    for name in ("lexical", "vector", "hybrid"):
        lat = artifact["latency_seconds"].get(name) or {}
        lines.append(f"- {name}: mean {lat.get('mean')}, median "
                     f"{lat.get('median')}, P95 {lat.get('p95')} (n={lat.get('n')})")
    lines.append("")
    lines.append("## Methodological notes")
    lines.append("- RRF constant 60 is the pre-existing documented default; no "
                 "tuning was performed.")
    lines.append("- Hybrid fuses full in-scope branch rankings; only the fused "
                 "list is cut to top-10.")
    lines.append("- Temporal-only queries carry no lexical text; their hybrid "
                 "scores come from the vector branch plus scope filtering.")
    lines.append("- Recall@K discriminates more than MRR here; empty queries "
                 "are excluded everywhere.")
    return "\n".join(lines) + "\n"


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 5A.4/5: frozen comparison")
    parser.add_argument("--lexical-latency", default=None,
                        help="temp lexical metrics JSON carrying latency block")
    parser.add_argument("--hybrid", default=None,
                        help="hybrid results JSON for three-method comparison")
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--output-md", default=None)
    args = parser.parse_args(argv)

    try:
        lexical = _load(PROJECT_ROOT / LEXICAL_PATH)
        vector = _load(PROJECT_ROOT / VECTOR_PATH)
        benchmark = _load(PROJECT_ROOT / BENCHMARK_PATH)
    except (OSError, ValueError) as exc:
        print(f"comparison error: bad input: {exc}")
        return 2
    lex_lat = None
    if args.lexical_latency:
        try:
            lex_lat = _load(Path(args.lexical_latency))["latency_seconds"]
        except (OSError, ValueError, KeyError) as exc:
            print(f"comparison error: bad latency input: {exc}")
            return 2
    try:
        artifact = build_artifact(lexical, vector, benchmark, lex_lat)
    except ValueError as exc:
        print(f"comparison error: {exc}")
        return 2
    problems = verify_expected(artifact)
    if problems:
        for problem in problems:
            print(f"comparison mismatch: {problem}")
        return 2
    if args.hybrid:
        try:
            hybrid = _load(Path(args.hybrid))
        except (OSError, ValueError) as exc:
            print(f"comparison error: bad hybrid input: {exc}")
            return 2
        try:
            artifact = build_hybrid_artifact(lexical, vector, hybrid, benchmark)
        except ValueError as exc:
            print(f"comparison error: {exc}")
            return 2
        out_json = Path(args.output_json) if args.output_json else \
            PROJECT_ROOT / "eval/results_hybrid_comparison_v1.json"
        out_md = Path(args.output_md) if args.output_md else \
            PROJECT_ROOT / "eval/results_hybrid_comparison_v1.md"
        with out_json.open("w", encoding="utf-8") as fh:
            json.dump(artifact, fh, indent=2, sort_keys=True)
        with out_md.open("w", encoding="utf-8") as fh:
            fh.write(render_hybrid_markdown(artifact))
        print(f"compared 3 methods over {len(artifact['per_query'])} queries; "
              f"diffs {artifact['pairwise_differences']} -> {out_json}, {out_md}")
        return 0
    with (PROJECT_ROOT / OUTPUT_JSON).open("w", encoding="utf-8") as fh:
        json.dump(artifact, fh, indent=2, sort_keys=True)
    with (PROJECT_ROOT / OUTPUT_MD).open("w", encoding="utf-8") as fh:
        fh.write(render_markdown(artifact))
    print(f"compared {len(artifact['per_query'])} queries; "
          f"diffs {artifact['vector_minus_lexical']} -> {OUTPUT_JSON}, {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
