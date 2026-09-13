"""Phase 2A Parts B/C/E - Frame sampling + object evidence extraction.

Streams each subset video sequentially (never loads a whole video), samples
frames at a configurable rate with original timestamps, runs a pretrained
detector, and writes videos/observations/detections JSON plus a run manifest.

Usage:
    python -m src.pipeline.extract_evidence [--config PATH] [--subset PATH]
        [--output-dir DIR] [--limit-videos N] [--max-frames N]
        [--save-frames N] [--device cpu|cuda] [--skip-detection]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.evidence.models import (
    EVIDENCE_SCHEMA_VERSION,
    FrameObservation,
    ObjectDetection,
    VideoRecord,
    frame_timestamp_seconds,
    observation_source_reference,
)


# ---------------------------------------------------------------------------
# Sampling (pure helpers are unit-testable without video files)
# ---------------------------------------------------------------------------
def sampling_step(video_fps: float, target_fps: float) -> int:
    """Frame stride for the target sampling rate (every step-th frame)."""
    if video_fps is None or video_fps <= 0:
        raise ValueError(f"invalid video_fps: {video_fps}")
    if target_fps is None or target_fps <= 0:
        raise ValueError(f"invalid target_fps: {target_fps}")
    return max(1, int(round(video_fps / target_fps)))


def iter_sampled_frames(capture, video_fps: float, target_fps: float):
    """Yield (frame_index, timestamp_seconds, frame) sequentially."""
    step = sampling_step(video_fps, target_fps)
    index = 0
    while True:
        ok, frame = capture.read()
        if not ok or frame is None:
            return
        if index % step == 0:
            yield (index, frame_timestamp_seconds(index, video_fps), frame)
        index += 1


def open_capture(path: str):
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("opencv (cv2) is required for sampling") from exc
    capture = cv2.VideoCapture(path)
    if not capture.isOpened():
        raise RuntimeError(f"cannot open video: {path}")
    return capture


def resolve_video_fps(capture, video: VideoRecord) -> float:
    """Effective frame rate for sampling stride and timestamps.

    Prefers inventory metadata (frame_count/duration from parsed container
    boxes); container-reported fps is only trusted when plausible, since
    some files carry bogus headers (e.g. fps=2486).
    """
    if video.frame_count and video.duration_seconds and video.duration_seconds > 0:
        return video.frame_count / video.duration_seconds
    fps = capture.get(7)  # CAP_PROP_FPS without importing cv2 at module level
    if fps is not None and 0 < fps <= 120:
        return float(fps)
    if video.fps is not None and video.fps > 0:
        return float(video.fps)
    raise ValueError("unknown video fps (container and inventory both unusable)")


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------
def extract_video(
    video: VideoRecord,
    detector,
    target_fps: float,
    conf_threshold: float,
    save_frames_budget: int,
    frames_dir: Path | None,
    max_frames: int | None = None,
) -> dict:
    """Sample + detect one video. Returns observations/detections/stats."""
    abs_path = video.absolute_path()
    capture = open_capture(abs_path)
    try:
        video_fps = resolve_video_fps(capture, video)
        observations: list = []
        detections: list = []
        det_index = 0
        saved = 0
        sampled = 0
        for frame_index, timestamp, frame in iter_sampled_frames(capture, video_fps, target_fps):
            if max_frames is not None and sampled >= max_frames:
                break
            sampled += 1
            observation_id = f"{video.video_id}:f{frame_index}"
            observations.append(
                FrameObservation(
                    observation_id=observation_id,
                    video_id=video.video_id,
                    timestamp_seconds=timestamp,
                    frame_index=frame_index,
                    source_reference=observation_source_reference(
                        video.video_id, timestamp, frame_index
                    ),
                    sample_fps=target_fps,
                )
            )
            if detector is not None:
                for det in detector.detect(frame, conf_threshold):
                    detections.append(
                        ObjectDetection(
                            detection_id=f"{observation_id}:d{det_index}",
                            observation_id=observation_id,
                            video_id=video.video_id,
                            timestamp_seconds=timestamp,
                            class_name=det["class_name"],
                            confidence=det["confidence"],
                            bounding_box=det["bounding_box"],
                            model_name=getattr(detector, "model_name", "unknown"),
                            model_conf_threshold=conf_threshold,
                        )
                    )
                    det_index += 1
            if (
                frames_dir is not None
                and saved < save_frames_budget
                and _save_debug_frame(frames_dir, video, frame_index, frame)
            ):
                saved += 1
        return {
            "observations": observations,
            "detections": detections,
            "sampled_frames": sampled,
            "saved_frames": saved,
            "video_fps": video_fps,
        }
    finally:
        capture.release()


def _save_debug_frame(frames_dir: Path, video: VideoRecord, frame_index: int, frame) -> bool:
    try:
        import cv2
    except ImportError:
        return False
    frames_dir.mkdir(parents=True, exist_ok=True)
    stem = video.video_id.replace("/", "_")
    ok = cv2.imwrite(str(frames_dir / f"{stem}_f{frame_index}.jpg"), frame)
    return bool(ok)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2A: sample frames + detect objects")
    parser.add_argument("--config", default=None)
    parser.add_argument("--subset", default=None, help="override subset json path")
    parser.add_argument("--output-dir", default=None, help="override evidence output dir")
    parser.add_argument("--limit-videos", type=int, default=None, help="debug: cap videos")
    parser.add_argument("--max-frames", type=int, default=None,
                        help="debug: cap sampled frames per video")
    parser.add_argument("--save-frames", type=int, default=None,
                        help="override debug stills budget for the run")
    parser.add_argument("--device", default=None, help="override device (cpu|cuda)")
    parser.add_argument("--skip-detection", action="store_true",
                        help="sampling only; records honestly that detection was skipped")
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
    sampling_cfg = config.get("sampling") or {}
    detection_cfg = config.get("detection") or {}
    evidence_cfg = config.get("evidence") or {}
    target_fps = float(sampling_cfg.get("fps", 1.0))
    conf_threshold = float(detection_cfg.get("confidence_threshold", 0.4))
    device = args.device or detection_cfg.get("device", "cpu")
    save_budget = args.save_frames if args.save_frames is not None else int(
        sampling_cfg.get("save_debug_frames", 0)
    )
    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT / evidence_cfg.get(
        "output_dir", "data/evidence/phase2"
    )

    with subset_path.open("r", encoding="utf-8") as fh:
        subset = json.load(fh)
    videos = [VideoRecord.from_dict(v) for v in subset["videos"]]
    if args.limit_videos is not None:
        videos = videos[: args.limit_videos]

    detector = None
    detector_info: dict = {"model": None, "skipped": True}
    if not args.skip_detection:
        from src.pipeline.detect import YOLODetector

        weights = detection_cfg.get("weights_path", "data/models/yolo11n.pt")
        weights_path = PROJECT_ROOT / weights
        if not weights_path.exists():
            print(f"Weights not found: {weights_path}")
            return 2
        detector = YOLODetector(str(weights_path), device)
        detector_info = {
            "model": detection_cfg.get("model", detector.model_name),
            "weights": str(weights_path),
            "confidence_threshold": conf_threshold,
            "device_requested": device,
            "device_used": detector.device,
            "skipped": False,
        }
        print(f"Detector: {detector_info['model']} on {detector.device}")

    started = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()
    all_observations: list = []
    all_detections: list = []
    failures: list = []
    processed = 0
    frames_dir = output_dir / "frames" if save_budget > 0 else None
    for i, video in enumerate(videos, 1):
        print(f"[{i}/{len(videos)}] {video.video_id}")
        try:
            result = extract_video(
                video, detector, target_fps, conf_threshold, save_budget, frames_dir,
                args.max_frames,
            )
            save_budget -= result["saved_frames"]
            all_observations.extend(result["observations"])
            all_detections.extend(result["detections"])
            processed += 1
            print(f"  {result['sampled_frames']} frames @ {target_fps}fps "
                  f"(video {result['video_fps']:.2f}fps), "
                  f"{len(result['detections'])} detections")
        except Exception as exc:  # noqa: BLE001 - one bad video must not stop the run
            failures.append({"video_id": video.video_id, "error": str(exc)[:300]})
            print(f"  FAILED: {exc}")
    if detector is not None:
        detector.close()
    elapsed = round(time.perf_counter() - t0, 1)

    all_observations.sort(key=lambda o: (o.video_id, o.frame_index))
    all_detections.sort(key=lambda d: d.detection_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "videos.json", [v.to_dict() for v in videos])
    _write_json(output_dir / "observations.json", [o.to_dict() for o in all_observations])
    _write_json(output_dir / "detections.json", [d.to_dict() for d in all_detections])
    manifest = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "subset": str(subset_path),
        "sampling_fps": target_fps,
        "detector": detector_info,
        "started_utc": started,
        "elapsed_seconds": elapsed,
        "videos_selected": len(videos),
        "videos_processed": processed,
        "videos_failed": len(failures),
        "observations": len(all_observations),
        "detections": len(all_detections),
        "failures": failures,
    }
    _write_json(output_dir / "manifest.json", manifest)

    print(f"\nWrote {len(videos)} videos, {len(all_observations)} observations, "
          f"{len(all_detections)} detections -> {output_dir} in {elapsed}s")
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