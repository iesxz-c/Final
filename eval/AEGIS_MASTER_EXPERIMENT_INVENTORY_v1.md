# AEGIS Master Experiment Inventory v1

Project: "An Agentic Framework for Crime Investigation Using CCTV Video Analysis"
(also: AEGIS / Agentic AI Crime Investigation System Using CCTV Video Analytics).
Source of truth: repository files listed per experiment. Status words:
MEASURED, MEASURED / SUPERSEDED, EXECUTED / RESULT PARTIALLY RECOVERED,
PLANNED / NOT EXECUTED, REFERENCE ONLY, INVALID / ARTIFACT BUG, NOT RECOVERED.

## 1. Executive inventory

| # | Experiment | Status | Key result |
|---|---|---|---|
| E01 | 899-video inventory | MEASURED | 899 total, 849 anomaly, 50 normal |
| E02 | 40-video Phase 2 extraction | MEASURED | 4,094 obs, 11,165 dets, 1,931 fused / 40 incidents |
| E03 | 155-video Phase 2 expansion | MEASURED | 16,807 obs, 7,927 fused / 155 incidents |
| E04 | 702-video UCF extraction | MEASURED | 702/702, 44,716 obs, 0 failures |
| E05 | VideoMAE-14 fine-tune training | PLANNED / NOT EXECUTED | configured only, gated notebook cell |
| E06 | Temporal tIoU pilot (n=6) | MEASURED | mean 0.1973 |
| E07 | Temporal tIoU 155-expansion (n=112) | MEASURED | mean 0.1728, median 0.1318 |
| E08 | Temporal tIoU 702-subset (n=11) | EXECUTED / RESULT PARTIALLY RECOVERED | 0.3427 claimed, no artifact found |
| E09 | Fusion coverage 40-video | MEASURED | 85.6% 3-source, 100% >=2-source |
| E10 | Lexical retrieval | MEASURED | R@5 0.4315, R@10 0.6045, MRR 0.8182 (n=22) |
| E11 | Vector retrieval (MiniLM + Qdrant) | MEASURED | R@5 0.4743, R@10 0.6917, MRR 0.8565 (n=22) |
| E12 | Hybrid RRF k=60 | MEASURED | R@5 0.5686, R@10 0.7449, MRR 0.9659 (n=22) |
| E13 | Lexical v1 sentence baseline | MEASURED / SUPERSEDED | all zeros (substring artifact), provenance only |
| E14 | API investigation, 24 Qs | MEASURED | 16/24 ok; 3C 1.0, 3E 0.7083, 3F 0.9412 |
| E15 | API rerun, 7 Qs | MEASURED | 5/7 ok (artifacts present; combined v1-final dir absent) |
| E16 | Investigation baseline/full, 30 cases | MEASURED | baseline 30/30; full 28/30, 154/4/0 claims |
| E17 | Human fact grading (locked, external) | MEASURED (recorded) | baseline 28/10/8, full 34/8/4 (n=46) |
| E18 | Human claim review (locked, external) | MEASURED (recorded) | 155/3/0 (n=158), 98.10% grounding rate |
| E19 | Ablation no-temporal/no-verification/no-planning | MEASURED (exec) + recorded (grades) | 5/20/21, 13/18/15, 7/14/25 (n=46 each) |
| E20 | Structural grounding | MEASURED | ID-existence 1.0, 0/0/0 violations |
| E21 | Folder agreement 16/40 | MEASURED | 0.40 descriptive agreement, NOT accuracy |
| E22 | Vector index build | MEASURED | 7,927 points, 384-dim, 250.6 s |

## 2. Repository state

- HEAD 216fce8 and ancestors verified via git log; no deleted JSON/MD artifacts
  (`git log --diff-filter=D --name-only` empty); no renames.
