"""Phase 2B - Temporal activity-model backends.

All VideoMAE-specific code lives here so the activity model can be replaced
later without touching the extraction pipeline or evidence schema.

VideoMAEActivityModel runs the pretrained MCG-NJU/videomae-base
 Kinetics-400 checkpoint (inference only; never trained/fine-tuned here)
and reports the model's raw Kinetics labels verbatim. MockActivityModel
returns canned predictions for unit tests (no weights, no GPU).
"""

from __future__ import annotations

MODEL_ID = "MCG-NJU/videomae-base-finetuned-kinetics"
UCF_EVENT_MODEL_ID = "OPear/videomae-large-finetuned-UCF-Crime"

from src.evidence.models import (
    ActivityObservation,
    UCFEventObservation,
    activity_source_reference,
    frame_timestamp_seconds,
)
from src.pipeline.extract_evidence import sampling_step


def iter_window_frames(capture, video_fps: float, num_frames: int,
                       sampling_fps: float, window_hop: int):
    """Yield successive temporal windows while streaming a video.

    Reads sequentially and keeps only the current window in memory; the
    whole video is never loaded. Yields
    (window_index, frame_indices, frames_bgr, padded_frames). The final
    short window is edge-padded with its last frame.
    """
    if num_frames < 1:
        raise ValueError(f"invalid num_frames: {num_frames}")
    if window_hop < 1:
        raise ValueError(f"invalid window_hop: {window_hop}")
    stride = sampling_step(video_fps, sampling_fps)
    buffer: list = []       # (frame_index, frame_bgr) sampled at stride
    source_index = 0
    window_index = 0
    eof = False
    while not eof:
        ok, frame = capture.read()
        if not ok or frame is None:
            eof = True
        else:
            if source_index % stride == 0:
                buffer.append((source_index, frame))
            source_index += 1
        while len(buffer) >= num_frames or (eof and buffer):
            window = buffer[:num_frames]
            padded = 0
            if len(window) < num_frames:
                padded = num_frames - len(window)
                window = window + [window[-1]] * padded
            indices = [i for (i, _) in window]
            frames = [f for (_, f) in window]
            yield (window_index, indices, frames, padded)
            window_index += 1
            buffer = buffer[window_hop:]
            if eof and not buffer:
                break
        if eof:
            break


def window_timestamps(frame_indices: list, video_fps: float) -> tuple:
    """(start_time, end_time) of a window from its source frame indices."""
    if not frame_indices:
        raise ValueError("window has no frames")
    return (
        frame_timestamp_seconds(frame_indices[0], video_fps),
        frame_timestamp_seconds(frame_indices[-1], video_fps),
    )


def to_activity_observation(video_id: str, window_index: int, frame_indices: list,
                            start_time: float, end_time: float, prediction: dict,
                            model_name: str, model_version: str,
                            padded_frames: int = 0) -> ActivityObservation:
    """Convert a model prediction dict into an ActivityObservation."""
    return ActivityObservation(
        observation_id=f"{video_id}:a{window_index}",
        video_id=video_id,
        start_time=start_time,
        end_time=end_time,
        label=str(prediction["label"]),
        confidence=float(prediction["confidence"]),
        model_name=model_name,
        model_version=model_version,
        top_k=[
            {"label": str(e["label"]), "confidence": float(e["confidence"])}
            for e in prediction.get("top_k", [])
        ],
        frame_indices=list(frame_indices),
        padded_frames=padded_frames,
        source_reference=activity_source_reference(video_id, start_time, end_time),
    )


class MockActivityModel:
    """Test double: cycles canned (label, confidence, top_k) predictions."""

    def __init__(self, model_name="mock-activity", model_version="mock-0", predictions=()):
        self.model_name = model_name
        self.model_version = model_version
        self._predictions = list(predictions) or [
            {"label": "walking", "confidence": 0.7, "top_k": []}
        ]
        self.calls = 0

    def predict(self, frames_rgb, top_k: int) -> dict:
        pred = self._predictions[self.calls % len(self._predictions)]
        self.calls += 1
        return {
            "label": pred["label"],
            "confidence": float(pred["confidence"]),
            "top_k": [
                {"label": str(e["label"]), "confidence": float(e["confidence"])}
                for e in pred.get("top_k", [])[:top_k]
            ],
        }

    def close(self):
        pass


