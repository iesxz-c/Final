#!/usr/bin/env bash
# AEGIS local-GPU Colab setup. Run cells top to bottom; stop on any error.
# Pins: llama.cpp b11541 (Ubuntu x64 CUDA 12.8) + Qwen2.5-3B-Instruct Q4_K_M.
# Robust to: tarball subdirectory layouts, occupied ports (8080/8081/8082).
set -euo pipefail

LLAMA_TAG="b11541"
LLAMA_URL="https://github.com/ggml-org/llama.cpp/releases/download/${LLAMA_TAG}/llama-${LLAMA_TAG}-bin-ubuntu-cuda-12.8-x64.tar.gz"
CUDART_URL="https://github.com/ggml-org/llama.cpp/releases/download/${LLAMA_TAG}/cudart-llama-${LLAMA_TAG}-bin-ubuntu-cuda-12.8-x64.tar.gz"
MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
# Recorded integrity values (local CPU track, Get-FileHash SHA256).
MODEL_SHA256="626B4A6678B86442240E33DF819E00132D3BA7DDDFE1CDC4FBB18E0A9615C62D"
MODEL_BYTES="2104932768"
WORK="${AEGIS_COLAB_WORK:-/content/aegis-colab-gpu}"

echo "== GPU check (must show Tesla T4 + CUDA) =="
nvidia-smi
python3 -c "import torch; print('torch', torch.__version__, 'cuda:', torch.cuda.is_available())"

mkdir -p "${WORK}/bin" "${WORK}/models" "${WORK}/logs" "${WORK}/results"
cd "${WORK}"

SRV="$(find bin -name llama-server -type f 2>/dev/null | head -1 || true)"
if [ -z "${SRV}" ]; then
  echo "== downloading llama.cpp ${LLAMA_TAG} (CUDA 12.8 build) =="
  curl -L --fail --retry 3 -o /tmp/llama.tgz "${LLAMA_URL}"
  tar -xzf /tmp/llama.tgz -C bin/
  echo "== downloading cudart libs =="
  curl -L --fail --retry 3 -o /tmp/cudart.tgz "${CUDART_URL}"
  tar -xzf /tmp/cudart.tgz -C bin/
  SRV="$(find bin -name llama-server -type f | head -1)"
fi
SRVDIR="$(dirname "${SRV}")"
CUDARTDIR="$(dirname "$(find bin -name 'libcudart.so*' | head -1)")"
export LD_LIBRARY_PATH="${SRVDIR}:${CUDARTDIR}:${LD_LIBRARY_PATH:-}"
echo "server binary: ${SRV}"
"${SRV}" --version

if [ ! -f models/qwen2.5-3b-instruct-q4_k_m.gguf ]; then
  echo "== downloading model (~2.1 GB, qwen-research license) =="
  curl -L --fail --retry 3 -o models/qwen2.5-3b-instruct-q4_k_m.gguf "${MODEL_URL}"
fi
echo "== verifying model =="
BYTES="$(stat -c%s models/qwen2.5-3b-instruct-q4_k_m.gguf)"
test "${BYTES}" = "${MODEL_BYTES}" || { echo "SIZE MISMATCH: ${BYTES}"; exit 1; }
echo "${MODEL_SHA256}  models/qwen2.5-3b-instruct-q4_k_m.gguf" | sha256sum -c -
echo "model integrity OK"

# Colab squatters accept-and-reject on 8080, which defeats curl probes:
# default to 8081 (override with AEGIS_PORT). The runner cells read the
# effective port from logs/server.port, so no other change is needed.
PORT="${AEGIS_PORT:-8081}"
echo "${PORT}" > logs/server.port
echo "selected port: ${PORT}"

echo "== starting server on 127.0.0.1:${PORT} (native 32k context) =="
nohup "${SRV}" -m models/qwen2.5-3b-instruct-q4_k_m.gguf \
  --host 127.0.0.1 --port "${PORT}" -c 32768 -t 8 \
  --log-file logs/server-colab.log > logs/server-colab.out.log 2>&1 &
echo $! > logs/server.pid
for i in $(seq 1 30); do
  if curl -sf --max-time 10 "http://127.0.0.1:${PORT}/health" >/dev/null; then
    echo "server healthy on port ${PORT}"
    break
  fi
  sleep 10
  if [ "$i" = "30" ]; then echo "SERVER FAILED TO START"; exit 1; fi
done
echo "SETUP COMPLETE. Work dir: ${WORK}. Server URL: http://127.0.0.1:${PORT}"
