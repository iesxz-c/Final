"""Phase 2A Part C - Pretrained object-detector backends.

YOLODetector wraps a pretrained Ultralytics YOLO model (inference only;
never trained here) and reports the model's native class names with
confidences. MockDetector returns canned detections for unit tests so no
weights or GPU are needed.
"""

from __future__ import annotations


class MockDetector:
    """Test double: returns fixed (class_name, confidence, bbox) tuples."""

    def __init__(self, model_name="mock-detector", detections=()):
        self.model_name = model_name
        self._detections = list(detections)

    def detect(self, frame, conf_threshold: float) -> list:
        return [
            {
                "class_name": name,
                "confidence": float(conf),
                "bounding_box": [float(v) for v in bbox],
            }
            for (name, conf, bbox) in self._detections
            if conf >= conf_threshold
        ]

    def close(self):
        pass


class YOLODetector:
    """Pretrained YOLO inference. torch device 'cpu' default, 'cuda' optional."""

    def __init__(self, weights_path: str, device: str = "cpu"):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "ultralytics is required for detection (pip install ultralytics)"
            ) from exc
        self._model = YOLO(weights_path)
        from pathlib import Path as _Path

        ckpt = self._model.ckpt_path
        self.model_name = _Path(ckpt).stem if ckpt else "yolo"
        self.device = self._resolve_device(device)

    @staticmethod
    def _resolve_device(requested: str) -> str:
        requested = (requested or "cpu").lower()
        if requested.startswith("cuda"):
            try:
                import torch

                if torch.cuda.is_available():
                    return requested
                print("CUDA requested but unavailable; falling back to cpu")
            except ImportError:
                print("torch unavailable for device check; using cpu")
        return "cpu"

    def detect(self, frame, conf_threshold: float) -> list:
        results = self._model.predict(frame, conf=conf_threshold, device=self.device,
                                      verbose=False)
        names = self._model.names
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0])
                detections.append(
                    {
                        "class_name": str(names.get(cls_id, cls_id)),
                        "confidence": float(box.conf[0]),
                        "bounding_box": [float(v) for v in box.xyxy[0].tolist()],
                    }
                )
        return detections

    def close(self):
        pass
