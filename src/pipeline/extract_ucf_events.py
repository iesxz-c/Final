"""Phase 2C (pretrained track) - UCF-Crime surveillance-event extraction.

Runs the SAME 40-video Phase 2B subset through the SAME 16-frame temporal
windows, but classifies each window with the pretrained UCF-Crime VideoMAE
(OPear/videomae-large-finetuned-UCF-Crime, inference only) instead of the
Kinetics model. Outputs are UCFEventObservation records ("surveillance
events"), kept separate from Kinetics ActivityObservations so the two
streams can later be compared window-for-window.

Usage:
    python -m src.pipeline.extract_ucf_events [--input-manifest PATH]
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
    UCF_EVENT_MODEL_ID,
    iter_window_frames,
    to_ucf_event_observation,
    window_timestamps,
)
from src.pipeline.extract_evidence import open_capture, resolve_video_fps

DEFAULT_SUBSET = "data/experiments/phase2_subset.json"
DEFAULT_OUTPUT_DIR = "data/evidence/phase2c_ucf"
NUM_FRAMES = 16
SAMPLING_FPS = 8.0
WINDOW_HOP = 16
TOP_K = 5


def extract_video_events(video: VideoRecord, model, num_frames: int,
                         sampling_fps: float, window_hop: int, top_k: int,
                         max_windows: int | None = None) -> dict:
    """Run windowed surveillance-event inference over one video, streaming."""
    capture = open_capture(video.absolute_path())
    try:
        video_fps = resolve_video_fps(capture, video)
        events: list = []
        windows = 0
        for window_index, indices, frames_bgr, padded in iter_window_frames(
            capture, video_fps, num_frames, sampling_fps, window_hop
        ):
            if max_windows is not None and windows >= max_windows:
                break
            prediction = model.predict(frames_bgr, top_k)  # BGR; backend converts
            start_time, end_time = window_timestamps(indices, video_fps)
            events.append(
                to_ucf_event_observation(
                    video.video_id, window_index, indices, start_time, end_time,
                    prediction, model.model_name, model.model_version, padded,
                )
            )
            windows += 1
        return {"events": events, "windows": windows, "video_fps": video_fps}
    finally:
        capture.release()


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2C: UCF-Crime event inference")
    parser.add_argument("--input-manifest", default=None,
                        help="subset json with a 'videos' list")
    parser.add_argument("--output-dir", default=None, help="override evidence output dir")
    parser.add_argument("--limit-videos", type=int, default=None, help="debug: cap videos")
    parser.add_argument("--max-windows", type=int, default=None,
                        help="debug: cap windows per video")
    parser.add_argument("--device", default="auto", help="override device (auto|cpu|cuda)")
    args = parser.parse_args(argv)

    subset_path = Path(args.input_manifest) if args.input_manifest else PROJECT_ROOT / DEFAULT_SUBSET
    if not subset_path.exists():
        print(f"Subset not found: {subset_path} (run select_subset first)")
        return 2
    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / DEFAULT_OUTPUT_DIR

    with subset_path.open("r", encoding="utf-8") as fh:
        subset = json.load(fh)
    if "videos" not in subset:
        print(f"Input has no 'videos' list: {subset_path}")
        return 2
    videos = [VideoRecord.from_dict(v) for v in subset["videos"]]
    if args.limit_videos is not None:
        videos = videos[: args.limit_videos]

    from src.pipeline.activity import UCFEventModel

    try:
        model = UCFEventModel(UCF_EVENT_MODEL_ID, args.device)
    except Exception as exc:  # noqa: BLE001 - missing weights/libs reported plainly
        print(f"Event model error: {exc}")
        return 2
    try:
        resolution = model.processor.crop_size.get("height", 224) \
            if isinstance(getattr(model.processor, "crop_size", None), dict) else 224
    except Exception:  # noqa: BLE001 - metadata only, never fail the run
        resolution = 224
    print(f"Event model: {model.model_name} ({model.model_version}) on {model.device} "
          f"({NUM_FRAMES} frames @ {SAMPLING_FPS}fps, top-{TOP_K})")

    started = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    all_events: list = []
    failures: list = []
    processed = 0
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] {video.video_id}")
        try:
            result = extract_video_events(
                video, model, NUM_FRAMES, SAMPLING_FPS, WINDOW_HOP, TOP_K,
                args.max_windows,
            )
            all_events.extend(result["events"])
            processed += 1
            print(f"  {result['windows']} windows (video {result['video_fps']:.2f}fps)")
        except Exception as exc:  # noqa: BLE001 - one bad video must not stop the run
            failures.append({"video_id": video.video_id, "error": str(exc)[:300]})
            print(f"  FAILED: {exc}")
    model.close()
    elapsed = round(time.perf_counter() - t0, 1)

    all_events.sort(key=lambda e: (e.video_id, e.start_time))
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "videos.json", [v.to_dict() for v in videos])
    _write_json(output_dir / "ucf_events.json", [e.to_dict() for e in all_events])
    manifest = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "subset": str(subset_path),
        "model": {
            "name": model.model_name,
            "version": model.model_version,
            "weight_notes": getattr(model, "weight_notes", ""),
            "num_frames": NUM_FRAMES,
            "input_resolution": resolution,
            "sampling_fps": SAMPLING_FPS,
            "window_hop": WINDOW_HOP,
            "top_k": TOP_K,
            "device_requested": args.device,
            "device_used": model.device,
        },
        "started_utc": started,
        "elapsed_seconds": elapsed,
        "videos_selected": len(videos),
        "videos_processed": processed,
        "videos_failed": len(failures),
        "observations": len(all_events),
        "failures": failures,
    }
    _write_json(output_dir / "manifest.json", manifest)

    print(f"\nWrote {len(videos)} videos, {len(all_events)} surveillance events "
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
