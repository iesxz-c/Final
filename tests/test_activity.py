"""Phase 2B tests: ActivityObservation validation, window sampling math,
model-output conversion, top-k, device fallback, traceability. Mocks and
synthetic frames only - never downloads the model, needs no GPU, performs
no real inference."""

import unittest

from src.evidence import models as m
from src.pipeline import activity as act
from src.pipeline import extract_activity as exa


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


class WindowSamplingTest(unittest.TestCase):
    def test_non_overlapping_windows(self):
        cap = StubCapture(64)
        windows = list(act.iter_window_frames(cap, 30.0, 16, 15.0, 16))
        self.assertEqual(len(windows), 2)  # 32 sampled frames -> 2 windows
        idx0, frames0, _, padded0 = windows[0]
        self.assertEqual(idx0, 0)
        self.assertEqual(frames0, list(range(0, 32, 2)))
        self.assertEqual(padded0, 0)
        self.assertEqual(windows[1][1], list(range(32, 64, 2)))

    def test_short_tail_is_padded(self):
        cap = StubCapture(20)
        windows = list(act.iter_window_frames(cap, 10.0, 16, 10.0, 16))
        self.assertEqual(len(windows), 2)
        self.assertEqual(windows[0][3], 0)
        self.assertEqual(windows[1][3], 12)  # 4 real + 12 repeated
        self.assertEqual(len(windows[1][2]), 16)
        self.assertEqual(windows[1][1][:4], [16, 17, 18, 19])

    def test_overlapping_hop(self):
        cap = StubCapture(20)
        windows = list(act.iter_window_frames(cap, 10.0, 4, 10.0, 2))
        self.assertEqual([w[1] for w in windows],
                         [[0, 1, 2, 3], [2, 3, 4, 5], [4, 5, 6, 7], [6, 7, 8, 9],
                          [8, 9, 10, 11], [10, 11, 12, 13], [12, 13, 14, 15],
                          [14, 15, 16, 17], [16, 17, 18, 19], [18, 19, 19, 19]])

    def test_invalid_params_raise(self):
        with self.assertRaises(ValueError):
            list(act.iter_window_frames(StubCapture(4), 10.0, 0, 10.0, 4))
        with self.assertRaises(ValueError):
            list(act.iter_window_frames(StubCapture(4), 10.0, 4, 10.0, 0))
        with self.assertRaises(ValueError):
            act.window_timestamps([], 10.0)

    def test_window_timestamps(self):
        start, end = act.window_timestamps([30, 60, 90], 30.0)
        self.assertEqual((start, end), (1.0, 3.0))


class ConversionTest(unittest.TestCase):
    def test_prediction_to_observation(self):
        obs = act.to_activity_observation(
            "anomaly/Fighting/x.mp4", 2, [60, 90], 2.0, 3.0,
            {"label": "punching", "confidence": 0.8234,
             "top_k": [{"label": "punching", "confidence": 0.8234},
                       {"label": "wrestling", "confidence": 0.05}]},
            "MCG-NJU/videomae-base-finetuned-kinetics", "abc123",
        )
        self.assertEqual(obs.observation_id, "anomaly/Fighting/x.mp4:a2")
        self.assertEqual(obs.video_id, "anomaly/Fighting/x.mp4")
        self.assertEqual(obs.label, "punching")
        self.assertEqual(obs.confidence, 0.8234)
        self.assertEqual(len(obs.top_k), 2)
        self.assertEqual(obs.top_k[1]["label"], "wrestling")
        self.assertEqual(obs.source_reference,
                         "anomaly/Fighting/x.mp4@t=2.0s-3.0s")
        self.assertEqual(m.ActivityObservation.from_dict(obs.to_dict()), obs)


