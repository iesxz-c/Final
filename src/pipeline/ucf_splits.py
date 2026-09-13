"""Phase 2C - Official UCF-Crime Action Recognition split handling.

Parses the official Action_Regnition_splits/*.txt files (never random
splits), maps the 14 classes (13 anomaly + Normal), resolves references to
local paths, and reports missing files / train-test overlap.

Split line format: `<Class>/<file>.mp4` for anomalies,
`Normal_Videos_event/<file>.mp4` for normals. Ground-truth folder labels
are training targets here (fine-tuning), which is distinct from Phase 2B,
where folder names must never become model outputs.

Usage:
    python -m src.pipeline.ucf_splits --split 002 [--anomaly-root P] [--normal-root P]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Fixed 14-class label space, in split-file appearance order. Normal last.
CLASS_NAMES = [
    "Abuse", "Arrest", "Arson", "Assault", "Burglary", "Explosion",
    "Fighting", "RoadAccidents", "Robbery", "Shooting", "Shoplifting",
    "Stealing", "Vandalism", "Normal",
]
LABEL_TO_INDEX = {name: i for i, name in enumerate(CLASS_NAMES)}
NORMAL_SPLIT_DIR = "Normal_Videos_event"


def split_class_to_label(split_class: str) -> str:
    """Map a split-file directory name to a label (never touches inference)."""
    if split_class == NORMAL_SPLIT_DIR:
        return "Normal"
    if split_class not in LABEL_TO_INDEX:
        raise ValueError(f"unknown split class: {split_class!r}")
    return split_class


def parse_split_file(path: str | Path) -> list:
    """Parse one split file into [(reference, label)] preserving file order."""
    entries = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            split_class, filename = line.split("/", 1)
            entries.append((line, split_class_to_label(split_class)))
    return entries


def resolve_video_path(anomaly_root: Path, normal_root: Path, reference: str) -> Path:
    """Resolve a split reference to a local path (OS-independent)."""
    split_class, filename = reference.split("/", 1)
    if split_class == NORMAL_SPLIT_DIR:
        return Path(normal_root) / filename
    return Path(anomaly_root) / split_class / filename


def find_missing(anomaly_root: Path, normal_root: Path, references: list) -> list:
    """Return references whose files are absent locally."""
    return [r for r in references if not resolve_video_path(anomaly_root, normal_root, r).is_file()]


def check_overlap(train_refs: list, test_refs: list) -> list:
    """Return video references present in both train and test (should be empty)."""
    return sorted(set(train_refs).intersection(test_refs))


def load_fold(split_root: Path, split: str) -> tuple:
    """Load (train_entries, test_entries) for a fold like '002'."""
    train = parse_split_file(Path(split_root) / f"train_{split}.txt")
    test = parse_split_file(Path(split_root) / f"test_{split}.txt")
    return train, test


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2C: validate official split files")
    parser.add_argument("--split", default="002")
    parser.add_argument("--config", default=None)
    parser.add_argument("--anomaly-root", default=None)
    parser.add_argument("--normal-root", default=None)
    parser.add_argument("--split-root", default=None)
    args = parser.parse_args(argv)

    from src.settings import dataset_paths, load_config

    config = load_config(args.config)
    paths = dataset_paths(config)
    anomaly_root = Path(args.anomaly_root) if args.anomaly_root else paths["anomaly_videos"]
    normal_root = Path(args.normal_root) if args.normal_root else paths["normal_videos"]
    split_root = Path(args.split_root) if args.split_root else (
        PROJECT_ROOT / "UCF_Crimes-Train-Test-Split" / "Action_Regnition_splits")

    train, test = load_fold(split_root, args.split)
    train_refs = [r for (r, _) in train]
    test_refs = [r for (r, _) in test]
    train_missing = find_missing(anomaly_root, normal_root, train_refs)
    test_missing = find_missing(anomaly_root, normal_root, test_refs)
    overlap = check_overlap(train_refs, test_refs)

    print(f"Fold {args.split}: train={len(train)} (effective {len(train) - len(train_missing)}), "
          f"test={len(test)} (effective {len(test) - len(test_missing)})")
    print(f"  train/test overlap: {len(overlap)}")
    print(f"  missing train ({len(train_missing)}): {train_missing}")
    print(f"  missing test ({len(test_missing)}): {test_missing}")
    return 0 if not overlap else 2


if __name__ == "__main__":
    sys.exit(main())
