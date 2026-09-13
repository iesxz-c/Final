"""Package the Phase 2B Colab run: the 40 subset videos + inventory.

Reads data/experiments/phase2_subset.json and zips the referenced videos
(read-only; dataset stays untouched) under dataset/anomaly/... and
dataset/normal/..., plus the Phase 1 inventory. On Colab, re-running
select_subset with the dataset env vars reproduces the same 40 video_ids.

Usage:
    python scripts/make_colab_package.py [--output ../colab_phase2b.zip]
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Zip the 40-video Colab package")
    parser.add_argument("--output", default="../colab_phase2b.zip",
                        help="zip destination (keep outside the repo)")
    parser.add_argument("--subset", default="data/experiments/phase2_subset.json")
    parser.add_argument("--inventory", default="data/inventory/videos.json")
    args = parser.parse_args(argv)

    subset_path = PROJECT_ROOT / args.subset
    inventory_path = PROJECT_ROOT / args.inventory
    if not subset_path.exists():
        print(f"Subset not found: {subset_path} (run select_subset first)")
        return 2
    subset = json.loads(subset_path.read_text(encoding="utf-8"))
    output = Path(args.output)
    if str(PROJECT_ROOT) in str(output.resolve()):
        print("Refusing to write the zip inside the repo (it would bundle videos).")
        return 2

    total = 0
    with zipfile.ZipFile(output, "w", zipfile.ZIP_STORED) as zf:
        zf.write(inventory_path, "inventory/videos.json")
        zf.write(subset_path, "phase2_subset.json")
        for entry in subset["videos"]:
            src = Path(entry["dataset_root"]) / entry["path"]
            if not src.exists():
                print(f"  MISSING: {src}")
                return 2
            arc = f"dataset/{entry['source_type']}/{entry['path']}"
            zf.write(src, arc)
            total += src.stat().st_size
    print(f"Packed {len(subset['videos'])} videos ({round(total / 1e9, 2)} GB) -> {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())