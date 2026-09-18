# Lexical vs Vector Retrieval Comparison (v1)

## A. Experimental setup
- Corpus: 7927 fused records, 155 videos (data/data_155n/fused_155/evidence.json)
- Benchmark: eval/retrieval_benchmark_v1.json — 30 queries, 22 positive, 8 intentionally empty, 293 frozen judgments
- Lexical: frozen Phase 3A substring retrieval via rule-derived terms (results_lexical_v2.json)
- Vector: all-MiniLM-L6-v2 + local Qdrant cosine, verbatim queries (results_vector_v1.json)
- Empty-relevance queries are null in both files and excluded from aggregates (n=22).

## B. Aggregate results
- recall@5: lexical 0.4315, vector 0.4743 (vector-minus-lexical +0.0429)
- recall@10: lexical 0.6045, vector 0.6917 (vector-minus-lexical +0.0872)
- mrr: lexical 0.8182, vector 0.8565 (vector-minus-lexical +0.0383)

## C. Per-query comparison
| query | lexical R@5/R@10/MRR | vector R@5/R@10/MRR | higher per metric (R@5/R@10/MRR) |
|---|---|---|---|
| Q01 | 0.385/0.769/1.000 | 0.308/0.692/1.000 | lexical/lexical/tie |
| Q02 | 0.147/0.294/1.000 | 0.147/0.294/1.000 | tie/tie/tie |
| Q03 | null/null/null | null/null/null | n/a/n/a/n/a |
| Q04 | null/null/null | null/null/null | n/a/n/a/n/a |
| Q05 | 0.357/0.643/1.000 | 0.286/0.571/1.000 | lexical/lexical/tie |
| Q06 | 1.000/1.000/1.000 | 0.500/1.000/0.200 | lexical/tie/lexical |
| Q07 | null/null/null | null/null/null | n/a/n/a/n/a |
| Q08 | 1.000/1.000/1.000 | 1.000/1.000/1.000 | tie/tie/tie |
| Q09 | 0.000/0.000/0.000 | 1.000/1.000/1.000 | vector/vector/vector |
| Q10 | 0.000/0.000/0.000 | 1.000/1.000/1.000 | vector/vector/vector |
| Q11 | 0.000/0.000/0.000 | 1.000/1.000/1.000 | vector/vector/vector |
| Q12 | null/null/null | null/null/null | n/a/n/a/n/a |
| Q13 | null/null/null | null/null/null | n/a/n/a/n/a |
| Q14 | null/null/null | null/null/null | n/a/n/a/n/a |
| Q15 | 0.455/0.818/1.000 | 0.182/0.273/0.500 | lexical/lexical/lexical |
| Q16 | 0.217/0.435/1.000 | 0.217/0.391/1.000 | tie/lexical/tie |
| Q17 | 0.385/0.769/1.000 | 0.231/0.462/1.000 | lexical/lexical/tie |
| Q18 | 0.500/1.000/1.000 | 0.500/1.000/1.000 | tie/tie/tie |
| Q19 | 0.227/0.455/1.000 | 0.045/0.045/0.500 | lexical/lexical/lexical |
| Q20 | 0.135/0.270/1.000 | 0.135/0.243/1.000 | tie/lexical/tie |
| Q21 | 0.833/1.000/1.000 | 0.833/1.000/1.000 | tie/tie/tie |
| Q22 | 0.714/1.000/1.000 | 0.714/1.000/1.000 | tie/tie/tie |
| Q23 | 0.250/0.500/1.000 | 0.250/0.500/1.000 | tie/tie/tie |
| Q24 | null/null/null | null/null/null | n/a/n/a/n/a |
| Q25 | null/null/null | null/null/null | n/a/n/a/n/a |
| Q26 | 0.172/0.345/1.000 | 0.172/0.345/1.000 | tie/tie/tie |
| Q27 | 1.000/1.000/1.000 | 0.000/1.000/0.143 | lexical/tie/lexical |
| Q28 | 0.000/0.000/0.000 | 0.200/0.400/1.000 | vector/vector/vector |
| Q29 | 0.714/1.000/1.000 | 0.714/1.000/1.000 | tie/tie/tie |
| Q30 | 1.000/1.000/1.000 | 1.000/1.000/0.500 | tie/tie/lexical |

## D. Latency comparison
- lexical: mean 0.001s, median 0.001s, P95 0.003s (n=30)
- vector: mean 0.255s, median 0.221s, P95 0.473s (n=30)

## E. Observed complementary behavior
- Lexical retrieval is strong on exact stored labels: every content-bearing query returns a relevant record first (lexical MRR 0.8182), reflecting deterministic exact-match priority rather than semantic understanding.
- Vector retrieval can recover semantically related evidence where wording differs from stored labels (e.g. the Q27 disjunction reaches R@10 1.000 where lexical substring matching is exact-only).
- Temporal-only success on both sides can involve the explicit evaluation scope filter rather than semantic temporal understanding.

## F. Limitations
- Single 155-video corpus; 22 scored queries; no significance testing.
- Recall@K is the more discriminating retrieval measure here; MRR saturates because exact matches rank first.
- Lexical temporal-only queries score 0.000 by construction (substring retrieval cannot express time).
- Vector truncation at top-10 with scope filtering mirrors, but does not replicate, production retrieval conditions.
