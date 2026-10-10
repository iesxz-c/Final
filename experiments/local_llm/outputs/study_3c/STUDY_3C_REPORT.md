# 3C field study — 10 benchmark cases, local Qwen2.5-3B Q4_K_M (CPU)

Scope: generation + frozen schema validation + mechanical field
comparison only. No 3D/3E/3F, no grades, no plan repair. Per-case raw
plans preserved under outputs/study_3c/<qid>/raw_output.txt; machine log
at logs/study_3c.jsonl.

## Aggregate (mechanical)
- Schema validity: 10/10 valid, 0 request failures, 0 validator errors.
- Latency: 14.6–29.2 s per plan (~18.5 s mean); ~453–465 prompt tokens,
  ~103–140 generated tokens; native 8k context; server otherwise idle.
- video_exact_corpus_match: 3/10 (I05, I11, I19 only).
- Null-time scopes reproduced exactly (start/end null): 7/7.
- Non-null scope times: I05 0/100 exact; I10 36/42 exact; I11 14/32
  exact; I01 27/49 vs scope 27.7/48.9 (integer-rounded, wider window).
- Query source field: surveillance_event in 10/10 local queries
  (locked reference plans use object/generic_action/null on several of
  the same questions; recorded as reference, not a grade).
- Local query texts frequently embed full video paths/filenames
  (I10, I11, I22, I23, I28); locked plans use short keywords.
- temporal_context_seconds nonzero in 4/10 (I01:22, I05:100, I10:6,
  I11:18); remainder 0.

## Recurring weakness (mechanical, confirmed across cases)
In 7/10 plans the model strips the `anomaly/` path prefix from video_id
(I01, I02, I10, I22, I23, I28, I30). Corpus video IDs are full relative
paths matched exactly downstream, so these 7 plans would retrieve
nothing on a video filter. The 3 passing cases kept the full path.
Schema validity (10/10) does not catch this: the field is a free-form
string and any non-empty value validates.

## What this does and does not establish
- Establishes: local 3C generation is reliable at the schema level with
  stable ~15–30 s latency, and the ID-prefix defect is systematic (7/10),
  not a one-off.
- Does not establish: retrieval effectiveness of these plans, 3E/3F
  quality, or end-to-end local feasibility (3E/3F remain context-blocked
  per the Phase-2 report).
