"""Phase 2C tests: splits, labels, paths, sampling, tensors, aggregation,
metrics, checkpoints. Offline only: synthetic files/frames and a stub
model - never downloads weights, needs no GPU, performs no real inference."""

import random
import tempfile
import unittest
from pathlib import Path

from src.pipeline import ucf_splits as splits
from src.pipeline import activity_data as data


class SplitParsingTest(unittest.TestCase):
    def _write(self, directory, name, lines):
        path = Path(directory) / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def test_parse_split_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(tmp, "train_002.txt", [
                "Abuse/Abuse013_x264.mp4 ",
                "Normal_Videos_event/Normal_Videos_317_x264.mp4",
                "",
            ])
            entries = splits.parse_split_file(path)
            self.assertEqual(entries, [
                ("Abuse/Abuse013_x264.mp4", "Abuse"),
                ("Normal_Videos_event/Normal_Videos_317_x264.mp4", "Normal"),
            ])

    def test_label_space(self):
        self.assertEqual(len(splits.CLASS_NAMES), 14)
        self.assertEqual(splits.CLASS_NAMES[-1], "Normal")
        self.assertEqual(splits.LABEL_TO_INDEX["Fighting"], 6)
        self.assertEqual(splits.split_class_to_label("Normal_Videos_event"), "Normal")
        with self.assertRaises(ValueError):
            splits.split_class_to_label("Nope")

    def test_path_resolution_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "anomaly" / "Abuse").mkdir(parents=True)
            (root / "normal").mkdir(parents=True)
            (root / "anomaly" / "Abuse" / "a.mp4").write_bytes(b"x")
            refs = ["Abuse/a.mp4", "Abuse/b.mp4", "Normal_Videos_event/n.mp4"]
            resolved = splits.resolve_video_path(root / "anomaly", root / "normal", refs[0])
            self.assertEqual(resolved, root / "anomaly" / "Abuse" / "a.mp4")
            resolved_n = splits.resolve_video_path(root / "anomaly", root / "normal", refs[2])
            self.assertEqual(resolved_n, root / "normal" / "n.mp4")
            missing = splits.find_missing(root / "anomaly", root / "normal", refs)
            self.assertEqual(sorted(missing), ["Abuse/b.mp4", "Normal_Videos_event/n.mp4"])

    def test_overlap_detection(self):
        self.assertEqual(splits.check_overlap(["a", "b"], ["b", "c"]), ["b"])
        self.assertEqual(splits.check_overlap(["a"], ["b"]), [])


class SamplingTest(unittest.TestCase):
    def test_train_window_deterministic(self):
        rng1 = random.Random(data.combine_seed(0, 3, 7))
        rng2 = random.Random(data.combine_seed(0, 3, 7))
        w1 = data.train_window_indices(1000, 16, 4, rng1)
        w2 = data.train_window_indices(1000, 16, 4, rng2)
        self.assertEqual(w1, w2)
        self.assertEqual(len(w1), 16)
        self.assertTrue(all(b - a == 4 for a, b in zip(w1, w1[1:])))
        self.assertGreaterEqual(w1[0], 0)
        self.assertLess(w1[-1], 1000)

    def test_train_window_varies_by_epoch(self):
        seen = set()
        for epoch in range(5):
            rng = random.Random(data.combine_seed(0, epoch, 7))
            w = tuple(data.train_window_indices(1000, 16, 4, rng))
            seen.add(w)
        self.assertGreater(len(seen), 1)

    def test_short_video_padded_indices(self):
        w = data.train_window_indices(5, 16, 4, random.Random(0))
        self.assertEqual(len(w), 16)

    def test_eval_windows_deterministic_and_covering(self):
        a = data.eval_window_indices(1000, 16, 4, 5)
        b = data.eval_window_indices(1000, 16, 4, 5)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 5)
        self.assertEqual(a[0][0], 0)
        self.assertLessEqual(a[-1][-1], 999)
        for w in a:
            self.assertEqual(len(w), 16)


class TensorTest(unittest.TestCase):
    def test_frames_to_tensor(self):
        import numpy as np

        frames = [np.full((240, 320, 3), v, dtype="uint8") for v in (0, 128, 255)] * 6
        frames = frames[:16]
        tensor = data.preprocess_frames(frames, training=False)
        self.assertEqual(tuple(tensor.shape), (16, 3, 224, 224))
        self.assertEqual(str(tensor.dtype), "torch.float32")
        self.assertGreaterEqual(float(tensor.min()), -3.0)
        self.assertLessEqual(float(tensor.max()), 3.0)

    def test_train_augmentation_deterministic(self):
        import numpy as np

        frames = [np.random.RandomState(0).randint(0, 255, (240, 320, 3)).astype("uint8")
                  for _ in range(16)]
        t1 = data.preprocess_frames(frames, training=True, rng=random.Random(1))
        t2 = data.preprocess_frames(frames, training=True, rng=random.Random(1))
        self.assertTrue(bool((t1 == t2).all()))


class AggregationMetricsTest(unittest.TestCase):
    def test_video_probability_averaging(self):
        import numpy as np

        clips = [np.array([0.7, 0.2, 0.1]), np.array([0.2, 0.5, 0.3]), np.array([0.4, 0.4, 0.2])]
        mean = np.mean(np.stack(clips), axis=0)
        self.assertEqual(int(mean.argmax()), 0)
        self.assertAlmostEqual(float(mean.sum()), 1.0, places=5)

    def test_compute_metrics(self):
        from src.pipeline.train_activity import compute_metrics

        m = compute_metrics([0, 0, 1, 1, 2, 2], [0, 1, 1, 1, 2, 0], 3)
        self.assertAlmostEqual(m["accuracy"], 4 / 6, places=4)
        self.assertEqual(set(m["per_class_f1"]), {"Abuse", "Arrest", "Arson"})
        self.assertEqual(len(m["confusion_matrix"]), 3)
        self.assertIn("macro_f1", m)


