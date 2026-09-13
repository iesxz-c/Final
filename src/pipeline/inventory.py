"""Phase 1 - Dataset inventory.

Read-only scan of the externally configured UCF-Crime dataset. Discovers
video files, extracts lightweight container metadata (duration, fps,
dimensions, frame count) without decoding frames or loading whole files
into memory, and writes a machine-readable inventory plus a summary.

No ML, no agents, no LLM calls in this phase.

Usage:
    python -m src.pipeline.inventory [--config PATH] [--output-dir DIR]
                                     [--absolute-paths] [--limit N]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
ANOMALY_SOURCE = "anomaly"
NORMAL_SOURCE = "normal"
NORMAL_CATEGORY = "Normal"
UNKNOWN_CATEGORY = "Unknown"

CSV_COLUMNS = [
    "video_id",
    "filename",
    "source_type",
    "category",
    "path",
    "dataset_root",
    "absolute_path",
    "format",
    "file_size_bytes",
    "duration_seconds",
    "fps",
    "width",
    "height",
    "frame_count",
    "metadata_ok",
    "metadata_error",
]


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------
def iter_video_files(root: Path):
    """Yield video files under root, recursively, in sorted order."""
    root = Path(root)
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            yield path


def derive_category(
    dataset_root: Path,
    file_path: Path,
    source_type: str,
    known_categories: tuple | list = (),
) -> str:
    """Derive the category for a discovered file.

    Normal videos are always "Normal". Anomaly videos take the top-level
    folder under the dataset root (the category directory); falls back to
    the immediate parent dir when that matches a known category, else
    "Unknown".
    """
    if source_type == NORMAL_SOURCE:
        return NORMAL_CATEGORY
    try:
        rel = file_path.relative_to(dataset_root)
    except ValueError:
        return UNKNOWN_CATEGORY
    if len(rel.parts) > 1 and rel.parts[0] in known_categories:
        return rel.parts[0]
    parent = file_path.parent.name
    if parent in known_categories:
        return parent
    if len(rel.parts) > 1:
        return rel.parts[0]
    return UNKNOWN_CATEGORY


# ---------------------------------------------------------------------------
# Lightweight metadata probing (headers only, never decode/load the video)
# ---------------------------------------------------------------------------
def _failed_metadata(reason: str) -> dict:
    return {
        "duration_seconds": None,
        "fps": None,
        "width": None,
        "height": None,
        "frame_count": None,
        "error": str(reason)[:300],
    }


def _read_box_header(f):
    """Read an ISO-BMFF (mp4/mov) box header at the current position."""
    pos = f.tell()
    raw = f.read(8)
    if len(raw) < 8:
        return None
    (size, raw_type) = struct.unpack(">I4s", raw)
    try:
        box_type = raw_type.decode("ascii")
    except UnicodeDecodeError:
        raise ValueError(f"invalid box type at offset {pos}")
    header_len = 8
    if size == 1:
        (size,) = struct.unpack(">Q", f.read(8))
        header_len = 16
    if size != 0 and size < header_len:
        raise ValueError(f"corrupt box {box_type!r} at offset {pos}")
    return {"type": box_type, "start": pos, "header_len": header_len, "size": size}


def _iter_child_boxes(f, payload_start: int, payload_end: int):
    f.seek(payload_start)
    guard = 0
    while f.tell() + 8 <= payload_end:
        header = _read_box_header(f)
        if header is None:
            return
        box_end = payload_end if header["size"] == 0 else header["start"] + header["size"]
        if box_end > payload_end:
            raise ValueError(f"box {header['type']!r} overruns its parent")
        yield (header["type"], header["start"] + header["header_len"], box_end)
        f.seek(box_end)
        guard += 1
        if guard > 100000:
            raise ValueError("too many boxes (file may be corrupt)")


def _find_child(f, payload_start: int, payload_end: int, want: str):
    for (box_type, start, end) in _iter_child_boxes(f, payload_start, payload_end):
        if box_type == want:
            return (start, end)
    return None


def _parse_mdhd(f, payload_start: int, payload_end: int):
    f.seek(payload_start)
    raw = f.read(32)
    if len(raw) < 20:
        raise ValueError("truncated mdhd box")
    if raw[0] == 1:
        if len(raw) < 32:
            raise ValueError("truncated mdhd box")
        (timescale,) = struct.unpack(">I", raw[20:24])
        (duration,) = struct.unpack(">Q", raw[24:32])
    else:
        (timescale,) = struct.unpack(">I", raw[12:16])
        (duration,) = struct.unpack(">I", raw[16:20])
    return timescale, duration


def _parse_tkhd_dimensions(f, payload_start: int, payload_end: int):
    if payload_end - payload_start < 8:
        raise ValueError("truncated tkhd box")
    f.seek(payload_end - 8)
    (width_fixed, height_fixed) = struct.unpack(">II", f.read(8))
    return (width_fixed >> 16, height_fixed >> 16)


def _parse_hdlr(f, payload_start: int, payload_end: int):
    f.seek(payload_start)
    raw = f.read(12)
    if len(raw) < 12:
        raise ValueError("truncated hdlr box")
    return raw[8:12].decode("ascii", errors="replace")


def _parse_stts_frame_count(f, payload_start: int, payload_end: int):
    f.seek(payload_start)
    head = f.read(8)
    if len(head) < 8:
        raise ValueError("truncated stts box")
    (_, entry_count) = struct.unpack(">II", head)
    if entry_count > 10_000_000:
        raise ValueError("suspicious stts entry count")
    total = 0
    for _ in range(entry_count):
        entry = f.read(8)
        if len(entry) < 8 or f.tell() > payload_end:
            raise ValueError("truncated stts entries")
        (sample_count, _) = struct.unpack(">II", entry)
        total += sample_count
    return total


def _probe_mp4(path: Path) -> dict:
    """Extract metadata from mp4/mov containers by walking box headers."""
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        file_end = f.tell()
        moov = None
        for (box_type, start, end) in _iter_child_boxes(f, 0, file_end):
            if box_type == "moov":
                moov = (start, end)
                break
        if moov is None:
            raise ValueError("moov box not found")
        fallback_timescale = fallback_duration = None
        mvhd = _find_child(f, moov[0], moov[1], "mvhd")
        if mvhd is not None:
            fallback_timescale, fallback_duration = _parse_mdhd(f, *mvhd)
        video = None
        for (box_type, start, end) in _iter_child_boxes(f, moov[0], moov[1]):
            if box_type != "trak":
                continue
            dims = timescale = duration = handler = frames = None
            tkhd = _find_child(f, start, end, "tkhd")
            if tkhd is not None:
                dims = _parse_tkhd_dimensions(f, *tkhd)
            mdia = _find_child(f, start, end, "mdia")
            if mdia is not None:
                hdlr = _find_child(f, mdia[0], mdia[1], "hdlr")
                if hdlr is not None:
                    handler = _parse_hdlr(f, *hdlr)
                mdhd = _find_child(f, mdia[0], mdia[1], "mdhd")
                if mdhd is not None:
                    timescale, duration = _parse_mdhd(f, *mdhd)
                minf = _find_child(f, mdia[0], mdia[1], "minf")
                if minf is not None:
                    stbl = _find_child(f, minf[0], minf[1], "stbl")
                    if stbl is not None:
                        stts = _find_child(f, stbl[0], stbl[1], "stts")
                        if stts is not None:
                            frames = _parse_stts_frame_count(f, *stts)
            if handler == "vide":
                video = {
                    "timescale": timescale,
                    "duration": duration,
                    "frames": frames,
                    "dims": dims,
                }
                break
        if video is None:
            raise ValueError("no video track found")
        timescale = video["timescale"] or fallback_timescale
        duration = video["duration"]
        if (duration is None or duration == 0) and fallback_duration:
            duration = fallback_duration
            timescale = timescale or fallback_timescale
        if not timescale or duration is None or duration <= 0:
            raise ValueError("missing or zero duration")
        duration_seconds = duration / timescale
        width, height = video["dims"] if video["dims"] else (None, None)
        frame_count = video["frames"]
        fps = frame_count / duration_seconds if frame_count else None
        return {
            "duration_seconds": round(duration_seconds, 3),
            "fps": round(fps, 3) if fps else None,
            "width": width,
            "height": height,
            "frame_count": frame_count,
            "error": None,
        }


def _iter_riff_chunks(f, start: int, end: int):
    pos = start
    guard = 0
    while pos + 8 <= end:
        f.seek(pos)
        raw = f.read(8)
        if len(raw) < 8:
            return
        (size,) = struct.unpack("<I", raw[4:8])
        data_start = pos + 8
        data_end = min(data_start + size, end)
        yield (raw[0:4], data_start, data_end)
        pos = data_end + (data_end & 1)
        guard += 1
        if guard > 100000:
            raise ValueError("too many RIFF chunks (file may be corrupt)")


def _probe_avi(path: Path) -> dict:
    """Extract metadata from AVI files via the RIFF header (no decoding)."""
    with open(path, "rb") as f:
        head = f.read(12)
        if len(head) < 12 or head[0:4] != b"RIFF" or head[8:12] != b"AVI ":
            raise ValueError("not a RIFF/AVI file")
        (riff_size,) = struct.unpack("<I", head[4:8])
        f.seek(0, os.SEEK_END)
        real_end = f.tell()
        file_end = min(8 + riff_size, real_end)
        for (fourcc, data_start, data_end) in _iter_riff_chunks(f, 12, file_end):
            if fourcc != b"LIST":
                continue
            f.seek(data_start)
            if f.read(4) != b"hdrl":
                continue
            for (child, start, _end) in _iter_riff_chunks(f, data_start + 4, data_end):
                if child != b"avih":
                    continue
                f.seek(start)
                buf = f.read(56)
                if len(buf) < 40:
                    raise ValueError("truncated avih chunk")
                (microsec,) = struct.unpack("<I", buf[0:4])
                (total_frames,) = struct.unpack("<I", buf[16:20])
                (width,) = struct.unpack("<I", buf[32:36])
                (height,) = struct.unpack("<I", buf[36:40])
                if not microsec or not total_frames:
                    raise ValueError("missing timing info in avih")
                fps = 1_000_000 / microsec
                return {
                    "duration_seconds": round(total_frames / fps, 3),
                    "fps": round(fps, 3),
                    "width": width,
                    "height": height,
                    "frame_count": total_frames,
                    "error": None,
                }
        raise ValueError("avih chunk not found")


def _ffprobe_available() -> bool:
    return shutil.which("ffprobe") is not None


def _probe_ffprobe(path: Path) -> dict:
    """Optional fallback for containers without a native parser (mkv/webm)."""
    if not _ffprobe_available():
        raise ValueError("no parser for this format and ffprobe is not installed")
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate,duration,nb_frames:format=duration",
        "-of",
        "json",
        os.fspath(path),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        raise ValueError("ffprobe timed out")
    if proc.returncode != 0:
        raise ValueError(f"ffprobe failed: {proc.stderr.strip()[:200]}")
    try:
        info = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        raise ValueError("ffprobe returned invalid JSON")
    streams = info.get("streams", [])
    if not streams:
        raise ValueError("ffprobe found no video stream")
    stream = streams[0]

    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _to_float(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    fps = None
    rate = stream.get("avg_frame_rate", "")
    if isinstance(rate, str) and "/" in rate:
        num, den = rate.split("/", 1)
        try:
            if float(den):
                fps = float(num) / float(den)
        except (TypeError, ValueError, ZeroDivisionError):
            fps = None
    duration = _to_float(stream.get("duration"))
    if not duration:
        duration = _to_float((info.get("format") or {}).get("duration"))
    if not duration or duration <= 0:
        raise ValueError("ffprobe: missing duration")
    frames = _to_int(stream.get("nb_frames"))
    if frames is None and fps:
        frames = int(round(duration * fps))
    return {
        "duration_seconds": round(duration, 3),
        "fps": round(fps, 3) if fps else None,
        "width": _to_int(stream.get("width")),
        "height": _to_int(stream.get("height")),
        "frame_count": frames,
        "error": None,
    }


def _validated(meta: dict) -> dict:
    duration = meta.get("duration_seconds")
    if duration is None or duration <= 0:
        raise ValueError(meta.get("error") or "missing or zero duration")
    return meta


def _sniff_container(path: Path) -> str | None:
    """Identify mp4/avi containers from magic bytes (12-byte read only)."""
    try:
        with open(path, "rb") as f:
            head = f.read(12)
    except OSError:
        return None
    if len(head) >= 12 and head[0:4] == b"RIFF" and head[8:12] == b"AVI ":
        return "avi"
    if len(head) >= 8 and head[4:8] == b"ftyp":
        return "mp4"
    return None


def probe_video(path: Path) -> dict:
    """Probe one file; never raises - failures become an error payload."""
    ext = Path(path).suffix.lower()
    by_extension = (
        _probe_mp4
        if ext in (".mp4", ".mov", ".m4v")
        else _probe_avi if ext == ".avi" else None
    )
    sniffed = _sniff_container(path)
    by_content = (
        _probe_mp4 if sniffed == "mp4" else _probe_avi if sniffed == "avi" else None
    )
    parsers = []
    for parser in (by_content, by_extension):
        if parser is not None and parser not in parsers:
            parsers.append(parser)
    errors: list = []
    for parser in parsers:
        try:
            return _validated(parser(path))
        except Exception as exc:  # noqa: BLE001 - try next parser, then ffprobe
            errors.append(str(exc))
    if _ffprobe_available():
        try:
            return _validated(_probe_ffprobe(path))
        except Exception as exc:  # noqa: BLE001 - reported in the record
            errors.append(str(exc))
    elif not parsers:
        errors.append("unrecognized container and ffprobe is not installed")
    return _failed_metadata("; ".join(errors) or "unknown probing error")


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------
def build_record(
    file_path: Path,
    dataset_root: Path,
    source_type: str,
    known_categories: tuple | list = (),
    absolute_paths: bool = False,
    _probe=probe_video,
) -> dict:
    dataset_root = Path(dataset_root)
    rel = file_path.relative_to(dataset_root).as_posix()
    try:
        file_size = file_path.stat().st_size
    except OSError as exc:
        file_size = 0
        meta = _failed_metadata(f"cannot stat file: {exc}")
    else:
        meta = _probe(file_path)
    duration = meta.get("duration_seconds")
    ok = duration is not None and duration > 0
    record = {
        "video_id": f"{source_type}/{rel}",
        "filename": file_path.name,
        "source_type": source_type,
        "category": derive_category(dataset_root, file_path, source_type, known_categories),
        "dataset_root": str(dataset_root),
        "path": rel,
        "format": file_path.suffix.lower().lstrip("."),
        "file_size_bytes": file_size,
        "duration_seconds": duration,
        "fps": meta.get("fps"),
        "width": meta.get("width"),
        "height": meta.get("height"),
        "frame_count": meta.get("frame_count"),
        "metadata_ok": ok,
        "metadata_error": None if ok else (meta.get("error") or "unknown probing error"),
    }
    if absolute_paths:
        record["absolute_path"] = str(file_path)
    else:
        record["absolute_path"] = None
    return record


def scan_source(
    root: Path,
    source_type: str,
    known_categories: tuple | list = (),
    absolute_paths: bool = False,
    limit: int | None = None,
    log_every: int = 100,
    _probe=probe_video,
) -> list:
    root = Path(root)
    files = sorted(iter_video_files(root))
    if limit is not None:
        files = files[:limit]
    total = len(files)
    records = []
    for i, file_path in enumerate(files, 1):
        if log_every and i % log_every == 0:
            print(f"  [{source_type}] probed {i}/{total}")
        records.append(
            build_record(file_path, root, source_type, known_categories, absolute_paths, _probe)
        )
    return records


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def write_inventory_json(records: list, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)


def write_inventory_csv(records: list, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            row = dict(record)
            for key in ("duration_seconds", "fps"):
                if isinstance(row.get(key), float):
                    row[key] = round(row[key], 3)
            writer.writerow({k: ("" if row.get(k) is None else row.get(k)) for k in CSV_COLUMNS})


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
def summarize(records: list) -> dict:
    by_category: dict = {}
    by_format: dict = {}
    unreadable = []
    anomaly_count = 0
    normal_count = 0
    for record in records:
        if record["source_type"] == ANOMALY_SOURCE:
            anomaly_count += 1
        elif record["source_type"] == NORMAL_SOURCE:
            normal_count += 1
        cat = by_category.setdefault(
            record["category"], {"count": 0, "total_duration_seconds": 0.0}
        )
        cat["count"] += 1
        if record["duration_seconds"]:
            cat["total_duration_seconds"] += record["duration_seconds"]
        by_format[record["format"]] = by_format.get(record["format"], 0) + 1
        if not record["metadata_ok"]:
            unreadable.append(
                {
                    "video_id": record["video_id"],
                    "path": record["path"],
                    "error": record["metadata_error"],
                }
            )
    for cat in by_category.values():
        cat["total_duration_seconds"] = round(cat["total_duration_seconds"], 3)
    return {
        "total_videos": len(records),
        "anomaly_videos": anomaly_count,
        "normal_videos": normal_count,
        "by_category": dict(sorted(by_category.items())),
        "by_format": dict(sorted(by_format.items())),
        "unreadable_count": len(unreadable),
        "unreadable": sorted(unreadable, key=lambda e: e["video_id"]),
    }


def print_summary(summary: dict) -> None:
    print("\n== Dataset inventory summary ==")
    print(f"  total videos:   {summary['total_videos']}")
    print(f"  anomaly videos: {summary['anomaly_videos']}")
    print(f"  normal videos:  {summary['normal_videos']}")
    print("  -- per category (count, total duration s) --")
    for category, stats in summary["by_category"].items():
        print(f"    {category}: {stats['count']} videos, {stats['total_duration_seconds']}s")
    print("  -- by format --")
    for fmt, count in summary["by_format"].items():
        print(f"    .{fmt}: {count}")
    print(f"  unreadable metadata: {summary['unreadable_count']}")
    for entry in summary["unreadable"]:
        print(f"    {entry['video_id']}: {entry['error']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def resolve_output_dir(config: dict, override: str | None) -> Path:
    if override:
        return Path(override)
    inventory_cfg = config.get("inventory") or {}
    return PROJECT_ROOT / inventory_cfg.get("output_dir", "data/inventory")


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 1: scan the dataset into an inventory")
    parser.add_argument("--config", default=None, help="path to a config file")
    parser.add_argument("--output-dir", default=None, help="override inventory output dir")
    parser.add_argument(
        "--absolute-paths",
        action="store_true",
        help="also store absolute paths per record (default: relative only)",
    )
    parser.add_argument("--limit", type=int, default=None, help="debug: cap files per source")
    parser.add_argument("--log-every", type=int, default=100, help="progress interval")
    args = parser.parse_args(argv)

    from src.settings import dataset_paths, load_config

    try:
        config = load_config(args.config)
    except Exception as exc:  # noqa: BLE001 - CLI reports config errors plainly
        print(f"Config error: {exc}")
        return 2

    paths = dataset_paths(config)
    datasets_cfg = config.get("datasets", {})
    known_categories = tuple(datasets_cfg.get("anomaly_videos", {}).get("categories", ()))
    inventory_cfg = config.get("inventory") or {}
    absolute_paths = args.absolute_paths or bool(inventory_cfg.get("store_absolute_paths", False))
    output_dir = resolve_output_dir(config, args.output_dir)

    for label, root in (("anomaly", paths["anomaly_videos"]), ("normal", paths["normal_videos"])):
        if not root or not Path(root).is_dir():
            print(f"Dataset dir missing for {label}: {root}")
            return 2

    print(f"Scanning anomaly: {paths['anomaly_videos']}")
    records = scan_source(
        paths["anomaly_videos"],
        ANOMALY_SOURCE,
        known_categories,
        absolute_paths,
        args.limit,
        args.log_every,
    )
    print(f"Scanning normal: {paths['normal_videos']}")
    records += scan_source(
        paths["normal_videos"],
        NORMAL_SOURCE,
        known_categories,
        absolute_paths,
        args.limit,
        args.log_every,
    )
    records.sort(key=lambda r: r["video_id"])

    json_path = output_dir / "videos.json"
    csv_path = output_dir / "videos.csv"
    summary_path = output_dir / "summary.json"
    write_inventory_json(records, json_path)
    write_inventory_csv(records, csv_path)
    summary = summarize(records)
    write_inventory_json(summary, summary_path)
    print(f"\nWrote {len(records)} records to {json_path} and {csv_path}")
    print(f"Wrote summary to {summary_path}")
    print_summary(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
