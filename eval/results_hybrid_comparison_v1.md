# Lexical vs Vector vs Hybrid Retrieval Comparison (v1)

## Setup
- Corpus: 7927 fused records, 155 videos
- Benchmark: 30 queries, 22 positive, 8 intentionally empty
- Lexical: frozen Phase 3A substring via rule-derived terms
- Vector: all-MiniLM-L6-v2 + local Qdrant cosine, verbatim queries
- Hybrid: RRF (score = sum(1 / (constant + rank)), constant=60); documented default constant; never tuned

## Aggregates (n=22)
- lexical: recall@5 0.4315, recall@10 0.6045, mrr 0.8182
- vector: recall@5 0.4743, recall@10 0.6917, mrr 0.8565
- hybrid: recall@5 0.5686, recall@10 0.7449, mrr 0.9659

## Pairwise absolute differences
- hybrid_minus_lexical: recall@5 +0.1372, recall@10 +0.1405, mrr +0.1477
- hybrid_minus_vector: recall@5 +0.0943, recall@10 +0.0532, mrr +0.1094
- vector_minus_lexical: recall@5 +0.0429, recall@10 +0.0872, mrr +0.0383

## Per-query metrics
| query | lexical R@5/R@10/MRR | vector R@5/R@10/MRR | hybrid R@5/R@10/MRR | highest per metric |
|---|---|---|---|---|
| Q01 | 0.385/0.769/1.000 | 0.308/0.692/1.000 | 0.385/0.769/1.000 | lexical/lexical/lexical |
| Q02 | 0.147/0.294/1.000 | 0.147/0.294/1.000 | 0.147/0.294/1.000 | lexical/lexical/lexical |
| Q03 | null/null/null | null/null/null | null/null/null | n/a/n/a/n/a |
| Q04 | null/null/null | null/null/null | null/null/null | n/a/n/a/n/a |
| Q05 | 0.357/0.643/1.000 | 0.286/0.571/1.000 | 0.357/0.714/1.000 | lexical/hybrid/lexical |
| Q06 | 1.000/1.000/1.000 | 0.500/1.000/0.200 | 1.000/1.000/1.000 | lexical/lexical/lexical |
| Q07 | null/null/null | null/null/null | null/null/null | n/a/n/a/n/a |
| Q08 | 1.000/1.000/1.000 | 1.000/1.000/1.000 | 1.000/1.000/1.000 | lexical/lexical/lexical |
| Q09 | 0.000/0.000/0.000 | 1.000/1.000/1.000 | 1.000/1.000/1.000 | vector/vector/vector |
| Q10 | 0.000/0.000/0.000 | 1.000/1.000/1.000 | 1.000/1.000/1.000 | vector/vector/vector |
| Q11 | 0.000/0.000/0.000 | 1.000/1.000/1.000 | 1.000/1.000/1.000 | vector/vector/vector |
| Q12 | null/null/null | null/null/null | null/null/null | n/a/n/a/n/a |
| Q13 | null/null/null | null/null/null | null/null/null | n/a/n/a/n/a |
| Q14 | null/null/null | null/null/null | null/null/null | n/a/n/a/n/a |
| Q15 | 0.455/0.818/1.000 | 0.182/0.273/0.500 | 0.364/0.727/1.000 | lexical/lexical/lexical |
| Q16 | 0.217/0.435/1.000 | 0.217/0.391/1.000 | 0.217/0.435/1.000 | lexical/lexical/lexical |
| Q17 | 0.385/0.769/1.000 | 0.231/0.462/1.000 | 0.385/0.615/1.000 | lexical/lexical/lexical |
| Q18 | 0.500/1.000/1.000 | 0.500/1.000/1.000 | 0.500/1.000/1.000 | lexical/lexical/lexical |
| Q19 | 0.227/0.455/1.000 | 0.045/0.045/0.500 | 0.136/0.318/1.000 | lexical/lexical/lexical |
| Q20 | 0.135/0.270/1.000 | 0.135/0.243/1.000 | 0.135/0.270/1.000 | lexical/lexical/lexical |
| Q21 | 0.833/1.000/1.000 | 0.833/1.000/1.000 | 0.833/1.000/1.000 | lexical/lexical/lexical |
| Q22 | 0.714/1.000/1.000 | 0.714/1.000/1.000 | 0.714/1.000/1.000 | lexical/lexical/lexical |
| Q23 | 0.250/0.500/1.000 | 0.250/0.500/1.000 | 0.250/0.500/1.000 | lexical/lexical/lexical |
| Q24 | null/null/null | null/null/null | null/null/null | n/a/n/a/n/a |
| Q25 | null/null/null | null/null/null | null/null/null | n/a/n/a/n/a |
| Q26 | 0.172/0.345/1.000 | 0.172/0.345/1.000 | 0.172/0.345/1.000 | lexical/lexical/lexical |
| Q27 | 1.000/1.000/1.000 | 0.000/1.000/0.143 | 1.000/1.000/0.250 | lexical/lexical/lexical |
| Q28 | 0.000/0.000/0.000 | 0.200/0.400/1.000 | 0.200/0.400/1.000 | vector/vector/vector |
| Q29 | 0.714/1.000/1.000 | 0.714/1.000/1.000 | 0.714/1.000/1.000 | lexical/lexical/lexical |
| Q30 | 1.000/1.000/1.000 | 1.000/1.000/0.500 | 1.000/1.000/1.000 | lexical/lexical/lexical |

## Latency (seconds per query)
- lexical: mean None, median None, P95 None (n=None)
- vector: mean 0.255, median 0.221, P95 0.473 (n=30)
- hybrid: mean 0.262, median 0.221, P95 0.47 (n=30)

## Methodological notes
- RRF constant 60 is the pre-existing documented default; no tuning was performed.
- Hybrid fuses full in-scope branch rankings; only the fused list is cut to top-10.
- Temporal-only queries carry no lexical text; their hybrid scores come from the vector branch plus scope filtering.
- Recall@K discriminates more than MRR here; empty queries are excluded everywhere.