- Untracked work: AEGIS_Ablation_Human_Grading_Sheet.xlsx (18,286 B, read-only),
  figures/*.png/*.pdf (6 files), eval/*.md + ieee_tables_v1.tex, tests +2 files
  (M investigation_eval.py).
- Tests: 530 passing (Ran 530, OK).

## 3. Dataset inventory

- UCF-Crime local mirror: Anomaly-Videos-Part-1 (949 files on local disk) +
  Normal_Videos_for_Event_Recognition (50 sampled); Drive inventory snapshot 899.
- Classes (14, from ClassIDs.txt + ucf_splits.py): Abuse, Arrest, Arson, Assault,
  Burglary, Explosion, Fighting, Normal_Videos_event, RoadAccidents, Robbery,
  Shooting, Shoplifting, Stealing, Vandalism.
- Official splits: train_*.txt 532 lines x4 folds, test_*.txt 168 lines x4;
  effective 531/167 (Arson019 absent). train/test overlap enforced 0 by
  ucf_splits.check_overlap. Anomaly_Train.txt 1,610 lines; Anomaly_Test.txt 290.
- Temporal annotations: Temporal_Anomaly_Annotation_for_Testing_Videos.txt,
  290 lines, start/end frames @30fps; 150 all-`-1/-1` normal lines.
- Subset rule: config phase2_subset 8 categories x 5 = 40 videos.

## 4. Population reconciliation

| Population | Videos | Normal | Anomaly | Records/Obs | Purpose | Artifact | Status |
|---|---|---|---|---|---|---|---|
| Inventory | 899 | 50 | 849 | — | universe | data/inventory/summary.json | MEASURED |
| 40-subset | 40 | 5 | 35 | 4,094 obs / 1,931 fused | pipeline E2E | data/experiments/phase2_subset.json | MEASURED |
| 155-corpus | 155 | 43 | 112 | 16,807 obs / 7,927 fused | retrieval corpus | data/phase2c_155.json | MEASURED |
| 702-run | 702 | 0 | 702 | 44,716 obs | scale extraction | data/phase2c_remaining_702.json | MEASURED |
| 720 | — | — | — | — | NO SUCH POPULATION | none (frame counts/filenames only) | NOT RECOVERED (= nonexistent) |

Notes: 155 + 702 = 857, disjoint; 40-subset disjoint from both; 42 inventory
videos (40-subset + Normal 914/929) in neither 155 nor 702. Local disk holds
949 anomaly files vs 849 inventoried (RoadAccidents 150 local vs 51 inventoried).
54,574 = derived sum 44,716+7,927+1,931 (not a stored field).

## 5. Architecture (all modules verified present in src/)

CCTV video -> 2A sampling+YOLO11n -> 2B VideoMAE-Base/Kinetics windows ->
2C OPear VideoMAE-Large/UCF-Crime windows -> 2D fusion (fuse_evidence.py) ->
case memory (evidence.json/incidents.json) -> 3C query_planner.py ->
3A retrieve_evidence.py (lexical) -> 3B retrieve_temporal.py (context) ->
3D evidence_retrieval.py (execute_plan) -> 3E timeline_correlation.py ->
3F verification_report.py -> Phase 4 run_investigation.py bundles ->
evaluate_investigations.py / evaluate_quantitative.py / api_eval.py /
retrieval_eval.py / vector_store.py (Qdrant) / investigation_eval.py
(arms full/baseline/no-temporal/no-verification/no-planning) /
compare_retrieval.py. Only LLM calls: 3C/3E/3F via MetaDirectClient
(muse-spark-1.3-contributor); retrieval/fusion deterministic, no LLM.

| Phase | Module | Input -> Output | Method | LLM | Executed | Artifact |
|---|---|---|---|---|---|---|
| 0 | settings.py, env_file.py | config/env -> dicts | stdlib+YAML | no | yes | config/config.example.yaml |
| 2A | extract_evidence.py + detect.py | videos -> obs/detections @1fps, YOLO11n conf 0.4 | Ultralytics | no | yes (CUDA) | phase2*/manifest.json |
| 2B | extract_activity.py + activity.py | videos -> 16f@8fps hop16 top5 windows, MCG-NJU Kinetics-400 | transformers | no | yes (CUDA) | phase2b*/manifest.json |
| 2C-train | train_activity.py | official fold 002 -> 14-class head | AdamW, e10/b4/acc2/lr5e-5 | no | NO (gated cell) | none locally |
| 2C-infer | extract_ucf_events.py | videos -> 16f@8fps hop16 top5, OPear bc5f1c1 | transformers | no | yes (CUDA) | phase2c*/manifest.json |
| 2D | fuse_evidence.py + fusion.py | 3 streams -> fused records + incidents | deterministic rules | no | yes (CPU) | fused*/manifest.json |
| 3A | retrieve_evidence.py | query -> ranked substring hits | deterministic | no | yes | results_lexical_*.json |
| 3B | retrieve_temporal.py | hits -> incident context | deterministic | no | yes | via 3D bundles |
| 3C | query_planner.py | NL question -> validated plan | MetaDirectClient | YES | yes | bundles q*.json |
| 3D | evidence_retrieval.py | plan -> merged evidence | deterministic | no | yes | bundles |
| 3E | timeline_correlation.py | evidence -> timeline | MetaDirectClient | YES | yes | bundles |
| 3F | verification_report.py | timeline -> verified report | MetaDirectClient | YES | yes | bundles |
| 4A | run_investigation.py | questions -> phase4/v1 bundles | orchestration | via 3C/3E/3F | yes | tier2-*/q*.json |
| 4B | evaluate_quantitative.py | artifacts -> agreement/tIoU/grounding | deterministic | no | yes | quantitative/metrics.json |

