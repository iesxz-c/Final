"""Phase 2C (pretrained track) tests: UCF event schema, label passthrough,
top-k handling, timestamps, window shapes, metadata, preprocessing
determinism, per-video failure isolation. Mocks and synthetic frames only -
never loads the large model, needs no GPU, performs no real inference."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.evidence import models as m
from src.pipeline import activity as act
from src.pipeline import extract_ucf_events as exu


class StubCapture:
    """Fake sequential capture yielding N blank frames."""

    def __init__(self, n, shape=(16, 16, 3)):
        import numpy as np

        self._frames = [np.zeros(shape, dtype="uint8") for _ in range(n)]
        self._pos = 0

    def read(self):
        if self._pos < len(self._frames):
            frame = self._frames[self._pos]
            self._pos += 1
            return True, frame
        return False, None

    def get(self, _prop):
        return 10.0

    def release(self):
        pass


class SchemaTest(unittest.TestCase):
    def _obs(self, **overrides):
        base = {
            "observation_id": "v:e0",
            "video_id": "v",
            "start_time": 0.0,
            "end_time": 2.0,
            "label": "Assault",
            "confidence": 0.5,
        }
        base.update(overrides)
        return m.UCFEventObservation(**base)

    def test_roundtrip(self):
        self.assertEqual(m.UCFEventObservation.from_dict(self._obs().to_dict()),
                         self._obs())

    def test_rejects_bad_confidence(self):
        with self.assertRaises(ValueError):
            self._obs(confidence=1.5)

    def test_rejects_bad_window(self):
        with self.assertRaises(ValueError):
            self._obs(start_time=3.0, end_time=2.0)

    def test_rejects_empty_label(self):
        with self.assertRaises(ValueError):
            self._obs(label="")

    def test_no_ground_truth_or_activity_fields(self):
        d = self._obs().to_dict()
        self.assertNotIn("ground_truth_category", d)
        self.assertNotIn("activity", d)
        self.assertNotIn("top_k", [k for k in d if k == "activity"])
        self.assertTrue(d["observation_id"].endswith(":e0"))


class LabelMappingTest(unittest.TestCase):
    def test_labels_pass_through_verbatim(self):
        obs = act.to_ucf_event_observation(
            "anomaly/Fighting/x.mp4", 3, [0, 4], 0.0, 2.0,
            {"label": "Fighting", "confidence": 0.62,
             "top_k": [{"label": "Fighting", "confidence": 0.62},
                       {"label": "Assault", "confidence": 0.11}]},
            "OPear/videomae-large-finetuned-UCF-Crime", "rev123",
        )
        self.assertEqual(obs.label, "Fighting")
        self.assertEqual(obs.observation_id, "anomaly/Fighting/x.mp4:e3")
        self.assertEqual(obs.model_name, "OPear/videomae-large-finetuned-UCF-Crime")
        self.assertEqual(obs.model_version, "rev123")
        self.assertEqual(obs.source_reference,
                         "anomaly/Fighting/x.mp4@t=0.0s-2.0s")

    def test_top_k_softmax_shape(self):
        import torch

        logits = torch.tensor([2.0, 1.0, 0.5, 0.0, -1.0])
        probs = torch.softmax(logits, dim=0)
        self.assertAlmostEqual(float(probs.sum()), 1.0, places=5)
        top = torch.topk(probs, k=5)
        ordered = top.values.tolist()
        self.assertEqual(ordered, sorted(ordered, reverse=True))
        obs = act.to_ucf_event_observation(
            "v", 0, [0], 0.0, 1.0,
            {"label": "a", "confidence": float(probs[0]),
             "top_k": [{"label": f"c{i}", "confidence": float(p)}
                       for i, p in enumerate(probs.tolist())]},
            "mock", "mock-0",
        )
        self.assertEqual(len(obs.top_k), 5)
        self.assertEqual(obs.top_k[0]["label"], "c0")


class WindowReuseTest(unittest.TestCase):
    def test_same_windows_as_phase2b(self):
        cap = StubCapture(64)
        windows = list(act.iter_window_frames(cap, 30.0, 16, 15.0, 16))
        self.assertEqual(len(windows), 2)
        self.assertEqual(len(windows[0][2]), 16)  # 16 frames per window
        self.assertEqual(windows[0][1], list(range(0, 32, 2)))

    def test_timestamps_preserved(self):
        start, end = act.window_timestamps([0, 60], 30.0)
        self.assertEqual((start, end), (0.0, 2.0))


class PreprocessingDeterminismTest(unittest.TestCase):
    def test_same_seed_same_tensor(self):
        import numpy as np

        frames = [np.random.RandomState(0).randint(0, 255, (240, 320, 3)).astype("uint8")
                  for _ in range(16)]
        self.assertTrue(hasattr(act, "UCFEventModel"))
        from src.pipeline.activity_data import preprocess_frames
        import random

        a = preprocess_frames(frames, training=True, rng=random.Random(7))
        b = preprocess_frames(frames, training=True, rng=random.Random(7))
        self.assertTrue(bool((a == b).all()))
        self.assertEqual(tuple(a.shape), (16, 3, 224, 224))


class FailureIsolationTest(unittest.TestCase):
    def _video(self, root, name, category="Fighting"):
        return m.VideoRecord(
            video_id=f"anomaly/{category}/{name}",
            source_type="anomaly",
            ground_truth_category=category,
            dataset_root=str(root),
            path=f"{category}/{name}",
            fps=10.0,
        )

    def test_one_bad_video_does_not_stop_run(self):
        import tempfile
        from pathlib import Path as P
        from unittest import mock

        from src.pipeline import detect as det_mod

        with tempfile.TemporaryDirectory() as tmp:
            root = P(tmp)
            good = self._video(root, "good.mp4")
            bad = self._video(root, "bad.mp4")
            model = det_mod.MockDetector(
                model_name="mock-ucf", detections=[])  # predict unused here
            model.predict = lambda frames_bgr, top_k: {
                "label": "Fighting", "confidence": 0.9,
                "top_k": [{"label": "Fighting", "confidence": 0.9}]}
            model.model_version = "mock-0"

            events, failures = [], []
            with mock.patch.object(exu, "open_capture",
                                   side_effect=[StubCapture(20),
                                                RuntimeError("decode boom")]):
                for video in (good, bad):
                    try:  # mirrors the CLI per-video isolation
                        result = exu.extract_video_events(
                            video, model, 16, 8.0, 16, 5, None)
                        events.extend(result["events"])
                    except Exception as exc:  # noqa: BLE001 - record and continue
                        failures.append({"video_id": video.video_id,
                                         "error": str(exc)})
            self.assertEqual(len(events), 2)  # 16-frame window + padded tail
            self.assertEqual(len(failures), 1)
            self.assertTrue(failures[0]["video_id"].endswith("bad.mp4"))
            self.assertTrue(all(e.video_id == good.video_id for e in events))


if __name__ == "__main__":
    unittest.main()