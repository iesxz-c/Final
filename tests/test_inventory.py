"""Phase 1 tests for src.pipeline.inventory.

Self-contained: uses temp dirs, crafted MP4/AVI bytes and stubbed probes.
Never touches the real UCF-Crime dataset and needs no external binaries.
"""

import csv
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.pipeline import inventory as inv


# ---------------------------------------------------------------------------
# Crafted container builders
# ---------------------------------------------------------------------------
def _box(typ: bytes, payload: bytes) -> bytes:
    return struct.pack(">I4s", 8 + len(payload), typ) + payload


def make_mp4(
    timescale=25, duration_ticks=250, stts_entries=((250, 1),), width=320, height=240
) -> bytes:
    ftyp = _box(b"ftyp", b"isom" + struct.pack(">I", 0) + b"isom")
    mvhd = _box(
        b"mvhd",
        b"\x00\x00\x00\x00" + struct.pack(">IIII", 0, 0, timescale, duration_ticks),
    )
    tkhd = _box(
        b"tkhd",
        struct.pack(">III", 0, 0, 0)
        + struct.pack(">III", 1, 0, duration_ticks)
        + b"\x00" * 8
        + struct.pack(">HHHH", 0, 0, 0, 0)
        + b"\x00" * 36
        + struct.pack(">II", width << 16, height << 16),
    )
    mdhd = _box(
        b"mdhd",
        b"\x00\x00\x00\x00"
        + struct.pack(">IIII", 0, 0, timescale, duration_ticks)
        + struct.pack(">HH", 0, 0),
    )
    hdlr = _box(b"hdlr", b"\x00" * 8 + b"vide" + b"\x00" * 12 + b"VideoHandler\x00")
    stts_body = struct.pack(">II", 0, len(stts_entries))
    for count, delta in stts_entries:
        stts_body += struct.pack(">II", count, delta)
    stts = _box(b"stts", stts_body)
    stbl = _box(b"stbl", stts)
    minf = _box(b"minf", stbl)
    mdia = _box(b"mdia", mdhd + hdlr + minf)
    trak = _box(b"trak", tkhd + mdia)
    moov = _box(b"moov", mvhd + trak)
    return ftyp + moov


def _chunk(fourcc: bytes, data: bytes) -> bytes:
    blob = fourcc + struct.pack("<I", len(data)) + data
    return blob + (b"\x00" if len(data) % 2 else b"")


def make_avi(microsec=40000, total_frames=250, width=320, height=240) -> bytes:
    avih = struct.pack(
        "<IIIIIIIIIIIIII",
        microsec,
        0,
        0,
        0x10,
        total_frames,
        0,
        1,
        0,
        width,
        height,
        0,
        0,
        0,
        0,
    )
    hdrl_body = b"hdrl" + _chunk(b"avih", avih)
    hdrl = b"LIST" + struct.pack("<I", len(hdrl_body)) + hdrl_body
    body = b"AVI " + hdrl
    return b"RIFF" + struct.pack("<I", len(body)) + body


