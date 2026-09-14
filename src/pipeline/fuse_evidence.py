"""Phase 2D - Evidence fusion CLI (no inference; reads existing outputs).

Reads the three frozen evidence streams plus subset video metadata and
writes timestamp-aligned fused evidence:

    python -m src.pipeline.fuse_evidence [--phase2 DIR] [--phase2b DIR]
        [--phase2c DIR] [--output-dir DIR] [--max-gap-seconds F]

A missing source file is treated as an empty source (recorded in the
manifest); the run only fails when no source evidence exists at all.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.evidence.fusion import (
    FUSION_SCHEMA_VERSION,
    NORMAL_LABELS,
    RECORD_AGREEMENT_WEIGHT,
    RECORD_EVENT_WEIGHT,
    RECORD_PRESENCE_WEIGHT,
    VIDEO_AGREEMENT_WEIGHT,
    VIDEO_CONCENTRATION_SATURATION_RECORDS,
    VIDEO_CONCENTRATION_WEIGHT,
    VIDEO_PERSISTENCE_SATURATION_SECONDS,
    VIDEO_PERSISTENCE_WEIGHT,
    VIDEO_STRENGTH_WEIGHT,
    fuse_all,
)

DEFAULT_PHASE2_DIR = "data/evidence/phase2"
DEFAULT_PHASE2B_DIR = "data/evidence/phase2b"
DEFAULT_PHASE2C_DIR = "data/evidence/phase2c_ucf"
DEFAULT_OUTPUT_DIR = "data/evidence/fused"
DEFAULT_SUBSET = "data/experiments/phase2_subset.json"


def _read_list(path: Path) -> tuple:
    """Returns (records, missing_flag). Missing file -> ([], True)."""
    if not path.exists():
        return [], True
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"expected a JSON list: {path}")
    return data, False


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2D: fuse evidence streams")
    parser.add_argument("--phase2", default=None)
    parser.add_argument("--phase2b", default=None)
    parser.add_argument("--phase2c", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--subset", default=None,
                        help="subset json defining the video universe")
    parser.add_argument("--max-gap-seconds", type=float, default=1.0)
    args = parser.parse_args(argv)

    phase2 = Path(args.phase2) if args.phase2 else PROJECT_ROOT / DEFAULT_PHASE2_DIR
    phase2b = Path(args.phase2b) if args.phase2b else PROJECT_ROOT / DEFAULT_PHASE2B_DIR
    phase2c = Path(args.phase2c) if args.phase2c else PROJECT_ROOT / DEFAULT_PHASE2C_DIR
    output_dir = (Path(args.output_dir) if args.output_dir
                  else PROJECT_ROOT / DEFAULT_OUTPUT_DIR)
    subset_path = Path(args.subset) if args.subset else PROJECT_ROOT / DEFAULT_SUBSET

    detections, miss_det = _read_list(phase2 / "detections.json")
    activities, miss_act = _read_list(phase2b / "activities.json")
    events, miss_evt = _read_list(phase2c / "ucf_events.json")
    missing = {"phase2_detections": miss_det, "phase2b_activities": miss_act,
               "phase2c_events": miss_evt}
    for name, was_missing in missing.items():
        if was_missing:
            print(f"WARNING: {name} not found; treating as empty source")

    if subset_path.exists():
        with subset_path.open("r", encoding="utf-8") as fh:
            video_ids = sorted(v["video_id"] for v in json.load(fh)["videos"])
    else:
        print(f"WARNING: subset not found ({subset_path}); "
              "video universe = union of source video_ids")
        video_ids = sorted({o.get("video_id") for o in detections + activities + events
                            if o.get("video_id")})

    if not detections and not activities and not events:
        print("No source evidence found; nothing to fuse")
        return 2

    started = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    result = fuse_all(video_ids, activities, events, detections,
                      max_gap_seconds=args.max_gap_seconds)
    elapsed = round(time.perf_counter() - t0, 1)

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "evidence.json",
                [r.to_dict() for r in result["records"]])
    _write_json(output_dir / "incidents.json",
                [i.to_dict() for i in result["incidents"]])
    _write_json(output_dir / "video_scores.json",
                [s.to_dict() for s in result["scores"]])
    manifest = {
        "schema_version": FUSION_SCHEMA_VERSION,
        "inputs": {
            "phase2_detections": str(phase2 / "detections.json"),
            "phase2b_activities": str(phase2b / "activities.json"),
            "phase2c_events": str(phase2c / "ucf_events.json"),
            "subset": str(subset_path),
        },
        "missing_sources": [k for k, v in missing.items() if v],
        "videos": len(video_ids),
        "observations": {
            "yolo_detections": len(detections),
            "kinetics_activities": len(activities),
            "ucf_events": len(events),
        },
        "fused_records": len(result["records"]),
        "incident_regions": len(result["incidents"]),
        "unaligned_detections": result["unaligned_detections"],
        "scoring": {
            "record": (f"min(1, {RECORD_EVENT_WEIGHT}*E + "
                       f"{RECORD_PRESENCE_WEIGHT}*has_action + "
                       f"{RECORD_PRESENCE_WEIGHT}*has_object + "
                       f"{RECORD_AGREEMENT_WEIGHT}*(num_types-1)); "
                       "E = max non-normal UCF hypothesis confidence"),
            "video": (f"min(1, {VIDEO_STRENGTH_WEIGHT}*strength + "
                      f"{VIDEO_PERSISTENCE_WEIGHT}*persistence + "
                      f"{VIDEO_CONCENTRATION_WEIGHT}*concentration + "
                      f"{VIDEO_AGREEMENT_WEIGHT}*agreement); "
                      f"persistence saturates at "
                      f"{VIDEO_PERSISTENCE_SATURATION_SECONDS}s, concentration at "
                      f"{VIDEO_CONCENTRATION_SATURATION_RECORDS} records"),
            "normal_labels": sorted(NORMAL_LABELS),
            "max_gap_seconds": args.max_gap_seconds,
            "note": "evidence aggregation only; NOT a probability of crime",
        },
        "started_utc": started,
        "elapsed_seconds": elapsed,
    }
    _write_json(output_dir / "manifest.json", manifest)

    print(f"\nFused {len(video_ids)} videos: {len(detections)} detections + "
          f"{len(activities)} activities + {len(events)} events -> "
          f"{len(result['records'])} records, {len(result['incidents'])} "
          f"incidents in {elapsed}s -> {output_dir}")
    top = sorted(result["scores"], key=lambda s: s.score, reverse=True)[:3]
    print("Top video scores:")
    for score in top:
        print(f"  {score.video_id}: {score.score} {score.components}")
    return 0


def _write_json(path: Path, payload) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


if __name__ == "__main__":
    sys.exit(main())