class FourteenClassOutputTest(unittest.TestCase):
    def test_stub_model_output_shape(self):
        import torch

        class Stub(torch.nn.Module):
            def forward(self, pixel_values):
                out = torch.zeros(pixel_values.shape[0], 14)
                out[:, 6] = 10.0  # Fighting index
                return type("R", (), {"logits": out})()

        model = Stub()
        logits = model(torch.zeros(2, 3, 16, 224, 224)).logits
        self.assertEqual(tuple(logits.shape), (2, 14))
        self.assertEqual(logits.argmax(dim=1).tolist(), [6, 6])


class CheckpointTest(unittest.TestCase):
    def test_save_and_resume_roundtrip(self):
        import torch

        from src.pipeline.train_activity import load_checkpoint, save_checkpoint

        model = torch.nn.Linear(4, 14)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ckpt"
            save_checkpoint(path, model, optimizer, None, None, epoch=2,
                            global_step=50, best_acc=0.7)
            self.assertTrue((path / "checkpoint.pt").exists())
            saved = {k: v.clone() for k, v in model.state_dict().items()}
            with torch.no_grad():
                for p in model.parameters():
                    p.add_(1.0)
            state = load_checkpoint(path, model, optimizer)
            for k, v in model.state_dict().items():
                self.assertTrue(bool((v == saved[k]).all()))
            self.assertEqual((state["epoch"], state["global_step"], state["best_acc"]),
                             (2, 50, 0.7))


class EvalCheckpointTest(unittest.TestCase):
    def _ckpt_dir(self, parent, name):
        path = Path(parent) / name
        path.mkdir(parents=True)
        (path / "checkpoint.pt").write_bytes(b"fake")
        return path

    def test_precedence_best_then_final_then_latest(self):
        import tempfile

        from src.pipeline.train_activity import resolve_eval_checkpoint

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._ckpt_dir(root, "checkpoint-epoch0")
            self._ckpt_dir(root, "final_model")
            self._ckpt_dir(root, "checkpoint-best")
            self.assertEqual(resolve_eval_checkpoint(root, None).name, "checkpoint-best")
            import shutil

            shutil.rmtree(root / "checkpoint-best")
            self.assertEqual(resolve_eval_checkpoint(root, None).name, "final_model")

    def test_explicit_resume_from(self):
        import tempfile

        from src.pipeline.train_activity import resolve_eval_checkpoint

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            custom = self._ckpt_dir(root, "custom")
            self.assertEqual(resolve_eval_checkpoint(root, custom), custom)
            with self.assertRaises(FileNotFoundError):
                resolve_eval_checkpoint(root, root / "absent")

    def test_empty_output_dir_raises(self):
        import tempfile

        from src.pipeline.train_activity import resolve_eval_checkpoint

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                resolve_eval_checkpoint(Path(tmp), None)

    def test_resolve_plus_load_restores_trained_head(self):
        import tempfile

        import torch

        from src.pipeline.train_activity import load_checkpoint, resolve_eval_checkpoint, save_checkpoint

        class TinyHead(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.classifier = torch.nn.Linear(4, 3)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            trained = TinyHead()
            with torch.no_grad():
                trained.classifier.weight.fill_(1.0)
            save_checkpoint(out / "final_model", trained, None, None, None,
                            epoch=0, global_step=10, best_acc=0.9)
            fresh = TinyHead()  # random head, like a freshly built model
            self.assertFalse(bool((fresh.classifier.weight == 1.0).all()))
            ckpt = resolve_eval_checkpoint(out, None)
            self.assertEqual(ckpt.name, "final_model")
            load_checkpoint(ckpt, fresh)
            self.assertTrue(bool((fresh.classifier.weight == 1.0).all()),
                            "eval must load trained weights, not keep the fresh head")


class ClipDatasetTest(unittest.TestCase):
    def _tiny_video(self, directory, name="tiny.mp4", frames=24):
        import cv2
        import numpy as np

        path = Path(directory) / name
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 48))
        self.assertTrue(writer.isOpened())
        for i in range(frames):
            writer.write(np.full((48, 64, 3), (i * 10) % 255, np.uint8))
        writer.release()
        return path

    def test_train_and_eval_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Abuse").mkdir()
            self._tiny_video(root / "Abuse", "a.mp4")
            entries = [("Abuse/a.mp4", "Abuse")]
            train_ds = data.UCFClipDataset(entries, root, root, mode="train", seed=0)
            train_ds.set_epoch(0)
            tensor, label, pos = train_ds[0]
            self.assertEqual(tuple(tensor.shape), (16, 3, 224, 224))
            self.assertEqual(int(label), splits.LABEL_TO_INDEX["Abuse"])
            again = data.UCFClipDataset(entries, root, root, mode="train", seed=0)
            again.set_epoch(0)
            self.assertTrue(bool((again[0][0] == tensor).all()))
            eval_ds = data.UCFClipDataset(entries, root, root, mode="eval",
                                          num_eval_clips=2, seed=0)
            self.assertEqual(len(eval_ds), 2)
            tensor_e, _, pos_e = eval_ds[1]
            self.assertEqual(tuple(tensor_e.shape), (16, 3, 224, 224))
            self.assertEqual(pos_e, 0)


if __name__ == "__main__":
    unittest.main()