def stub_probe(path):
    return {
        "duration_seconds": 10.0,
        "fps": 25.0,
        "width": 320,
        "height": 240,
        "frame_count": 250,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class DiscoveryTest(unittest.TestCase):
    def test_finds_supported_formats_recursively(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wanted = [
                "Burglary/a.mp4",
                "Burglary/b.AVI",
                "Arrest/x.mov",
                "Fighting/y.mkv",
                "sub/deep/z.webm",
            ]
            for rel in wanted:
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"fake")
            (root / "notes.txt").write_text("ignore me")
            (root / "img.jpg").write_bytes(b"fake")
            found = [p.relative_to(root).as_posix() for p in inv.iter_video_files(root)]
            self.assertEqual(found, sorted(wanted))

    def test_missing_root_yields_nothing(self):
        self.assertEqual(list(inv.iter_video_files(Path("/nonexistent-xyz"))), [])


class CategoryTest(unittest.TestCase):
    known = ("Burglary", "Arrest")

    def test_anomaly_category_from_top_level_dir(self):
        root = Path("/data/anomaly")
        self.assertEqual(
            inv.derive_category(root, root / "Burglary" / "a.mp4", "anomaly", self.known),
            "Burglary",
        )

    def test_anomaly_nested_uses_category_dir(self):
        root = Path("/data/anomaly")
        self.assertEqual(
            inv.derive_category(
                root, root / "Arrest" / "sub" / "a.mp4", "anomaly", self.known
            ),
            "Arrest",
        )

    def test_anomaly_unknown_top_falls_back_to_parent(self):
        root = Path("/data/anomaly")
        self.assertEqual(
            inv.derive_category(
                root, root / "weird" / "Burglary" / "a.mp4", "anomaly", self.known
            ),
            "Burglary",
        )

    def test_file_directly_under_root_is_unknown(self):
        root = Path("/data/anomaly")
        self.assertEqual(
            inv.derive_category(root, root / "a.mp4", "anomaly", self.known), "Unknown"
        )

    def test_normal_is_always_normal(self):
        root = Path("/data/normal")
        self.assertEqual(
            inv.derive_category(root, root / "anything" / "a.mp4", "normal", self.known),
            "Normal",
        )


class ProbeMp4Test(unittest.TestCase):
    def test_crafted_mp4_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clip.mp4"
            path.write_bytes(make_mp4())
            meta = inv.probe_video(path)
            self.assertIsNone(meta["error"])
            self.assertEqual(meta["duration_seconds"], 10.0)
            self.assertEqual(meta["fps"], 25.0)
            self.assertEqual(meta["width"], 320)
            self.assertEqual(meta["height"], 240)
            self.assertEqual(meta["frame_count"], 250)

    def test_stts_entries_are_summed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clip.mp4"
            path.write_bytes(make_mp4(stts_entries=((100, 1), (150, 1))))
            meta = inv.probe_video(path)
            self.assertEqual(meta["frame_count"], 250)
            self.assertEqual(meta["fps"], 25.0)


class ProbeAviTest(unittest.TestCase):
    def test_crafted_avi_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clip.avi"
            path.write_bytes(make_avi())
            meta = inv.probe_video(path)
            self.assertIsNone(meta["error"])
            self.assertEqual(meta["duration_seconds"], 10.0)
            self.assertEqual(meta["fps"], 25.0)
            self.assertEqual(meta["width"], 320)
            self.assertEqual(meta["height"], 240)
            self.assertEqual(meta["frame_count"], 250)


class ProbeSniffingTest(unittest.TestCase):
    def test_avi_content_with_mp4_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "clip.mp4"
            path.write_bytes(make_avi())
            meta = inv.probe_video(path)
            self.assertIsNone(meta["error"])
            self.assertEqual(meta["duration_seconds"], 10.0)
            self.assertEqual(meta["frame_count"], 250)


class ProbeFailureTest(unittest.TestCase):
    def _check_unreadable(self, payload: bytes, suffix: str):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"broken{suffix}"
            path.write_bytes(payload)
            meta = inv.probe_video(path)
            self.assertIsNone(meta["duration_seconds"])
            self.assertTrue(meta["error"])

    def test_empty_mp4(self):
        self._check_unreadable(b"", ".mp4")

    def test_random_bytes_mp4(self):
        self._check_unreadable(bytes(range(256)) * 4, ".mp4")

    def test_truncated_mp4_without_moov(self):
        self._check_unreadable(_box(b"ftyp", b"isom"), ".mp4")

    def test_unsupported_format_without_ffprobe(self):
        with mock.patch.object(inv, "_ffprobe_available", return_value=False):
            self._check_unreadable(b"not a video", ".mkv")


class RecordTest(unittest.TestCase):
    def test_record_fields_and_relative_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "Burglary" / "a.mp4"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"0123456789")
            record = inv.build_record(
                target, root, "anomaly", ("Burglary",), False, stub_probe
            )
            self.assertEqual(record["video_id"], "anomaly/Burglary/a.mp4")
            self.assertEqual(record["filename"], "a.mp4")
            self.assertEqual(record["category"], "Burglary")
            self.assertEqual(record["path"], "Burglary/a.mp4")
            self.assertEqual(record["file_size_bytes"], 10)
            self.assertEqual(record["duration_seconds"], 10.0)
            self.assertTrue(record["metadata_ok"])
            self.assertIsNone(record["metadata_error"])
            self.assertIsNone(record["absolute_path"])

    def test_absolute_paths_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "a.mp4"
            target.write_bytes(b"0123456789")
            record = inv.build_record(target, root, "normal", (), True, stub_probe)
            self.assertEqual(record["absolute_path"], str(target))
            self.assertEqual(record["category"], "Normal")

    def test_video_id_unique_across_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.mp4").write_bytes(b"x")
            anomaly = inv.build_record(root / "a.mp4", root, "anomaly", (), False, stub_probe)
            normal = inv.build_record(root / "a.mp4", root, "normal", (), False, stub_probe)
            self.assertNotEqual(anomaly["video_id"], normal["video_id"])


