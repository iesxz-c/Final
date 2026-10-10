# AEGIS local-LLM experiments — consolidated report (read-only consolidation)

All figures below were re-verified against the saved JSONL logs, raw
outputs, server logs, and frozen bundles on the consolidation date. No
reruns, no edits to existing files. verdict key: GEN = generation
success; VAL = frozen-validator verdict. These are reported separately
throughout.

## 0. Fixed configuration (all runs)
- Model: `Qwen/Qwen2.5-3B-Instruct-GGUF`, `qwen2.5-3b-instruct-q4_k_m.gguf`
  (2,104,932,768 bytes; official Qwen org; license qwen-research; 3.09B
  params; 36 layers; native context 32,768).
- Runtime: llama.cpp b11541 `llama-b11541-bin-win-cpu-x64.zip`
  (build 11541, commit f2918cab), CPU-only, `-t 8`, `--cache-type-k q8_0`,
  bound to 127.0.0.1:8080. SHA256 of both downloads recorded in run logs
  (no published checksums exist to compare against — stated, not hidden).
- Hardware: Intel i5-10210U (4C/8T), 12.68 GB RAM, Intel UHD integrated
  graphics, no CUDA (torch CPU-only). No GPU inference is possible here.
- Requests: temperature 0.0, frozen per-stage max_tokens (3C 2048,
  3E 4096, 3F 6000), frozen JSON schemas via server `response_format`,
  stream off. `MODEL_API_KEY` asserted absent on every run (logs record
  the assertion path, never a value); Meta client never imported.

## 1. 3E smoke test (I01-hybrid result_3d) — BLOCKED
- Prompt: 183,288 chars (frozen system prompt + frozen serialization of
  247 evidence IDs + verbatim question); server-tokenized **53,308 tokens**.
- Server enforced `n_ctx_slot = 32768` (hard cap at training context;
  YaRN 65,536 request did not lift it). Verbatim server error:
  `request (53308 tokens) exceeds the available context size
  (32768 tokens)` (HTTP 400, n_tokens = 0, truncated = 0).
- GEN: failed (no output; no raw_output file exists by design).
- VAL: not reached. Model load ~8–20 s; server resident ~5.05 GB; free
  RAM hit 0.46 GB; first server instance died idle without a crash trace
  (consistent with memory pressure, cause unproven).
- Log: `logs/smoke_i01_3e.jsonl` (2 failure records). Report:
  `outputs/smoke_i01_3e/SMOKE_REPORT.md`.

## 2. Single-case 3C smoke test (I01 question) — PASSED (both senses)
- Prompt 2,004 chars -> 464 server tokens; generated 116 tokens
  (331 chars); prefill 12.06 s (38.5 tok/s); decode 13.13 s (8.8 tok/s);
  request 25.293 s total; native 8k context.
- GEN: success. VAL: **pass** (`parse_and_validate_plan`, no error).
- Functional caveat (observed, ungraded): plan used bare
  `Burglary032_x264.mp4` (prefix stripped), `source: surveillance_event`
  for `person`, `temporal_context_seconds: 22`.
- Raw: `outputs/smoke_i01_3c/raw_output.txt`; validated:
  `validated_plan.json`; log: `logs/smoke_i01_3c.jsonl`; report:
  `outputs/smoke_i01_3c/SMOKE_3C_REPORT.md`.

## 3. Full-pipeline plumbing test (I28) — wiring pass, reasoning untested
- 3C local 27.782 s (454/120 tok, valid) -> 3D frozen 0.698 s,
  **0 incident groups, 0 records** (local plan's stripped video_id
  matched nothing; correct frozen behavior) -> 3E local 27.483 s
  (560/89 tok, valid *empty* timeline) -> 3F local 39.263 s (569/176
  tok, valid "No verifiable claims"). Decode ~8.1–8.4 tok/s.
- This is a plumbing demonstration, NOT evidence-grounded reasoning:
  no evidence ever reached 3E/3F (their deterministic empty paths ran).
- Artifacts: `outputs/smoke_i28_full/{3c_plan,3c_raw,3d_result,3e_raw,
  3e_result,3f_raw,3f_result}.json|.txt` + `SMOKE_FULL_REPORT.md`;
  log: `logs/smoke_i28_full.jsonl` (4 stage records). No repair or
  re-prompting was performed.

## 4. Ten-case 3C study (I01,I02,I05,I10,I11,I19,I22,I23,I28,I30)
- Schema validity: **10/10 valid**, 0 request failures, 0 validator errors.
- Latency 14.579–29.155 s (mean 18.5 s); prompt tokens 453–465;
  generated 103–140 tokens.
- video_exact_corpus_match: **3/10** (I05, I11, I19). Recurring defect
  (7/10): `anomaly/` prefix stripped from video_id — schema-valid but
  functionally unmatchable downstream.
- Null time bounds reproduced 7/7; non-null times exact except I01
  (27/49 vs scope 27.7/48.9, integer-rounded).
- Query `source`: `surveillance_event` in 10/10 local plans (locked
  reference plans use object/generic_action/null on several of the same
  questions — reference only).
- `temporal_context_seconds` nonzero in 4/10 (22/100/6/18).
- Raw plans: `outputs/study_3c/<qid>/{raw_output.txt,validated_plan.json}`;
  log: `logs/study_3c.jsonl` (10 records); report:
  `outputs/study_3c/STUDY_3C_REPORT.md`.

## 5. Hardware/model/runtime/limits summary
- i5-10210U CPU-only; 12.68 GB RAM (observed free: 0.46–5.4 GB across
  runs); Qwen2.5-3B Q4_K_M (~2.1 GB weights, ~3.5–5 GB resident);
  llama.cpp b11541 CPU build; decode ~8–9 tok/s; prefill ~30–39 tok/s.
- Binding limits measured: 32,768 hard context cap (blocks full-context
  3E/3F at ~45–53k tokens); RAM exhaustion risk (0.46 GB observed);
  3B plan-content defects (ID prefix, source selection) outside validator
  scope. Sample sizes: n=1 (3E attempt, 3C smoke, full plumbing),
  n=10 (3C study). No statistical claims are made.

## 6. Verification statement
Every figure in §§1–5 was re-read from the JSONL logs, raw outputs,
server logs, and frozen bundles listed above; all agree with the
per-experiment reports. No discrepancies found. Credential scan: the
string `MODEL_API_KEY` occurs only in guard code/comments; no key
material, no Meta endpoint, no Meta client import exists under
`experiments/`. `git status` shows only `?? experiments/` — zero changes
to production code, prompts, schemas, validators, evaluation artifacts,
or API integration.

## 7. Measured facts vs interpretations
- Facts: the numbers, verdicts, error strings, and file inventory above.
- Interpretations (labeled as such): 3B-class local models appear
  adequate for schema-valid 3C drafting but unreliable on corpus-ID
  fidelity; full-context 3E/3F is infeasible in this hardware+model
  combination; no statement is made about local deployment feasibility
  for the complete AEGIS workflow, edge suitability, or any untested
  model/hardware pairing.