class SchemaValidationTest(unittest.TestCase):
    def _obs(self, **overrides):
        base = {
            "observation_id": "v:a0",
            "video_id": "v",
            "start_time": 0.0,
            "end_time": 2.0,
            "label": "dancing",
            "confidence": 0.5,
        }
        base.update(overrides)
        return m.ActivityObservation(**base)

    def test_roundtrip(self):
        self.assertEqual(m.ActivityObservation.from_dict(self._obs().to_dict()),
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

    def test_rejects_bad_top_k(self):
        with self.assertRaises(ValueError):
            self._obs(top_k=[{"label": "x", "confidence": 2.0}])

    def test_no_ground_truth_leakage_field(self):
        d = self._obs().to_dict()
        self.assertNotIn("ground_truth_category", d)
        self.assertNotIn("activity", d)


class MockModelTest(unittest.TestCase):
    def test_mock_cycles_predictions_and_clips_top_k(self):
        model = act.MockActivityModel(predictions=[
            {"label": "running", "confidence": 0.9,
             "top_k": [{"label": "running", "confidence": 0.9},
                       {"label": "jogging", "confidence": 0.05},
                       {"label": "walking", "confidence": 0.01}]},
        ])
        first = model.predict([object()], top_k=2)
        self.assertEqual(first["label"], "running")
        self.assertEqual(len(first["top_k"]), 2)
        second = model.predict([object()], top_k=5)
        self.assertEqual(second["label"], "running")  # cycles single entry

    def test_device_fallback_without_gpu(self):
        self.assertEqual(act.VideoMAEActivityModel._resolve_device("auto"), "cpu")
        self.assertEqual(act.VideoMAEActivityModel._resolve_device("cuda"), "cpu")
        self.assertEqual(act.VideoMAEActivityModel._resolve_device("cpu"), "cpu")


class ExtractActivityTest(unittest.TestCase):
    def _video(self, root, name="tiny.mp4"):
        return m.VideoRecord(
            video_id=f"normal/{name}",
            source_type="normal",
            ground_truth_category="Normal",
            dataset_root=str(root),
            path=name,
            fps=10.0,
        )

    def test_extract_with_mock_model_and_stub_capture(self):
        import tempfile
        from pathlib import Path
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            video = self._video(Path(tmp))
            model = act.MockActivityModel(predictions=[
                {"label": "sitting", "confidence": 0.6, "top_k": []}
            ])
            with mock.patch.object(exa, "open_capture", return_value=StubCapture(20)):
                result = exa.extract_video_activity(
                    video, model, num_frames=4, sampling_fps=10.0,
                    window_hop=4, top_k=3, max_windows=None,
                )
            self.assertEqual(result["windows"], 5)  # 20 frames / 4
            self.assertEqual(len(result["activities"]), 5)
            first = result["activities"][0]
            self.assertEqual(first.video_id, video.video_id)
            self.assertEqual(first.label, "sitting")  # mock label, not "Normal"
            self.assertEqual(first.frame_indices, [0, 1, 2, 3])
            self.assertNotEqual(first.label, video.ground_truth_category)

    def test_max_windows_caps_inference_calls(self):
        import tempfile
        from pathlib import Path
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            video = self._video(Path(tmp))
            model = act.MockActivityModel()
            with mock.patch.object(exa, "open_capture", return_value=StubCapture(40)):
                result = exa.extract_video_activity(
                    video, model, num_frames=4, sampling_fps=10.0,
                    window_hop=4, top_k=1, max_windows=2,
                )
            self.assertEqual(result["windows"], 2)
            self.assertEqual(model.calls, 2)


class WeightRemapTest(unittest.TestCase):
    def test_qv_bias_mapping_and_key_zeroing(self):
        import torch
        from unittest import mock

        prefix = "videomae.encoder.layer.0.attention.attention."
        fake_state = {
            prefix + "q_bias": torch.ones(8),
            prefix + "v_bias": torch.ones(8) * 2,
            "classifier.bias": torch.zeros(3),
            "classifier.weight": torch.ones(400, 8),
        }

        class FakeParam:
            def __init__(self):
                self.data = torch.ones(8)

        key_param = FakeParam()

        class FakeModel:
            def __init__(self):
                self.seen = None

            def state_dict(self):
                return {prefix + "query.bias": torch.zeros(8),
                        prefix + "value.bias": torch.zeros(8),
                        "classifier.weight": torch.zeros(14, 8)}

            def load_state_dict(self, state, strict=False):
                self.seen = state
                return ([prefix + "key.bias"], [])

            def named_parameters(self):
                return [(prefix + "key.bias", key_param)]

        model = FakeModel()
        with mock.patch("huggingface_hub.hf_hub_download", return_value="/tmp/w"):
            with mock.patch("safetensors.torch.load_file", return_value=fake_state):
                note = act._load_kinetics_state_dict(model, "some-id")
        self.assertIn(prefix + "query.bias", model.seen)
        self.assertTrue(torch.equal(model.seen[prefix + "query.bias"], torch.ones(8)))
        self.assertTrue(torch.equal(model.seen[prefix + "value.bias"], torch.ones(8) * 2))
        self.assertTrue(torch.equal(key_param.data, torch.zeros(8)))
        self.assertIn("missing=1 unexpected=0", note)
        self.assertNotIn("classifier.weight", model.seen)
        self.assertIn("classifier.weight", note)


class ConfigHandlingTest(unittest.TestCase):
    def test_activity_model_config_present(self):
        from src.settings import load_config

        config = load_config()
        activity = config["activity_model"]
        self.assertEqual(activity["name"],
                         "MCG-NJU/videomae-base-finetuned-kinetics")
        self.assertEqual(activity["num_frames"], 16)
        self.assertIn("sampling_fps", activity)
        self.assertIn("top_k", activity)
        self.assertIn("device", activity)
        self.assertIn("output_dir", activity)


if __name__ == "__main__":
    unittest.main()