class SummarizeTest(unittest.TestCase):
    def _record(self, video_id, source, category, duration, fmt="mp4", ok=True):
        return {
            "video_id": video_id,
            "filename": video_id.rsplit("/", 1)[-1],
            "source_type": source,
            "category": category,
            "dataset_root": "/root",
            "path": video_id.split("/", 1)[1],
            "absolute_path": None,
            "format": fmt,
            "file_size_bytes": 100,
            "duration_seconds": duration,
            "fps": 25.0 if ok else None,
            "width": 320 if ok else None,
            "height": 240 if ok else None,
            "frame_count": 250 if ok else None,
            "metadata_ok": ok,
            "metadata_error": None if ok else "boom",
        }

    def test_summary_counts(self):
        records = [
            self._record("anomaly/Burglary/a.mp4", "anomaly", "Burglary", 10.0),
            self._record("anomaly/Burglary/b.mp4", "anomaly", "Burglary", 20.0),
            self._record("anomaly/Arrest/c.avi", "anomaly", "Arrest", 5.0, fmt="avi"),
            self._record("normal/n.mp4", "normal", "Normal", None, ok=False),
        ]
        summary = inv.summarize(records)
        self.assertEqual(summary["total_videos"], 4)
        self.assertEqual(summary["anomaly_videos"], 3)
        self.assertEqual(summary["normal_videos"], 1)
        self.assertEqual(summary["by_category"]["Burglary"]["count"], 2)
        self.assertEqual(summary["by_category"]["Burglary"]["total_duration_seconds"], 30.0)
        self.assertEqual(summary["by_format"], {"avi": 1, "mp4": 3})
        self.assertEqual(summary["unreadable_count"], 1)
        self.assertEqual(summary["unreadable"][0]["video_id"], "normal/n.mp4")


class PersistenceTest(unittest.TestCase):
    def test_json_and_csv_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            records = [
                {
                    "video_id": "anomaly/Burglary/a.mp4",
                    "filename": "a.mp4",
                    "source_type": "anomaly",
                    "category": "Burglary",
                    "dataset_root": "/root",
                    "path": "Burglary/a.mp4",
                    "absolute_path": None,
                    "format": "mp4",
                    "file_size_bytes": 10,
                    "duration_seconds": 10.0,
                    "fps": 25.0,
                    "width": 320,
                    "height": 240,
                    "frame_count": 250,
                    "metadata_ok": True,
                    "metadata_error": None,
                }
            ]
            inv.write_inventory_json(records, out / "videos.json")
            inv.write_inventory_csv(records, out / "videos.csv")
            loaded = json.loads((out / "videos.json").read_text(encoding="utf-8"))
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["video_id"], "anomaly/Burglary/a.mp4")
            with (out / "videos.csv").open(encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["video_id"], "anomaly/Burglary/a.mp4")
            self.assertEqual(rows[0]["duration_seconds"], "10.0")


class ScanSourceTest(unittest.TestCase):
    def test_limit_caps_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("a.mp4", "b.mp4", "c.mp4"):
                (root / name).write_bytes(b"x")
            records = inv.scan_source(root, "normal", (), False, limit=2, _probe=stub_probe)
            self.assertEqual(len(records), 2)


if __name__ == "__main__":
    unittest.main()