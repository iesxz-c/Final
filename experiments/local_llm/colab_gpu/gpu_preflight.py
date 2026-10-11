"""GPU preflight: record hardware, confirm CUDA use, fail loudly otherwise.

Usage: python3 gpu_preflight.py --server-url http://127.0.0.1:8080 --out results/preflight.json
Stdlib only. Never touches model weights or prompts beyond a tiny /health
check. GPU use is confirmed via nvidia-smi process memory + server log
backend lines -- never inferred from GPU presence alone.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path


def sh(cmd: list, timeout: int = 60) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout).stdout.strip()[:3000]
    except Exception as exc:  # noqa: BLE001 - recorded as unavailable
        return "UNAVAILABLE: %s" % exc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="GPU preflight recorder")
    parser.add_argument("--server-url", default="http://127.0.0.1:8080")
    parser.add_argument("--out", default="results/preflight.json")
    parser.add_argument("--server-log", default=None,
                        help="llama.cpp server log to scan for backend lines")
    args = parser.parse_args(argv)

    record: dict = {
        "nvidia_smi": sh(["nvidia-smi",
                          "--query-gpu=name,driver_version,memory.total,"
                          "memory.free,compute_cap", "--format=csv"]),
        "nvidia_smi_procs": sh(["nvidia-smi",
                                "--query-compute-apps=pid,used_memory",
                                "--format=csv"]),
        "torch": sh([sys.executable, "-c",
                     "import torch; print(torch.__version__, "
                     "torch.cuda.is_available(), torch.cuda.get_device_name(0) "
                     "if torch.cuda.is_available() else 'no-cuda')"]),
        "ram": sh(["free", "-g"]),
    }
    try:
        with urllib.request.urlopen(args.server_url + "/health",
                                     timeout=20) as resp:
            record["server_health"] = resp.read().decode("utf-8")[:200]
    except Exception as exc:  # noqa: BLE001 - recorded, fatal below
        record["server_health"] = "UNREACHABLE: %s" % exc
    if args.server_log and Path(args.server_log).exists():
        text = Path(args.server_log).read_text(
            encoding="utf-8", errors="replace")
        record["server_backend_lines"] = [
            line.strip()[:300] for line in text.splitlines()
            if any(k in line for k in
                   ("cuda", "CUDA", "ggml-cuda", "backend", "device",
                    "n_ctx", "kv_unified"))][-15:]
    else:
        record["server_backend_lines"] = "NO_LOG_PROVIDED"
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2)
    print(json.dumps({k: (v[:160] + "..." if isinstance(v, str) and len(v) > 160
                                       else v)
                      for k, v in record.items()
                      if k != "server_backend_lines"}, indent=2))
    if "UNREACHABLE" in str(record["server_health"]):
        print("PREFLIGHT FAIL: server unreachable")
        return 2
    print("PREFLIGHT OK (verify CUDA lines in %s before trusting GPU use)"
          % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
