"""Phase 2A Part A - Deterministic experimental subset selection.

Reads the Phase 1 inventory and selects a fixed per-category subset using
stable sorting by video_id (first N per category), so the same inventory +
config always yields the same subset. Videos stay external; only inventory
metadata + relative paths are stored.

Usage:
    python -m src.pipeline.select_subset [--config PATH] [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def load_inventory_records(inventory_path: Path) -> list:
    with Path(inventory_path).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "records" in data:
        return data["records"]
    return data


def select_subset(records: list, selection: list) -> list:
    """Deterministically pick the first N records per category by video_id.

    selection: [{"category": str, "count": int}, ...]. Raises ValueError if
    any category has too few candidates.
    """
    by_category: dict = {}
    for record in records:
        by_category.setdefault(record.get("category", "Unknown"), []).append(record)
    selected = []
    for spec in selection:
        category = spec["category"]
        count = int(spec["count"])
        candidates = sorted(by_category.get(category, []), key=lambda r: r["video_id"])
        if len(candidates) < count:
            raise ValueError(
                f"category {category!r}: need {count}, only {len(candidates)} available"
            )
        selected.extend(candidates[:count])
    return selected


def to_subset_entries(records: list) -> list:
    """Project inventory records onto subset entries with ground-truth naming."""
    entries = []
    for record in records:
        entries.append(
            {
                "video_id": record["video_id"],
                "source_type": record["source_type"],
                "ground_truth_category": record["category"],
                "dataset_root": record.get("dataset_root"),
                "path": record["path"],
                "duration_seconds": record.get("duration_seconds"),
                "fps": record.get("fps"),
                "width": record.get("width"),
                "height": record.get("height"),
                "frame_count": record.get("frame_count"),
                "file_size_bytes": record.get("file_size_bytes"),
                "format": record.get("format"),
            }
        )
    return entries


def validate_subset(entries: list, selection: list) -> dict:
    """Check total and per-category counts; return {category: count}."""
    expected = {spec["category"]: int(spec["count"]) for spec in selection}
    actual: dict = {}
    for entry in entries:
        actual[entry["ground_truth_category"]] = (
            actual.get(entry["ground_truth_category"], 0) + 1
        )
    if actual != expected:
        raise ValueError(f"subset mismatch: expected {expected}, got {actual}")
    if len(entries) != sum(expected.values()):
        raise ValueError(f"subset size {len(entries)} != {sum(expected.values())}")
    if len({e["video_id"] for e in entries}) != len(entries):
        raise ValueError("duplicate video_id in subset")
    return actual


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2A: select deterministic subset")
    parser.add_argument("--config", default=None, help="path to a config file")
    parser.add_argument("--output", default=None, help="override subset output path")
    args = parser.parse_args(argv)

    from src.settings import load_config

    try:
        config = load_config(args.config)
    except Exception as exc:  # noqa: BLE001 - CLI reports config errors plainly
        print(f"Config error: {exc}")
        return 2

    subset_cfg = (config.get("experiments") or {}).get("phase2_subset") or {}
    selection = subset_cfg.get("selection", [])
    if not selection:
        print("Config error: experiments.phase2_subset.selection is empty")
        return 2
    inventory_path = PROJECT_ROOT / subset_cfg.get("inventory_file", "data/inventory/videos.json")
    if not inventory_path.exists():
        print(f"Inventory not found: {inventory_path} (run Phase 1 first)")
        return 2
    output_path = Path(args.output) if args.output else PROJECT_ROOT / subset_cfg.get(
        "output", "data/experiments/phase2_subset.json"
    )

    records = load_inventory_records(inventory_path)
    print(f"Inventory records: {len(records)}")
    try:
        selected = select_subset(records, selection)
        entries = to_subset_entries(selected)
        counts = validate_subset(entries, selection)
    except ValueError as exc:
        print(f"Subset error: {exc}")
        return 2

    payload = {
        "created_from": str(inventory_path),
        "selection": selection,
        "counts": counts,
        "total": len(entries),
        "videos": sorted(entries, key=lambda e: e["video_id"]),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    print(f"Selected {len(entries)} videos -> {output_path}")
    for category, count in counts.items():
        print(f"  {category}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())