# AEGIS verified table pack v1 — all tables below are MEASURED unless noted.

## TABLE A — Dataset/population summary
| Population | Videos | Normal | Anomaly | Purpose |
|---|---|---|---|---|
| Inventory snapshot | 899 | 50 | 849 | universe |
| 40-video subset | 40 | 5 | 35 | end-to-end pipeline |
| 155-video corpus | 155 | 43 | 112 | retrieval corpus |
| 702-video run | 702 | 0 | 702 | scale extraction |

## TABLE B — Processing/evidence scale
| Experiment | Videos | Observations | Detections/activities | Fused | Runtime |
|---|---|---|---|---|---|
| 40-video | 40 | 4,094 | 11,165 det / 1,931 act / 1,931 UCF | 1,931 / 40 incidents | 102.1 / 339.7 / 982.9 / 2.0 s |
| 155-video | 155 | 16,807 | 44,380 det / 7,927 / 7,927 | 7,927 / 155 incidents | 823.1 / 1439.0 / 3721.3 / 48.1 s |
| 702-video | 702 | 44,716 UCF | — | — | merged 2026-09-16 (no elapsed) |

## TABLE C — Temporal grounding (tIoU = span overlap, never accuracy)
| Experiment | n | Mean | Median |
|---|---|---|---|
| Pilot | 6 | 0.1973 | — |
| 155-expansion | 112 | 0.1728 | 0.1318 |

## TABLE D — Fusion coverage (40-video)
| Records | Incidents | All-3-source | >=2-source |
|---|---|---|---|
| 1,931 | 40 | 85.6% | 100% |

## TABLE E — Structural integrity
| Check | Value |
|---|---|
| ID-existence | 1.0 |
| Unknown / duplicate / cross-video | 0 / 0 / 0 |
| Audit pass (baseline, full) | 30/30, 30/30 |
| Uncontained ranges | 0 |
| Forbidden / safety-phrase hits | 0 / 0 |

## TABLE F — Retrieval (155 videos, 7,927 records, 30 queries, 293 judgments, n=22)
| Method | Recall@5 | Recall@10 | MRR |
|---|---|---|---|
| Lexical (3A substring) | 0.4315 | 0.6045 | 0.8182 |
| Vector (MiniLM-L6-v2 + Qdrant cosine) | 0.4743 | 0.6917 | 0.8565 |
| Hybrid (RRF k=60) | 0.5686 | 0.7449 | 0.9659 |

(Lexical v1 all-zeros superseded — sentence-vs-substring artifact, provenance only.)

## TABLE G — Recall@K = TABLE F Recall columns (no separate experiment).
## TABLE H — Retrieval MRR = TABLE F MRR column.
## TABLE I — Retrieval runtime: hybrid mean 0.262 / median 0.221 / P95 0.47 s per query (n=30).

## TABLE J — API investigation (40-video, 24 questions, muse-spark-1.3-contributor)
| Stage | Success |
|---|---|
| Investigations | 16/24 (0.6667) |
| 3C / 3E / 3F | 1.0 / 0.7083 / 0.9412 |
| Schema-valid | 16/24 |
| Claims S/P/U | 94 / 1 / 0 (n=95) |
| Grounding / temporal | 1.0 / 1.0 |
| Latency mean/med/P95 | 69.7 / 79.5 / 120.4 s |
| Tokens/cost | not persisted / unavailable |

## TABLE K — Baseline vs Full human facts (n=46)
| Configuration | Supported | Partial | Unsupported |
|---|---|---|---|
| Baseline | 28 (60.87%) | 10 (21.74%) | 8 (17.39%) |
| Full | 34 (73.91%) | 8 (17.39%) | 4 (8.70%) |

## TABLE L — Claim grounding (Full, n=158): 155 / 3 / 0, 98.10% claim-support rate (grounding rate, NOT accuracy).

## TABLE M — Ablation human facts (n=46 each)
| Configuration | Supported | Partial | Unsupported | Supported % |
|---|---|---|---|---|
| Full | 34 | 8 | 4 | 73.91 |
| No Temporal | 5 | 20 | 21 | 10.87 |
| No Verification | 13 | 18 | 15 | 28.26 |
| No Planning | 7 | 14 | 25 | 15.22 |

## TABLE N — Temporal subset I10–I15 (12 facts): Full 12/0/0 (100%), NT 0/4/8 (0%), NV 6/4/2 (50%), NP 0/3/9 (0%).

## TABLE O — Runtime/tokens
| Arm | Completed | Mean lat | Tokens in/out |
|---|---|---|---|
| Baseline | 30/30 | 13.6 s | 13.4k / 50.5k |
| Full | 28/30 | 52.7 s | 135.9k / 258.5k |
| No Temporal | 30/30 | 14.8 s | 13.4k / 50.0k |
| No Verification | 28/30 | 34.6 s | 62.8k / 137.8k |
| No Planning | 30/30 | 0.3 s | none (0 LLM calls) |

## TABLE P — Phase 4B: folder agreement 16/40 = 0.40 (descriptive, NOT classification accuracy); fusion/structural as in D/E; normal controls 5/5 descriptive; 702-run 702/702, 44,716 unique IDs, 0 unknown refs.

## TABLE Q — Colab/processing runtime: T4 15GB, CUDA 13.0, torch 2.11+cu128, transformers 5.16.1; per-40-video 2A/2B/2C times in TABLE B; vector build 250.6 s; training never executed.

## TABLE R — Per-case supplementary: 30-row retrieval comparison tables in results_*_comparison_v1.md; 60 investigation bundles; 46-row grading worksheet (locked).
