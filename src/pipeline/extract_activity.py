"""Phase 2B - Temporal activity evidence extraction.

Runs the existing 40-video Phase 2 subset through a sliding-window activity
model (pretrained VideoMAE-Base/Kinetics-400) and writes ActivityObservation
records plus a run manifest. Independent stream from Phase 2A objects.

Usage:
    python -m src.pipeline.extract_activity [--config PATH] [--subset PATH]
        [--output-dir DIR] [--limit-videos N] [--max-windows N]
        [--device auto|cpu|cuda]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.evidence.models import EVIDENCE_SCHEMA_VERSION, VideoRecord
from src.pipeline.activity import (
    MODEL_ID,
    iter_window_frames,
    to_activity_observation,
    window_timestamps,
)
from src.pipeline.extract_evidence import open_capture, resolve_video_fps


def extract_video_activity(video: VideoRecord, model, num_frames: int,
                           sampling_fps: float, window_hop: int, top_k: int,
                           max_windows: int | None = None) -> dict:
    """Run windowed activity inference over one video, streaming."""
    capture = open_capture(video.absolute_path())
    try:
        video_fps = resolve_video_fps(capture, video)
        activities: list = []
        windows = 0
        for window_index, indices, frames_bgr, padded in iter_window_frames(
            capture, video_fps, num_frames, sampling_fps, window_hop
        ):
            if max_windows is not None and windows >= max_windows:
                break
            prediction = model.predict(frames_bgr, top_k)  # BGR; backend converts
            start_time, end_time = window_timestamps(indices, video_fps)
            activities.append(
                to_activity_observation(
                    video.video_id, window_index, indices, start_time, end_time,
                    prediction, model.model_name, model.model_version, padded,
                )
            )
            windows += 1
        return {"activities": activities, "windows": windows, "video_fps": video_fps}
    finally:
        capture.release()


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2B: windowed activity inference")
    parser.add_argument("--config", default=None)
    parser.add_argument("--subset", default=None, help="override subset json path")
    parser.add_argument("--output-dir", default=None, help="override evidence output dir")
    parser.add_argument("--limit-videos", type=int, default=None, help="debug: cap videos")
    parser.add_argument("--max-windows", type=int, default=None,
                        help="debug: cap windows per video")
    parser.add_argument("--device", default=None, help="override device (auto|cpu|cuda)")
    args = parser.parse_args(argv)

    from src.settings import load_config

    try:
        config = load_config(args.config)
    except Exception as exc:  # noqa: BLE001 - CLI reports config errors plainly
        print(f"Config error: {exc}")
        return 2

    subset_cfg = (config.get("experiments") or {}).get("phase2_subset") or {}
    subset_path = Path(args.subset) if args.subset else PROJECT_ROOT / subset_cfg.get(
        "output", "data/experiments/phase2_subset.json"
    )
    if not subset_path.exists():
        print(f"Subset not found: {subset_path} (run select_subset first)")
        return 2
    activity_cfg = config.get("activity_model") or {}
    model_id = activity_cfg.get("name", MODEL_ID)
    num_frames = int(activity_cfg.get("num_frames", 16))
    sampling_fps = float(activity_cfg.get("sampling_fps", 8.0))
    window_hop = int(activity_cfg.get("window_hop", num_frames))
    top_k = int(activity_cfg.get("top_k", 5))
    device = args.device or activity_cfg.get("device", "auto")
    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / activity_cfg.get(
        "output_dir", "data/evidence/phase2b"
    )

    with subset_path.open("r", encoding="utf-8") as fh:
        subset = json.load(fh)
    videos = [VideoRecord.from_dict(v) for v in subset["videos"]]
    if args.limit_videos is not None:
        videos = videos[: args.limit_videos]

    from src.pipeline.activity import VideoMAEActivityModel

    try:
        model = VideoMAEActivityModel(model_id, device)
    except Exception as exc:  # noqa: BLE001 - missing weights/libs reported plainly
        print(f"Activity model error: {exc}")
        return 2
    print(f"Activity model: {model.model_name} on {model.device} "
          f"({num_frames} frames @ {sampling_fps}fps, top-{top_k})")

    started = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    all_activities: list = []
    failures: list = []
    processed = 0
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] {video.video_id}")
        try:
            result = extract_video_activity(
                video, model, num_frames, sampling_fps, window_hop, top_k,
                args.max_windows,
            )
            all_activities.extend(result["activities"])
            processed += 1
            print(f"  {result['windows']} windows (video {result['video_fps']:.2f}fps)")
        except Exception as exc:  # noqa: BLE001 - one bad video must not stop the run
            failures.append({"video_id": video.video_id, "error": str(exc)[:300]})
            print(f"  FAILED: {exc}")
    model.close()
    elapsed = round(time.perf_counter() - t0, 1)

    all_activities.sort(key=lambda a: (a.video_id, a.start_time))
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "videos.json", [v.to_dict() for v in videos])
    _write_json(output_dir / "activities.json", [a.to_dict() for a in all_activities])
    manifest = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "subset": str(subset_path),
        "model": {
            "name": model.model_name,
            "version": model.model_version,
            "weight_notes": getattr(model, "weight_notes", ""),
            "num_frames": num_frames,
            "sampling_fps": sampling_fps,
            "window_hop": window_hop,
            "top_k": top_k,
            "device_requested": device,
            "device_used": model.device,
        },
        "started_utc": started,
        "elapsed_seconds": elapsed,
        "videos_selected": len(videos),
        "videos_processed": processed,
        "videos_failed": len(failures),
        "activities": len(all_activities),
        "failures": failures,
    }
    _write_json(output_dir / "manifest.json", manifest)

    print(f"\nWrote {len(videos)} videos, {len(all_activities)} activities "
          f"-> {output_dir} in {elapsed}s")
    if failures:
        print(f"Failures: {len(failures)}")
        for failure in failures:
            print(f"  {failure['video_id']}: {failure['error']}")
    return 0


def _write_json(path: Path, payload) -> None:
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


if __name__ == "__main__":
    sys.exit(main())