def _load_kinetics_state_dict(model, model_id: str) -> str:
    """Load the hub checkpoint's weights with faithful name mapping.

    Verified against the published checkpoint and installed transformers:
    the checkpoint config sets `qkv_bias=True`, so the model instantiates
    `query/key/value.bias`, but the checkpoint file only stores DeiT-style
    `q_bias`/`v_bias` tensors (the original code has no key bias). Stock
    `from_pretrained` therefore loads everything except the 24 learned
    query/value biases, which silently remain at HF default zero-init
    (verified weight-for-weight; same-window inference then collapses from
    a peaked 0.45 to near-uniform 0.03). Map q/v onto their true learned
    values and zero key.bias (= no bias, as in the original). Returns a
    note describing the remap for the run manifest.
    """
    from huggingface_hub import hf_hub_download

    try:
        from safetensors.torch import load_file
    except ImportError as exc:
        raise RuntimeError("safetensors is required for activity inference") from exc
    state = load_file(hf_hub_download(model_id, "model.safetensors"))
    remapped = {}
    for key, value in state.items():
        if key.endswith(".attention.attention.q_bias"):
            remapped[key[: -len("q_bias")] + "query.bias"] = value
        elif key.endswith(".attention.attention.v_bias"):
            remapped[key[: -len("v_bias")] + "value.bias"] = value
        else:
            remapped[key] = value
    # Drop checkpoint tensors whose shape disagrees with the model (e.g. a
    # 400-class Kinetics head when fine-tuning with a fresh 14-class head).
    # strict=False tolerates missing/unexpected keys, but not shape clashes.
    own_shapes = {k: tuple(v.shape) for k, v in model.state_dict().items()}
    dropped = sorted(k for k, v in remapped.items()
                     if k in own_shapes and tuple(v.shape) != own_shapes[k])
    for key in dropped:
        del remapped[key]
    missing, unexpected = model.load_state_dict(remapped, strict=False)
    zeroed = 0
    for name, param in model.named_parameters():
        if name.endswith(".attention.attention.key.bias"):
            param.data.zero_()
            zeroed += 1
    return (
        f"mapped q_bias->query.bias, v_bias->value.bias; "
        f"zeroed {zeroed} key.bias (absent upstream); "
        f"dropped shape-mismatched={dropped}; "
        f"load missing={len(missing)} unexpected={len(unexpected)}"
    )


class VideoMAEActivityModel:
    """Pretrained VideoMAE-Base/Kinetics-400 inference. device 'auto'
    (default) uses CUDA when available, otherwise CPU."""

    def __init__(self, model_id: str = MODEL_ID, device: str = "auto"):
        try:
            from transformers import (
                AutoConfig,
                AutoImageProcessor,
                AutoModelForVideoClassification,
            )
        except ImportError as exc:
            raise RuntimeError(
                "transformers is required for activity inference "
                "(pip install transformers)"
            ) from exc
        self.processor = AutoImageProcessor.from_pretrained(model_id)
        config = AutoConfig.from_pretrained(model_id)
        self._model = AutoModelForVideoClassification.from_config(config)
        self.model_name = model_id
        self.model_version = getattr(config, "_commit_hash", None) or "unknown"
        self.weight_notes = _load_kinetics_state_dict(self._model, model_id)
        self.device = self._resolve_device(device)
        self._model.to(self.device)
        self._model.eval()

    @staticmethod
    def _resolve_device(requested: str) -> str:
        requested = (requested or "auto").lower()
        if requested in ("auto", "cuda"):
            try:
                import torch

                if torch.cuda.is_available():
                    return "cuda"
                if requested == "cuda":
                    print("CUDA requested but unavailable; falling back to cpu")
            except ImportError:
                print("torch unavailable for device check; using cpu")
        return "cpu"

    def predict(self, frames_bgr, top_k: int) -> dict:
        """Predict from BGR frames (cv2 order); converts to RGB internally."""
        import numpy as np
        import torch

        # ascontiguousarray: channel-flip views have negative strides,
        # which torch cannot ingest.
        rgb = [np.ascontiguousarray(f[:, :, ::-1]) for f in frames_bgr]
        inputs = self.processor(rgb, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self.device)
        with torch.no_grad():
            logits = self._model(pixel_values=pixel_values).logits[0]
        probs = torch.softmax(logits, dim=0)
        k = max(1, min(int(top_k), probs.numel()))
        values, indices = torch.topk(probs, k=k)
        id2label = self._model.config.id2label
        top = [
            {"label": str(id2label[int(i)]), "confidence": float(v)}
            for (v, i) in zip(values.tolist(), indices.tolist())
        ]
        return {"label": top[0]["label"], "confidence": top[0]["confidence"], "top_k": top}

    def close(self):
        pass


def to_ucf_event_observation(video_id: str, window_index: int, frame_indices: list,
                             start_time: float, end_time: float, prediction: dict,
                             model_name: str, model_version: str,
                             padded_frames: int = 0) -> UCFEventObservation:
    """Convert a model prediction dict into a UCFEventObservation.

    Labels pass through verbatim from the model's own id2label mapping;
    ground-truth folder categories are never consulted here.
    """
    return UCFEventObservation(
        observation_id=f"{video_id}:e{window_index}",
        video_id=video_id,
        start_time=start_time,
        end_time=end_time,
        label=str(prediction["label"]),
        confidence=float(prediction["confidence"]),
        model_name=model_name,
        model_version=model_version,
        top_k=[
            {"label": str(e["label"]), "confidence": float(e["confidence"])}
            for e in prediction.get("top_k", [])
        ],
        frame_indices=list(frame_indices),
        padded_frames=padded_frames,
        source_reference=activity_source_reference(video_id, start_time, end_time),
    )


class UCFEventModel(VideoMAEActivityModel):
    """Pretrained UCF-Crime surveillance-event inference (no training).

    Same VideoMAE machinery as the Kinetics backend (processor, windowing
    contract, remap-aware weight loading); only the checkpoint — and hence
    the native id2label vocabulary — differs. Labels are stored as
    surveillance-event predictions, never as generic activities.
    """

    def __init__(self, model_id: str = UCF_EVENT_MODEL_ID, device: str = "auto"):
        super().__init__(model_id=model_id, device=device)
