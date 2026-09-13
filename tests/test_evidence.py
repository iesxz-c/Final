"""Phase 2A tests: timestamps, schema, serialization, mocked detection,
sampling math and config handling. No dataset, GPU or weights needed."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.evidence import models as m
from src.pipeline import detect as det_mod
from src.pipeline import extract_evidence as ex


class TimestampTest(unittest.TestCase):
    def test_frame_timestamp_seconds(self):
        self.assertEqual(m.frame_timestamp_seconds(0, 30.0), 0.0)
        self.assertEqual(m.frame_timestamp_seconds(30, 30.0), 1.0)
        self.assertEqual(m.frame_timestamp_seconds(15, 25.0), 0.6)

    def test_frame_timestamp_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            m.frame_timestamp_seconds(5, 0)
        with self.assertRaises(ValueError):
            m.frame_timestamp_seconds(5, None)
        with self.assertRaises(ValueError):
            m.frame_timestamp_seconds(-1, 30.0)

    def test_source_reference_format(self):
        ref = m.observation_source_reference("anomaly/Fighting/x.mp4", 12.0, 360)
        self.assertEqual(ref, "anomaly/Fighting/x.mp4@t=12.0s#f360")


class SamplingMathTest(unittest.TestCase):
    def test_sampling_step(self):
        self.assertEqual(ex.sampling_step(30.0, 1.0), 30)
        self.assertEqual(ex.sampling_step(25.0, 1.0), 25)
        self.assertEqual(ex.sampling_step(15.0, 30.0), 1)

    def test_sampling_step_rejects_bad_input(self):
        with self.assertRaises(ValueError):
            ex.sampling_step(0, 1.0)
        with self.assertRaises(ValueError):
            ex.sampling_step(30.0, 0)

    def test_iter_sampled_frames_with_stub_capture(self):
        frames = [f"frame{i}" for i in range(10)]

        class StubCapture:
            def __init__(self):
                self.calls = 0

            def read(self):
                if self.calls < len(frames):
                    frame = frames[self.calls]
                    self.calls += 1
                    return True, frame
                return False, None

        sampled = list(ex.iter_sampled_frames(StubCapture(), 10.0, 2.0))
        self.assertEqual([i for (i, _, _) in sampled], [0, 5])
        self.assertEqual([t for (_, t, _) in sampled], [0.0, 0.5])
        self.assertEqual([f for (_, _, f) in sampled], ["frame0", "frame5"])


class SchemaTest(unittest.TestCase):
    def _video(self, **overrides):
        base = {
            "video_id": "anomaly/Fighting/x.mp4",
            "source_type": "anomaly",
            "ground_truth_category": "Fighting",
            "dataset_root": "/root",
            "path": "Fighting/x.mp4",
        }
        base.update(overrides)
        return m.VideoRecord(**base)

    def test_video_record_roundtrip(self):
        video = self._video(duration_seconds=90.9666, fps=30.0)
        restored = m.VideoRecord.from_dict(video.to_dict())
        self.assertEqual(restored, video)
        self.assertEqual(restored.duration_seconds, 90.967)

    def test_video_record_rejects_bad_source(self):
        with self.assertRaises(ValueError):
            self._video(source_type="unknown")

    def test_video_record_requires_ground_truth(self):
        with self.assertRaises(ValueError):
            self._video(ground_truth_category="")

    def test_observation_validation(self):
        with self.assertRaises(ValueError):
            m.FrameObservation("o", "v", 1.0, -1, "ref")
        with self.assertRaises(ValueError):
            m.FrameObservation("o", "v", -0.5, 0, "ref")
        obs = m.FrameObservation("v:f0", "v", 1.0, 30, "v@t=1.0s#f30")
        self.assertEqual(m.FrameObservation.from_dict(obs.to_dict()), obs)

    def test_detection_validation_and_rounding(self):
        det = m.ObjectDetection(
            detection_id="o:d0",
            observation_id="o",
            video_id="v",
            timestamp_seconds=1.0,
            class_name="person",
            confidence=0.87654,
            bounding_box=[10.25, 20.0, 30.0, 40.0],
            model_name="yolo11n",
            model_conf_threshold=0.4,
        )
        self.assertEqual(det.confidence, 0.8765)
        self.assertEqual(m.ObjectDetection.from_dict(det.to_dict()), det)
        with self.assertRaises(ValueError):
            m.ObjectDetection("d", "o", "v", 1.0, "person", 1.5, [0, 0, 1, 1])
        with self.assertRaises(ValueError):
            m.ObjectDetection("d", "o", "v", 1.0, "person", 0.5, [0, 0, 1])

    def test_no_activity_field_on_models(self):
        for obj in (self._video().to_dict(),
                    m.FrameObservation("o", "v", 0.0, 0, "r").to_dict()):
            self.assertNotIn("activity", obj)


class ResolveFpsTest(unittest.TestCase):
    def _video(self, **overrides):
        base = {
            "video_id": "anomaly/X/x.mp4",
            "source_type": "anomaly",
            "ground_truth_category": "X",
            "dataset_root": "/root",
            "path": "X/x.mp4",
        }
        base.update(overrides)
        return m.VideoRecord(**base)

    def test_inventory_metadata_beats_bogus_container_fps(self):
        class BogusCapture:
            def get(self, _prop):
                return 2486.0

        video = self._video(frame_count=2729, duration_seconds=90.967, fps=30.0)
        resolved = ex.resolve_video_fps(BogusCapture(), video)
        self.assertAlmostEqual(resolved, 2729 / 90.967, places=3)

    def test_plausible_container_fps_used_as_fallback(self):
        class GoodCapture:
            def get(self, _prop):
                return 25.0

        video = self._video(fps=None)
        self.assertEqual(ex.resolve_video_fps(GoodCapture(), video), 25.0)

    def test_unusable_sources_raise(self):
        class BadCapture:
            def get(self, _prop):
                return 0.0

        with self.assertRaises(ValueError):
            ex.resolve_video_fps(BadCapture(), self._video(fps=None))


class MockDetectorTest(unittest.TestCase):
    def test_threshold_filtering(self):
        detector = det_mod.MockDetector(detections=[
            ("person", 0.9, [0, 0, 10, 10]),
            ("car", 0.2, [0, 0, 5, 5]),
        ])
        self.assertEqual(detector.model_name, "mock-detector")
        found = detector.detect(object(), 0.4)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["class_name"], "person")
        self.assertEqual(found[0]["bounding_box"], [0.0, 0.0, 10.0, 10.0])

    def test_cuda_falls_back_to_cpu_without_gpu(self):
        self.assertEqual(det_mod.YOLODetector._resolve_device("cuda"), "cpu")
        self.assertEqual(det_mod.YOLODetector._resolve_device("cpu"), "cpu")


class ExtractVideoTest(unittest.TestCase):
    def _write_tiny_video(self, directory: Path, name="tiny.mp4", frames=5):
        cv2 = __import__("cv2")
        np = __import__("numpy")
        path = directory / name
        writer = cv2.VideoWriter(
            str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 48)
        )
        self.assertTrue(writer.isOpened())
        for i in range(frames):
            writer.write(np.full((48, 64, 3), i * 20, np.uint8))
        writer.release()
        return path

    def test_extract_video_end_to_end_with_mock_detector(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video_path = self._write_tiny_video(root)
            video = m.VideoRecord(
                video_id="normal/tiny.mp4",
                source_type="normal",
                ground_truth_category="Normal",
                dataset_root=str(root),
                path="tiny.mp4",
                fps=10.0,
            )
            detector = det_mod.MockDetector(detections=[
                ("person", 0.8, [1, 2, 3, 4]),
            ])
            cap = ex.open_capture(str(video_path))
            try:
                video_fps = ex.resolve_video_fps(cap, video)
            finally:
                cap.release()
            result = ex.extract_video(
                video, detector, target_fps=video_fps,
                conf_threshold=0.4, save_frames_budget=0,
                frames_dir=None, max_frames=None,
            )
            self.assertEqual(result["sampled_frames"], 5)
            self.assertEqual(len(result["observations"]), 5)
            self.assertEqual(len(result["detections"]), 5)
            first = result["observations"][0]
            self.assertEqual(first.observation_id, "normal/tiny.mp4:f0")
            self.assertEqual(first.timestamp_seconds, 0.0)
            det = result["detections"][0]
            self.assertEqual(det.class_name, "person")
            self.assertEqual(det.observation_id, first.observation_id)
            self.assertEqual(det.video_id, "normal/tiny.mp4")
            self.assertTrue(det.detection_id.startswith(first.observation_id))

    def test_extract_video_sampling_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_tiny_video(root)
            video = m.VideoRecord(
                video_id="normal/tiny.mp4",
                source_type="normal",
                ground_truth_category="Normal",
                dataset_root=str(root),
                path="tiny.mp4",
                fps=10.0,
            )
            result = ex.extract_video(
                video, None, target_fps=5.0, conf_threshold=0.4,
                save_frames_budget=0, frames_dir=None, max_frames=2,
            )
            self.assertEqual(result["sampled_frames"], 2)
            self.assertEqual(result["detections"], [])

    def test_extract_video_missing_file_raises(self):
        video = m.VideoRecord(
            video_id="anomaly/X/missing.mp4",
            source_type="anomaly",
            ground_truth_category="X",
            dataset_root="/nonexistent",
            path="X/missing.mp4",
        )
        with self.assertRaises(Exception):
            ex.extract_video(video, None, 1.0, 0.4, 0, None)


class ConfigHandlingTest(unittest.TestCase):
    def test_phase2a_config_sections(self):
        from src.settings import load_config

        config = load_config()
        selection = config["experiments"]["phase2_subset"]["selection"]
        self.assertEqual(sum(s["count"] for s in selection), 40)
        self.assertEqual(config["sampling"]["fps"], 1.0)
        self.assertEqual(config["detection"]["device"], "cpu")
        self.assertIn("confidence_threshold", config["detection"])
        self.assertIn("weights_path", config["detection"])
        self.assertIn("output_dir", config["evidence"])

    def test_env_override_still_applies(self):
        import os

        from src.settings import dataset_paths, load_config

        with mock.patch.dict(os.environ, {"CCTV_ANOMALY_VIDEOS_DIR": "/tmp/xyz"}):
            config = load_config()
            self.assertEqual(
                dataset_paths(config)["anomaly_videos"].as_posix(), "/tmp/xyz"
            )


if __name__ == "__main__":
    unittest.main()