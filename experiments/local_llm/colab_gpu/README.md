# AEGIS local-GPU experiment (Colab, T4)

Isolated track. Production code, prompts, schemas, validators, locked
artifacts, and the external Meta integration are never touched. No
external API calls; runners refuse to start if `MODEL_API_KEY` is set.
No evidence truncation: oversized inputs are recorded, never cut.

## What is measured
Qwen2.5-3B-Instruct Q4_K_M (official Qwen org, qwen-research license) on
a Colab Tesla T4: 3C benchmark (10 frozen questions), evidence-backed 3E
on 8 vendored frozen `result_3d` inputs (all fit native 32k context;
larger cases were excluded, see below), optional end-to-end on I28.

## Cell 0 — GPU runtime
Runtime > Change runtime type > **T4 GPU**, then:
```
nvidia-smi
python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```
Both must show CUDA. If no GPU, stop here.

## Cell 1 — clone this branch
```
git clone --branch experiment/aegis-colab-gpu https://github.com/iesxz-c/Final.git aegis
cd aegis/experiments/local_llm/colab_gpu
```

## Cell 2 — setup (downloads pinned binary + model, verifies, starts server)
```
export AEGIS_COLAB_WORK=/content/aegis-colab-gpu
bash colab_setup.sh
```
This downloads llama.cpp b11541 (Ubuntu x64 **CUDA 12.8** build +
cudart libs) and `qwen2.5-3b-instruct-q4_k_m.gguf` (~2.1 GB), verifies
byte size + SHA256 (`626B4A66…5C62D`, recorded in the script), and
starts `llama-server` on **127.0.0.1:8080** with native 32k context.
If `nvidia-smi` shows CUDA 13, replace the two URLs with the
`cuda-13.4` assets from the same release tag and rerun. No `pip install`
is required (runners are stdlib-only); `requirements-colab.txt` lists
only the optional `huggingface-hub` alternate download path.

## Cell 3 — preflight (proves GPU use, not just presence)
```
python3 gpu_preflight.py --server-url http://127.0.0.1:8080 \
  --server-log /content/aegis-colab-gpu/logs/server-colab.log \
  --out results/preflight.json
```
Check `results/preflight.json`: `nvidia-smi` must list the T4 with the
server process holding VRAM, and `server_backend_lines` must show CUDA
backend init. If either is missing, do not proceed.

## Cell 4 — 3C benchmark (10 cases, ~5 min)
```
python3 run_3c_bench.py --server-url http://127.0.0.1:8080 \
  --inputs inputs --results results/bench_3c
```

## Cell 5 — evidence-backed 3E (8 cases: I03 I19 I23 I24 I27 I28 I29 I30)
```
python3 run_3e_evidence.py --server-url http://127.0.0.1:8080 \
  --inputs inputs --results results/stage_3e
```
Excluded as oversized-for-design (documented, not run): every other
case exceeds ~60k prompt chars and risks the 32k slot cap; the runner
enforces `--max-prompt-chars 100000` and records oversize honestly.

## Cell 6 — optional end-to-end (needs corpus upload)
```
# upload data/data_155n/fused_155/evidence.json (35.9 MB) + incidents.json,
# e.g. from Drive, then:
python3 run_full.py --server-url http://127.0.0.1:8080 --inputs inputs \
  --results results/full --evidence /content/evidence.json \
  --incidents /content/incidents.json --cases I28
```
Without `--evidence/--incidents` the runner records an honest skip.

## Cell 7 — summarize + stop server
```
python3 summarize.py --results results --report results/REPORT.md \
  --out-csv results/summary.csv
kill $(cat /content/aegis-colab-gpu/logs/server.pid)
```

## Troubleshooting
- Server won't start: check `logs/server-colab*.log`; CUDA-12.8 vs driver
  mismatch -> use the cuda-13.4 assets (same tag).
- OOM on T4 (15 GB; model needs ~3 GB): lower `-c` is NOT permitted for
  3E inputs (would truncate evidence) — instead drop large cases.
- HTTP 400 "exceeds available context": expected for oversized inputs;
  it is a recorded result, not a bug. Do not raise `--max-prompt-chars`
  past native context.
- Any `MODEL_API_KEY` in env: runners refuse to start by design.

## Reproducibility
Branch `experiment/aegis-colab-gpu`, pinned binary/model/SHA, frozen
vendored inputs under `inputs/`, per-run JSONL under `results/`.
Sample sizes are small by design; no significance claims.