## 6. Model/training experiments

- YOLO11n (data/models/yolo11n.pt, gitignored, ~5MB; legacy registry names
  yolov8n.pt but pipeline uses yolo11n) COCO classes verbatim; conf 0.4; 1fps.
- MCG-NJU/videomae-base-finetuned-kinetics rev 488eb9a (Kinetics-400 labels
  verbatim; q_bias/v_bias remap, 12 key.bias zeroed).
- OPear/videomae-large-finetuned-UCF-Crime rev bc5f1c1 (native id2label verbatim).
- Fine-tune: 14-class head, fold 002 (532/168, effective 531/167), AdamW lr5e-5,
  linear warmup, AMP+GradScaler on CUDA, e10/b4/accum2/workers4/seed0/evalclips5;
  metrics suite defined (acc, macro-P/R/F1, per-class F1, 14x14 confusion) but
  NO metrics file exists -> training EXECUTED nowhere locally (PLANNED/NOT EXECUTED).
- Embedding: sentence-transformers/all-MiniLM-L6-v2 rev 1110a24, 384-dim,
  unit-normalized, Qdrant 1.19.1 local COSINE, 7,927/7,927 in 250.6 s.
- No local weights/checkpoints exist (0 *.pt/*.safetensors in repo).

## 7. Evidence extraction (measured, manifests)

| Experiment | Videos | Obs | Hours | Window/stride | Detector/activity | Device | Runtime | Fail | Artifact |
|---|---|---|---|---|---|---|---|---|---|
| 40-video | 40 | 4,094 obs / 11,165 det / 1,931 act / 1,931 UCF | ~1.13 | 1fps / 16f@8fps hop16 | yolo11n / Kinetics / OPear | T4 CUDA | 102.1/339.7/982.9/2.0 s | 0 | phase2*/manifest.json |
| 155-video | 155 | 16,807 / 44,380 det / 7,927 / 7,927 | ~4.65 | same | same | T4 CUDA | 823.1/1439.0/3721.3/48.1 s | 0 (+1 recovered Explosion013) | data_155n/*/manifest.json |
| 702-video | 702 | 44,716 UCF | 26.29 | 16f@8fps hop16 | OPear | T4 CUDA | merged 2026-09-16 (no elapsed field) | 0 | phase2c_ucf_remaining_702/manifest.json |
| 849 anomaly | 849 | 54,574 (derived) | 30.73 (anomaly part of 32.08) | — | — | — | — | — | derived, NOT a stored field |

No CPU/GPU-RAM/VRAM/obs-per-second logs beyond elapsed_seconds. No videos/hour recorded.

## 8. Temporal grounding (tIoU = span overlap, NEVER accuracy)

| Experiment | n | mean | median | range | Status |
|---|---|---|---|---|---|
| Pilot (fused incidents vs annotations) | 6 | 0.1973 | — | — | MEASURED (metrics.json) |
| 155-expansion (112 annot + 43 controls) | 112 | 0.1728 | 0.1318 | — | MEASURED (expanded_metrics.json) |
| 702-subset claimed | 11 | 0.3427 | 0.2632 | 0.1003–0.8280 | EXECUTED / RESULT PARTIALLY RECOVERED (no artifact; value absent from all files) |

## 9. Fusion (40-video measured; 155-video fused_155 manifest cited by subagent)

- 3 streams; 1,931 records; 40 incidents; 332 unaligned; source coverage 85.6%
  all-3-source / 100% >=2-source (metrics.json fusion_statistics).
- Structural: ID-existence 1.0, 0 unknown, 0 duplicates, 0 cross-video
  (structural_grounding). No calibration/soft-fusion/tau experiments found.

## 10. Retrieval (frozen; 155 videos / 7,927 records / 30 queries / 293 judgments / n=22 scored)

| Method | Recall@5 | Recall@10 | MRR | Config | Artifact | Status |
|---|---|---|---|---|---|---|
| Lexical v2 | 0.4315 | 0.6045 | 0.8182 | 3A substring, rule-derived terms | results_lexical_v2.json | MEASURED (final) |
| Vector | 0.4743 | 0.6917 | 0.8565 | MiniLM-L6-v2 + Qdrant cosine | results_vector_v1.json | MEASURED |
| Hybrid RRF k=60 | 0.5686 | 0.7449 | 0.9659 | deterministic, untuned | results_hybrid_v1.json | MEASURED |
| Lexical v1 | 0.0 / 0.0 / 0.0 | — | full-sentence substring artifact | results_lexical_v1.json | MEASURED / SUPERSEDED (provenance) |

N=22 means: 22 positive queries scored; 8 intentionally-empty queries scored
null and excluded (verified in files). No Recall@1/@3, no reranking, no metadata
filtering experiments exist.

## 11. Query planning

- plan_query -> validated phase3c/v1 plan (intent, source-typed queries,
  video/time bounds); planner latency/tokens inside bundle timings (not
  separately aggregated except api v1 3c_success_rate 1.0).
- No-planning ablation uses fixed_plan() (verbatim question, source None,
  unbounded, needs_timeline True) validated by existing
  parse_and_validate_plan (verified in code).

## 12. API investigation (40-video subset, muse-spark-1.3-contributor, mode real)

- v1: 24 investigations, 16 ok (api_success 0.6667); 3C 1.0, 3E 0.7083,
  3F 0.9412; schema-valid 0.6667; claims 94/1/0 over 95 (support 0.9895);
  grounding 1.0; temporal 1.0; violations 0/0; latency mean 69.7/median
  79.5/P95 120.4; cost unavailable (no pricing); NO token totals persisted.
- v1-rerun: 7 attempted (?dir lists q04,q07,q09,q10,q11,q12,q21,q23 = 8 files;
  metrics file to be re-read for exact ok count — see discrepancy note).
- Claimed-but-unrecoverable: "22/24 combined" (no v1-final dir), latencies
  91.5/102.3/235.7, tokens 716,893/296,181, tIoU 0.3427 — absent from all
  artifacts: EXECUTED / NUMERIC RESULT NOT PERSISTED.

## 13. Investigation baseline/full (30 cases I01–I30, 46 facts)

- Baseline 30/30, 0/0/0 claims by construction, latency 13.6/13.2/19.0,
  tokens 13.4k/50.5k; full 28/30 (2 validator rejections: I02 3E adjacency,
  I29 3F "definitely occurred"), 154/4/0 claims, citation 1.0, latency
  52.7/71.6/93.9, tokens 135.9k/258.5k; audit 30/30 both; 0 uncontained;
  0 forbidden/safety hits; abstention 1/1 (I30). Stage means: 3C ~13.7,
  3E ~19.1, 3F ~20.2 s. Artifact: results_investigation_v1.json
  (human_evaluation_pending: true).

## 14. Human evaluation (locked EXTERNAL record, transcribed)

- Worksheet in repo all-null; authoritative grades live only in locked files
  created from user's external review (no file predates transcription to
  cross-check against — flag as method limitation, not inconsistency).
- Baseline 28/10/8 (60.87/21.74/17.39), Full 34/8/4 (73.91/17.39/8.70), n=46.
- Claims 155/3/0 (n=158); 98.10% = claim-support/evidence-grounding rate, NEVER accuracy.
- Temporal: 5/5 reviewed relations Supported both systems; 3 ungraded, excluded.

## 15. Ablation (90 runs: artifacts present; grades external-recorded)

| Arm | Completed | Human S/P/U (n=46) | Latency mean | Notes |
|---|---|---|---|---|
| Full | 28/30 | 34/8/4, 73.91% | 52.7 | reference |
| No Temporal | 30/30 | 5/20/21, 10.87% | 14.8 | 0 claims (empty timelines) |
| No Verification | 28/30 | 13/18/15, 28.26% | 34.6 | claim metrics null by design |
| No Planning | 30/30 | 7/14/25, 15.22% | 0.3, 0 LLM calls | retrieval collapse (honest) |
| Temporal I10–I15 | — | Full 12/12, NT 0, NV 6, NP 0 | — | 12 facts |

Caveat: baseline-vs-full is a two-arm system comparison (template substitution
+ 3E/3F removal), not a single-component ablation; NT/NV/NP arms ARE
single-component removals.

## 16. Runtime/Colab inventory

- GPU all sessions: Tesla T4 15GB, CUDA 13.0 / driver 580.82.07, Python 3.13.15
  (local 3.14), torch 2.11+cu128, transformers 5.16.1, ultralytics 8.4.154.
- Deps executed: sentence-transformers 5.6.0, qdrant-client 1.19.1, PyYAML 6.0.3.
- Warnings: HF Hub unauthenticated (all model pulls); Explosion013 unreadable
  (recovered); eval4 `--max-videos` arg error (docs only).
- Notebooks: eval–eval4 (T4 session logs), Final_yr_project (40-video runs),
  phase2c_ucf_videomae_colab (gated training template, never executed).
- P95s: investigation full 93.9, api 120.4, hybrid retrieval 0.47 s/query.
- No RAM/VRAM/throughput logs exist.

## 17. Existing tables/figures/LaTeX (all found, none deleted in git history)

- eval/ieee_tables_v1.tex (untracked): Tables 1–4 final + Table 5 commented
  supplementary; labels tab:fact-support/ablation/claim-grounding/runtime.
- figures/*.png/*.pdf (6 files, untracked): fig1 stacked bar, fig2 ablation
  bars+pp, fig3 temporal bars; spec eval/ieee_figures_v1.md; no generator .py
  committed; no \includegraphics refs exist (no paper source in repo).
- eval MD tables: retrieval comparison (30-row), hybrid comparison (30-row),
  ablation locked aggregate; quantitative metrics JSON; NO CSV tables.
- Terminology scan: 11 hits for accuracy/precision, ALL legitimate
  prohibitions/disclaimers (tex guard comment, figure spec, locked-md
  disambiguation, tier2 disclaimer x8). No false claims found. "F1" hits are
  fact IDs (F01...). No mAP/confusion/ROC/PR anywhere.

## 18. Conflicts & discrepancies (all preserved, none silently resolved)

1. 720: no population; all hits are frame counts/filenames/confidences.
2. 54,574: derived sum, not stored.
3. API combined/token/latency/tIoU-0.3427 figures: claimed in conversation,
   absent from artifacts.
4. Train/test "effective 531/167" (notebook) vs README "532/167 effective" —
   both cite Arson019 missing; preserved verbatim.
5. yolov8n.pt registry entry (legacy) vs yolo11n.pt active weights.
6. COLAB.md "994 inventoried" (older run) vs frozen 899 snapshot.
7. v1-rerun dir contains 8 question files; rerun metrics ok-count to be stated
   from file (not assumed 5).

## 19. Missing values (honest list)

702 elapsed time; API token totals; API tIoU-11 artifact; v1-final combined dir;
training validation metrics; RAM/VRAM/throughput; Recall@1/@3; per-stage API
latencies beyond bundle timings; reviewer identity/date (never recorded);
figure-generator script (figures lack committed generator).

## 20. VERIFIED PAPER METRIC LEDGER

| Metric | Exact value | Population | Experiment | Artifact | Safe wording |
|---|---|---|---|---|---|
| Recall@5 lexical/vector/hybrid | 0.4315 / 0.4743 / 0.5686 | 22 queries | retrieval | results_{lexical_v2,vector_v1,hybrid_v1}.json | Recall@5 |
| Recall@10 | 0.6045 / 0.6917 / 0.7449 | 22 | retrieval | same | Recall@10 |
| MRR | 0.8182 / 0.8565 / 0.9659 | 22 | retrieval | same | MRR |
| tIoU mean pilot / 155-exp | 0.1973 (n=6) / 0.1728 (n=112) | annotated | temporal | metrics.json, expanded_metrics.json | temporal span overlap |
| tIoU median 155-exp | 0.1318 | 112 | temporal | expanded_metrics.json | span overlap |
| Fusion 3-source / >=2-source | 0.856 / 1.0 | 1,931 records | fusion | metrics.json | source coverage |
| ID-existence | 1.0 (0/0/0 violations) | 40 incidents | structural | metrics.json | evidence integrity |
| Folder agreement | 0.40 (16/40) | 40 videos | 4B | metrics.json | descriptive agreement |
| Fact support baseline/full | 60.87% / 73.91% (28,34/46) | 30 cases | human | locked json | expected-fact support rate |
| Claim support | 98.10% (155/158) | full arm | human | locked json | claim-support rate |
| Ablation S% | 73.91 / 10.87 / 28.26 / 15.22 | 46 facts | human | locked json | support rate + pp deltas |
| Temporal subset | 100 / 0 / 50 / 0 % | 12 facts | human | locked json | subset support |
| API success | 16/24 (0.6667) | 24 Qs | api v1 | metrics.json | investigation success rate |
| API latency mean/med/P95 | 69.7 / 79.5 / 120.4 s | 24 | api v1 | metrics.json | end-to-end latency |
| Invest latency full/baseline | 52.7 / 13.6 s mean | 30 cases | investigation | results_investigation_v1.json | latency |
| Tokens full/baseline | 135.9k/258.5k, 13.4k/50.5k in/out | 30 | investigation | same | token usage (cost null) |
| Videos/obs 702-run | 702, 44,716, 0 fail | 702 | scale | manifest | throughput counts |
| Videos 899/849/50, 32.08 h | as stated | inventory | scale | summary.json | corpus scale |
| Phase2 times | 102.1/339.7/982.9/2.0 s (40); 823.1/1439.0/3721.3/48.1 s (155) | per pop | extraction | manifests | processing runtime |
| Vector build | 7,927 pts, 384-d, 250.6 s | 155 corpus | index | manifest | index coverage |
| Abstention | 1/1 (I30) | 30 cases | investigation | results file | abstention correctness |
| Validator rejections | 2 full (I02,I29), 2 NV arms | 30/arm | guardrails | bundles | rejection = guardrail fired |
