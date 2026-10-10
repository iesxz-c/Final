# Local-LLM smoke experiment — frozen protocol (Phase 2)

Isolated track. Production code, prompts, schemas, validators, evaluation
artifacts, and the external Meta integration are untouched.

## Pinned inputs (read-only, never copied into outputs as new ground truth)
- Evidence: `data/evaluations/paired_30case/full-hybrid/I01.full-hybrid.json`
  (`result_3d` + `question` only). No 3C, retrieval, 3F, no external API.
- Prompt: frozen `timeline_correlation.SYSTEM_PROMPT` +
  `serialize_for_llm(result_3d)` + verbatim question (same construction as
  `run_timeline`). Measured prompt: 180,613 chars (~45k tokens).
- Schema: frozen `timeline_response_format()` JSON schema, reshaped to the
  llama.cpp `response_format` envelope. Validators unchanged.

## Pinned runtime
- Binary: llama.cpp b11541 `llama-b11541-bin-win-cpu-x64.zip`
  (https://github.com/ggml-org/llama.cpp/releases/download/b11541/llama-b11541-bin-win-cpu-x64.zip).
- Model: `https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf`
  (~2.1 GB, official Qwen org, license qwen-research).
- Server (localhost only): `-c 65536 --rope-scaling yarn --yarn-orig-ctx 32768`
  (prompt exceeds the 32,768 native context; YaRN extrapolation is an
  explicit experimental caveat), `-t 8`, `--cache-type-k q8_0`
  (RAM pressure mitigation; 12.7 GB total, ~2.5 GB free at preflight).
- Request: temperature 0.0, `max_tokens` 4096 (= frozen 3E cap), stream off.

## Integrity rules
- `MODEL_API_KEY` must be absent from the runner environment (asserted).
- `MetaDirectClient` is never imported or instantiated here.
- Raw output saved verbatim; validation via frozen
  `parse_and_validate_timeline` only. Generation success and validation
  success are reported separately.
- Stop conditions: OOM/crash/timeout/context overflow -> stop, report, no
  retries, no model switch, no validator change, no evidence change.
