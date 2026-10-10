# 3C smoke test — I01 question, Qwen2.5-3B-Instruct Q4_K_M (CPU)

## Outcome
- Generation: SUCCESS (schema-valid JSON, 116 tokens).
- Frozen 3C validation: PASS (`parse_and_validate_plan`, no error).

## Measured
- Prompt: 2,004 chars -> 464 server tokens. Native 8,192 context; no
  extrapolation, no truncation.
- Prefill 12.06 s (38.5 tok/s); decode 13.13 s (8.8 tok/s); request
  25.29 s total; model load ~20 s (separate).
- Server resident ~3.5 GB; system free RAM ~1.8 GB during run (12.68 total).
- No MODEL_API_KEY in env; Meta client never imported/instantiated.

## Functional observations (factual, not grades)
The validated plan differs from production-backend conventions in ways
the frozen validator permits but downstream stages would feel:
- `video_id` is `Burglary032_x264.mp4` (path prefix stripped); corpus IDs
  are full relative paths and video filters match exactly, so this value
  would retrieve nothing downstream.
- `source` is `surveillance_event` for the query `person` (an object-class
  label); narrows retrieval to the wrong evidence stream.
- `temporal_context_seconds` is 22 with no context requested in the
  question (validator range is [0, 300], so this passes).

## Scope
One 3C request only. No 3D/3E/3F, no end-to-end run. 3E/3F remain blocked
by the 32k context cap established in the 3E smoke report.
