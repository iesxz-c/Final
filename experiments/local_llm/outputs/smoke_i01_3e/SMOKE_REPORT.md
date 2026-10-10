# 3E smoke test — I01-hybrid, Qwen2.5-3B-Instruct Q4_K_M (CPU)

Outcome: **BLOCKED — context overflow. No generation, no validation.**
Stopped per protocol after the single mandated request. No retries, no
model switch, no validator or evidence change.

## Request (exact)
- Prompt: frozen 3E system prompt (2,675 chars) + frozen serialization of
  frozen I01-hybrid `result_3d` (247 evidence IDs) + verbatim question =
  **183,288 chars**; server-tokenized to **53,308 prompt tokens**.
- Runtime context: `--ctx-size 65536 --rope-scaling yarn
  --yarn-orig-ctx 32768` (YaRN extrapolation documented as experimental).
- Server enforced: `n_ctx_slot = 32768` (hard cap at training context).
- Verbatim server error: `request (53308 tokens) exceeds the available
  context size (32768 tokens), try increasing it` (HTTP 400, n_tokens = 0,
  truncated = 0 — nothing generated, nothing silently cut).

## Machine cost observed
- Model load: ~8–20 s. Server resident ~5.05 GB during request.
- System RAM free fell to **0.46 GB** at request time (12.68 GB total).
- An earlier server instance died idle with no crash trace (likely memory
  pressure); second instance served /health then the single request.

## Generation vs validation (kept separate)
- Generation: FAILED (no output; raw_output.txt absent by design — there is
  nothing verbatim to save).
- Validation: NOT REACHED (no output to validate; frozen validator untouched).

## What this establishes
- Qwen2.5-3B-Instruct (32,768 native context) cannot accept full-context
  AEGIS 3E prompts (~45–53k tokens) on this llama.cpp build, which caps
  slots at training context despite YaRN flags.
- Full-context local 3E/3F on this hardware+model combination is not
  feasible without either (a) a natively longer-context local model
  (new approval + new memory analysis), or (b) reduced-context stages
  (forbidden under current constraints: no evidence truncation).
- 3C-scale prompts (~hundreds of tokens) were not tested; no claim is made
  about them either way.
