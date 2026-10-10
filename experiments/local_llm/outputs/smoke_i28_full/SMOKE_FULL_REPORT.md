# Full-pipeline smoke — I28, local Qwen2.5-3B Q4_K_M (CPU)

## Outcome: plumbing complete, reasoning untested
All four stages executed in order with frozen validators passing, but 3D
retrieved 0 records, so 3E/3F exercised only their deterministic
empty-evidence short-circuits. This demonstrates pipeline wiring on local
hardware, NOT local 3E/3F reasoning quality.

## Stage log
- 3C (local, 27.8 s, 454 prompt / 120 gen tokens): valid plan, but with
  the known content defect — `video_id` stripped to
  `RoadAccidents021_x264.mp4` (corpus IDs carry the `anomaly/` prefix)
  and query/source pointed at the video path under `surveillance_event`.
- 3D (frozen, 0.7 s): 0 incident groups, 0 records (exact video match
  failed — correct behavior for that plan, no error).
- 3E (local, 27.5 s, 560 prompt / 89 gen tokens): valid empty timeline
  (no evidence supplied — deterministic short-circuit, no reasoning).
- 3F (local, 39.3 s, 569 prompt / 176 gen tokens): valid "No verifiable
  claims" (same short-circuit).
- Decode ~8.1–8.4 tok/s; server within native 32k context throughout.
- No MODEL_API_KEY in env; Meta client never touched.

## Interpretation
The single point of failure is local 3C plan content (already documented
in the 3C smoke report), not the harness, validators, or server. Fixing
or working around the plan (hand-written plan, plan repair, re-prompting)
was NOT done: it would deviate from the frozen pipeline and is withheld
for approval. I28's paired-experiment hybrid run (10 vector-only direct,
10 claims) remains the reference for what this case yields with a
working plan.
