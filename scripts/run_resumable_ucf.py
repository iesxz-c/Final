"""Crash-safe batched runner for large-scale UCF temporal inference.

Runs an existing manifest (e.g. data/phase2c_remaining_702.json) through
the UNMODIFIED `src.pipeline.extract_ucf_events` CLI in small batches,
so a Colab interruption loses at most one batch. Resume is driven by a
persistent on-disk checkpoint (`state.json` inside --output-dir); a video
counts as completed only when verified in the batch output, never merely
because the subprocess exited.

Usage:
    python scripts/run_resumable_ucf.py --input-manifest data/phase2c_remaining_702.json \\
        --output-dir data/evidence/phase2c_ucf_batches --device cuda
    python scripts/run_resumable_ucf.py --input-manifest ... --output-dir ... \\
        --merge --merge-output-dir data/evidence/phase2c_ucf_remaining_702
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_VERSION = "resumable-ucf/v1"
DEFAULT_BATCH_SIZE = 50


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path):
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, payload) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def load_state(output_dir: Path) -> dict | None:
    path = Path(output_dir) / "state.json"
    if not path.exists():
        return None
    return _read_json(path)


def save_state(output_dir: Path, state: dict) -> None:
    state = dict(state)
    state["last_updated"] = _utcnow()
    _write_json(Path(output_dir) / "state.json", state)


def fresh_state(input_manifest: Path, total_videos: int) -> dict:
    return {"schema_version": STATE_VERSION,
            "input_manifest": str(input_manifest),
            "total_videos": total_videos,
            "completed_video_ids": [],
            "failed_video_ids": [],
            "batches_completed": 0,
            "last_updated": _utcnow()}


def verify_batch(batch_dir: Path, expected_ids: list) -> tuple:
    """Verify batch output; return (completed_ids, failed_ids).

    A video counts as completed only if it appears exactly once in the
    batch videos.json, is absent from the batch manifest failures, and
    every event record is traceable. Zero events is valid when the
    manifest confirms the video processed without failure.
    """
    batch_dir = Path(batch_dir)
    videos_path = batch_dir / "videos.json"
    events_path = batch_dir / "ucf_events.json"
    manifest_path = batch_dir / "manifest.json"
    if not (videos_path.exists() and events_path.exists() and manifest_path.exists()):
        return [], list(expected_ids)
    try:
        videos = _read_json(videos_path)
        events = _read_json(events_path)
        manifest = _read_json(manifest_path)
    except ValueError:
        return [], list(expected_ids)
    if not isinstance(videos, list) or not isinstance(events, list):
        return [], list(expected_ids)
    counts: dict = {}
    for video in videos:
        if isinstance(video, dict) and video.get("video_id"):
            counts[video["video_id"]] = counts.get(video["video_id"], 0) + 1
    failed = {f.get("video_id") for f in manifest.get("failures", []) or []
              if isinstance(f, dict)}
    event_videos = {e.get("video_id") for e in events if isinstance(e, dict)}
    completed, missing = [], []
    for video_id in expected_ids:
        if counts.get(video_id, 0) != 1 or video_id in failed:
            missing.append(video_id)
            continue
        stray = [e for e in events if isinstance(e, dict)
                 and e.get("video_id") == video_id and not e.get("observation_id")]
        if stray:
            missing.append(video_id)
            continue
        _ = event_videos  # presence optional; zero events is a valid result
        completed.append(video_id)
    return sorted(completed), sorted(missing)


def _invoke_extract(batch_manifest: Path, batch_dir: Path, device: str) -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "src.pipeline.extract_ucf_events",
         "--input-manifest", str(batch_manifest),
         "--output-dir", str(batch_dir),
         "--device", device],
        cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=None)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def run_batches(input_manifest: Path, output_dir: Path, device: str,
                batch_size: int, max_batches: int | None = None,
                _invoke=_invoke_extract) -> int:
    manifest = _read_json(input_manifest)
    entries = manifest.get("videos", [])
    if not isinstance(entries, list) or not entries:
        print("investigation error: manifest has no videos list")
        return 2
    video_ids = [v["video_id"] for v in entries]
    if len(set(video_ids)) != len(video_ids):
        print("investigation error: duplicate video_ids in input manifest")
        return 2

    output_dir = Path(output_dir)
    state = load_state(output_dir)
    if state is None:
        state = fresh_state(input_manifest, len(video_ids))
        save_state(output_dir, state)
    elif state.get("total_videos") != len(video_ids):
        print(f"investigation error: manifest changed "
              f"({state.get('total_videos')} vs {len(video_ids)} videos)")
        return 2

    completed = set(state.get("completed_video_ids", []))
    print(f"TOTAL: {len(video_ids)}")
    print(f"COMPLETED BEFORE START: {len(completed)}")
    remaining = [v for v in video_ids if v not in completed]
    print(f"REMAINING: {len(remaining)}")
    if not remaining:
        print("nothing to do: all videos already completed")
        return 0

    batches_done = 0
    exit_code = 0
    while remaining:
        if max_batches is not None and batches_done >= max_batches:
            break
        batch_index = state.get("batches_completed", 0) + 1
        batch_ids = remaining[:batch_size]
        batch_name = f"batch_{batch_index:03d}"
        batch_dir = output_dir / batch_name
        print(f"CURRENT BATCH: {batch_name} ({len(batch_ids)} videos)")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                         encoding="utf-8") as fh:
            json.dump({"videos": [v for v in entries if v["video_id"] in set(batch_ids)]},
                      fh)
            batch_manifest = Path(fh.name)
        try:
            code = _invoke(batch_manifest, batch_dir, device)
        except Exception as exc:  # noqa: BLE001 - record, never mark complete
            print(f"batch invocation failed: {exc}")
            code = 1
        finally:
            batch_manifest.unlink(missing_ok=True)
        done, missing = verify_batch(batch_dir, batch_ids)
        print(f"BATCH PROGRESS: {len(done)}/{len(batch_ids)} verified")
        completed |= set(done)
        state["completed_video_ids"] = sorted(completed)
        failed = sorted(set(state.get("failed_video_ids", [])) | set(missing))
        state["failed_video_ids"] = [v for v in failed if v not in completed]
        if missing:
            print(f"batch {batch_name} incomplete: {len(missing)} unverified "
                  f"(subprocess exit={code})")
        else:
            state["batches_completed"] = batch_index
        save_state(output_dir, state)
        print(f"COMPLETED AFTER BATCH: {len(completed)}")
        remaining = [v for v in video_ids if v not in completed]
        print(f"REMAINING AFTER BATCH: {len(remaining)}")
        batches_done += 1
        if missing:
            print(f"stopping safely; {len(remaining)} video(s) remain for resume: "
                  f"{remaining[:5]}{'...' if len(remaining) > 5 else ''}")
            exit_code = 2
            break
    return exit_code


def merge_batches(output_dir: Path, merge_dir: Path) -> int:
    """Deterministically merge verified per-batch outputs into one directory."""
    output_dir, merge_dir = Path(output_dir), Path(merge_dir)
    state = load_state(output_dir)
    if state is None:
        print("merge error: no state.json (run batches first)")
        return 2
    batch_dirs = sorted(p for p in output_dir.iterdir()
                        if p.is_dir() and p.name.startswith("batch_"))
    videos, events = [], []
    seen_videos, seen_obs = set(), set()
    for batch_dir in batch_dirs:
        for video in _read_json(batch_dir / "videos.json"):
            if video["video_id"] in seen_videos:
                print(f"merge error: duplicate video {video['video_id']} in {batch_dir.name}")
                return 2
            seen_videos.add(video["video_id"])
            videos.append(video)
        for event in _read_json(batch_dir / "ucf_events.json"):
            if event["observation_id"] in seen_obs:
                print(f"merge error: duplicate observation {event['observation_id']}")
                return 2
            seen_obs.add(event["observation_id"])
            events.append(event)
    completed = set(state.get("completed_video_ids", []))
    if seen_videos != completed:
        print(f"merge error: merged {len(seen_videos)} videos but checkpoint "
              f"lists {len(completed)} completed")
        return 2
    videos.sort(key=lambda v: v["video_id"])
    events.sort(key=lambda e: (e["video_id"], e["start_time"]))
    try:
        from src.evidence.models import EVIDENCE_SCHEMA_VERSION
    except ImportError:
        EVIDENCE_SCHEMA_VERSION = "phase2a/v1"
    merge_dir.mkdir(parents=True, exist_ok=True)
    _write_json(merge_dir / "videos.json", videos)
    _write_json(merge_dir / "ucf_events.json", events)
    _write_json(merge_dir / "manifest.json", {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "inputs": {"batches": [p.name for p in batch_dirs],
                   "state": str(output_dir / "state.json")},
        "videos_selected": len(videos), "videos_processed": len(videos),
        "videos_failed": 0, "observations": len(events), "failures": [],
        "merged_utc": _utcnow()})
    print(f"merged {len(videos)} videos, {len(events)} observations -> {merge_dir}")
    return 0


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4C: resumable batched UCF inference")
    parser.add_argument("--input-manifest", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--merge-output-dir", default=None)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-batches", type=int, default=None)
    parser.add_argument("--merge", action="store_true",
                        help="merge verified batches instead of running")
    args = parser.parse_args(argv)

    if args.batch_size is not None and args.batch_size < 1:
        print("investigation error: --batch-size must be >= 1")
        return 2
    output_dir = Path(args.output_dir) if args.output_dir else None
    if output_dir is None:
        print("investigation error: --output-dir is required")
        return 2
    if args.merge:
        merge_dir = (Path(args.merge_output_dir) if args.merge_output_dir
                     else PROJECT_ROOT / "data/evidence/phase2c_ucf_remaining_702")
        return merge_batches(output_dir, merge_dir)
    if not args.input_manifest:
        print("investigation error: --input-manifest is required (or use --merge)")
        return 2
    return run_batches(Path(args.input_manifest), output_dir, args.device,
                       args.batch_size, args.max_batches)


if __name__ == "__main__":
    sys.exit(main())
