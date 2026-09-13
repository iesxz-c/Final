"""Phase 2C - Lazy clip dataset for VideoMAE fine-tuning on UCF-Crime.

Videos are never copied to RAM in full: each item opens its video,
decodes only the required frames (sequential reads + positional seeks),
and keeps at most one 16-frame window in memory. Preprocessing is
numpy/cv2 only (ImageNet mean/std, matching the HF processor defaults)
so dataset workers need no Hugging Face objects.

Training sampling is deterministic but varied per (seed, epoch, index);
evaluation uses evenly spaced windows whose softmax outputs are averaged
per video (video-level evaluation).
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

NUM_FRAMES = 16
CROP_SIZE = 224
RESIZE_EDGE = 256
# ImageNet statistics (same defaults as the VideoMAE image processor).
KINETICS_MEAN = (0.485, 0.456, 0.406)
KINETICS_STD = (0.229, 0.224, 0.225)


def combine_seed(*parts: int) -> int:
    """Deterministically fold ints into one seed (random.Random takes no tuples)."""
    import hashlib

    digest = hashlib.sha256(repr(tuple(int(p) for p in parts)).encode()).digest()
    return int.from_bytes(digest[:8], "big")


def sampling_stride(video_fps: float, sampling_fps: float) -> int:
    if video_fps is None or video_fps <= 0:
        video_fps = 30.0
    if sampling_fps is None or sampling_fps <= 0:
        raise ValueError(f"invalid sampling_fps: {sampling_fps}")
    return max(1, int(round(video_fps / sampling_fps)))


def train_window_indices(total_frames: int, num_frames: int, stride: int, rng: random.Random) -> list:
    """Random contiguous strided window; edge-padded if the video is short."""
    span = (num_frames - 1) * stride
    start = rng.randint(0, max(0, total_frames - 1 - span))
    return [start + j * stride for j in range(num_frames)]


def eval_window_indices(total_frames: int, num_frames: int, stride: int, num_clips: int) -> list:
    """Evenly spaced windows covering the video (deterministic)."""
    import numpy as np

    span = (num_frames - 1) * stride
    if num_clips < 1:
        raise ValueError(f"invalid num_clips: {num_clips}")
    if total_frames - 1 <= span:
        return [list(range(0, num_frames * stride, stride))]
    starts = np.linspace(0, total_frames - 1 - span, num_clips).round().astype(int)
    return [(s + np.arange(num_frames) * stride).tolist() for s in starts]


def grab_frames(path: str, indices: list) -> tuple:
    """Decode only the requested frames; out-of-range indices edge-repeat.

    Returns (frames_bgr, padded_count). Opens and releases the capture per
    call, so it is safe under multi-worker loading.
    """
    import cv2

    want = sorted(set(indices))
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {path}")
    try:
        frames: dict = {}
        next_pos = 0
        for target in want:
            if target < 0:
                continue
            if target != next_pos:
                cap.set(cv2.CAP_PROP_POS_FRAMES, target)
            ok, frame = cap.read()
            next_pos = target + 1
            if not ok or frame is None:
                break
            frames[target] = frame
        if not frames:
            raise RuntimeError(f"could not decode any frame from: {path}")
        last = frames[max(frames)]
        out = []
        padded = 0
        for i in indices:
            if i in frames:
                out.append(frames[i])
            else:
                out.append(last)
                padded += 1
        return out, padded
    finally:
        cap.release()


def preprocess_frames(frames_bgr, training: bool, rng: random.Random | None = None):
    """Resize/crop/flip/normalize a list of BGR frames to a (C,T,H,W) tensor."""
    import cv2
    import numpy as np
    import torch

    processed = []
    for frame in frames_bgr:
        rgb = frame[:, :, ::-1]
        h, w = rgb.shape[:2]
        scale = RESIZE_EDGE / min(h, w)
        resized = cv2.resize(rgb, (int(w * scale + 0.5), int(h * scale + 0.5)))
        rh, rw = resized.shape[:2]
        if training:
            if rng is None:
                raise ValueError("training preprocessing needs an rng")
            top = rng.randint(0, max(0, rh - CROP_SIZE))
            left = rng.randint(0, max(0, rw - CROP_SIZE))
            flip = rng.random() < 0.5
        else:
            top = max(0, (rh - CROP_SIZE) // 2)
            left = max(0, (rw - CROP_SIZE) // 2)
            flip = False
        crop = resized[top:top + CROP_SIZE, left:left + CROP_SIZE]
        if crop.shape[0] != CROP_SIZE or crop.shape[1] != CROP_SIZE:
            crop = cv2.resize(crop, (CROP_SIZE, CROP_SIZE))
        if flip:
            crop = np.ascontiguousarray(crop[:, ::-1, :])
        arr = crop.astype("float32") / 255.0
        mean = np.array(KINETICS_MEAN, dtype="float32").reshape(1, 1, 3)
        std = np.array(KINETICS_STD, dtype="float32").reshape(1, 1, 3)
        processed.append((arr - mean) / std)
    stacked = np.stack(processed, axis=0)  # (T,H,W,C)
    return torch.from_numpy(np.ascontiguousarray(stacked.transpose(0, 3, 1, 2))).permute(1, 0, 2, 3)


def video_frame_count(path: str) -> int:
    import cv2

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {path}")
    try:
        total = 0
        while True:
            ok, _ = cap.read()
            if not ok:
                break
            total += 1
        return total
    finally:
        cap.release()


class UCFClipDataset:
    """Lazy (reference, label) clip dataset. mode='train' yields one random
    window per video per epoch (call set_epoch(e) each epoch); mode='eval'
    yields num_eval_clips fixed windows per video for probability averaging."""

    def __init__(self, entries, anomaly_root, normal_root, num_frames=NUM_FRAMES,
                 sampling_fps=8.0, mode="train", num_eval_clips=5, seed=0):
        if mode not in ("train", "eval"):
            raise ValueError(f"bad mode: {mode!r}")
        from src.pipeline.ucf_splits import LABEL_TO_INDEX, resolve_video_path

        self.paths = [str(resolve_video_path(anomaly_root, normal_root, r)) for (r, _) in entries]
        self.labels = [LABEL_TO_INDEX[label] for (_, label) in entries]
        self.video_ids = [r for (r, _) in entries]
        self.num_frames = num_frames
        self.sampling_fps = sampling_fps
        self.mode = mode
        self.num_eval_clips = num_eval_clips
        self.seed = seed
        self.epoch = 0
        if mode == "eval":
            self.item_index = []
            for pos in range(len(self.paths)):
                for clip in range(num_eval_clips):
                    self.item_index.append((pos, clip))
        else:
            self.item_index = [(pos, 0) for pos in range(len(self.paths))]

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch

    def __len__(self) -> int:
        return len(self.item_index)

    def _video_fps(self, path: str) -> float:
        import cv2

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError(f"cannot open video: {path}")
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            return fps if fps and 0 < fps <= 120 else 30.0
        finally:
            cap.release()

    def __getitem__(self, i: int):
        import torch

        pos, clip_no = self.item_index[i]
        path = self.paths[pos]
        total = video_frame_count(path)
        if total <= 0:
            raise RuntimeError(f"no decodable frames: {path}")
        stride = sampling_stride(self._video_fps(path), self.sampling_fps)
        if self.mode == "train":
            rng = random.Random(combine_seed(self.seed, self.epoch, pos))
            indices = train_window_indices(total, self.num_frames, stride, rng)
        else:
            windows = eval_window_indices(total, self.num_frames, stride, self.num_eval_clips)
            indices = windows[clip_no % len(windows)]
        frames, _ = grab_frames(path, indices)
        rng = random.Random(combine_seed(self.seed, self.epoch, pos, 1)) \
            if self.mode == "train" else None
        tensor = preprocess_frames(frames, training=self.mode == "train", rng=rng)
        return tensor, torch.tensor(self.labels[pos], dtype=torch.long), pos


def main(argv: list | None = None) -> int:
    """Smoke check: decode clips from a few real videos, print batch shapes."""
    parser = argparse.ArgumentParser(description="Phase 2C: clip dataset smoke check")
    parser.add_argument("--config", default=None)
    parser.add_argument("--anomaly-root", default=None)
    parser.add_argument("--normal-root", default=None)
    parser.add_argument("--split-root", default=None)
    parser.add_argument("--split", default="002")
    parser.add_argument("--num-videos", type=int, default=2)
    parser.add_argument("--num-eval-clips", type=int, default=2)
    args = parser.parse_args(argv)

    import torch
    from torch.utils.data import DataLoader

    from src.settings import dataset_paths, load_config
    from src.pipeline.ucf_splits import find_missing, load_fold

    config = load_config(args.config)
    paths = dataset_paths(config)
    anomaly_root = Path(args.anomaly_root) if args.anomaly_root else paths["anomaly_videos"]
    normal_root = Path(args.normal_root) if args.normal_root else paths["normal_videos"]
    split_root = Path(args.split_root) if args.split_root else (
        PROJECT_ROOT / "UCF_Crimes-Train-Test-Split" / "Action_Regnition_splits")

    train, _ = load_fold(split_root, args.split)
    present = [(r, l) for (r, l) in train
               if r not in find_missing(anomaly_root, normal_root, [r])][: args.num_videos]
    if not present:
        print("no usable videos found")
        return 2
    for mode in ("train", "eval"):
        ds = UCFClipDataset(present, anomaly_root, normal_root, mode=mode,
                            num_eval_clips=args.num_eval_clips, seed=0)
        loader = DataLoader(ds, batch_size=1, num_workers=0)
        clips, labels, pos = next(iter(loader))
        print(f"{mode}: dataset_items={len(ds)} batch={tuple(clips.shape)} "
              f"labels={labels.tolist()} videos={pos.tolist()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
