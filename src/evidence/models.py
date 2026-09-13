"""Phase 2A/2B - Structured evidence domain models.

RESEARCH RULE: `ground_truth_category` is dataset metadata only. It must
never be used as, or converted into, a model-generated activity/event label.
Model observations (FrameObservation, ObjectDetection, ActivityObservation,
and later Event) carry only what inference actually produced. In particular,
ActivityObservation.label always holds the raw activity-model label
(e.g. a Kinetics-400 class name), never a dataset folder name.

The schema is versioned (EVIDENCE_SCHEMA_VERSION) and all models use
optional-with-default fields plus to_dict/from_dict, so future models
(ActivityObservation, PersonTrack, Event, EvidenceReference) can be added
without breaking these.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

EVIDENCE_SCHEMA_VERSION = "phase2a/v1"


def _round3(value) -> float | None:
    return None if value is None else round(float(value), 3)


@dataclass
class VideoRecord:
    """One experimental video. Category is ground truth metadata, not output."""

    video_id: str
    source_type: str  # "anomaly" | "normal"
    ground_truth_category: str  # dataset folder label; NEVER an inferred activity
    dataset_root: str
    path: str  # relative to dataset_root
    duration_seconds: float | None = None
    fps: float | None = None
    width: int | None = None
    height: int | None = None
    frame_count: int | None = None
    file_size_bytes: int = 0
    format: str = "mp4"
    schema_version: str = EVIDENCE_SCHEMA_VERSION

    def __post_init__(self):
        if not self.video_id:
            raise ValueError("video_id is required")
        if self.source_type not in ("anomaly", "normal"):
            raise ValueError(f"bad source_type: {self.source_type!r}")
        if not self.ground_truth_category:
            raise ValueError("ground_truth_category is required")
        self.duration_seconds = _round3(self.duration_seconds)
        self.fps = _round3(self.fps)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "VideoRecord":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})

    def absolute_path(self) -> str:
        from pathlib import Path

        return str(Path(self.dataset_root) / self.path)


@dataclass
class FrameObservation:
    """One sampled frame: timestamp + frame index, no interpretation."""

    observation_id: str  # f"{video_id}:f{frame_index}", deterministic
    video_id: str
    timestamp_seconds: float
    frame_index: int
    source_reference: str  # e.g. "anomaly/Fighting/x.mp4@t=12.0s#f360"
    sample_fps: float = 1.0
    schema_version: str = EVIDENCE_SCHEMA_VERSION

    def __post_init__(self):
        if not self.observation_id or not self.video_id:
            raise ValueError("observation_id and video_id are required")
        if self.frame_index < 0:
            raise ValueError("frame_index must be >= 0")
        if self.timestamp_seconds < 0:
            raise ValueError("timestamp_seconds must be >= 0")
        self.timestamp_seconds = _round3(self.timestamp_seconds)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FrameObservation":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class ObjectDetection:
    """One object seen by a pretrained detector. Stores the model's own
    class name and confidence verbatim; makes no weapon-reliability claims."""

    detection_id: str  # f"{observation_id}:d{index}", deterministic
    observation_id: str
    video_id: str
    timestamp_seconds: float
    class_name: str  # model-native label, e.g. "person"
    confidence: float
    bounding_box: list = field(default_factory=list)  # [x1, y1, x2, y2] pixels
    model_name: str = "unknown"
    model_conf_threshold: float = 0.0
    schema_version: str = EVIDENCE_SCHEMA_VERSION

    def __post_init__(self):
        if not self.detection_id or not self.observation_id or not self.video_id:
            raise ValueError("detection/observation/video ids are required")
        if not self.class_name:
            raise ValueError("class_name is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence out of range: {self.confidence}")
        if len(self.bounding_box) != 4:
            raise ValueError("bounding_box must be [x1, y1, x2, y2]")
        self.timestamp_seconds = _round3(self.timestamp_seconds)
        self.confidence = round(float(self.confidence), 4)
        self.bounding_box = [round(float(v), 1) for v in self.bounding_box]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ObjectDetection":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def observation_source_reference(video_id: str, timestamp_seconds: float, frame_index: int) -> str:
    return f"{video_id}@t={round(float(timestamp_seconds), 3)}s#f{frame_index}"


def activity_source_reference(video_id: str, start_time: float, end_time: float) -> str:
    return (
        f"{video_id}@t={round(float(start_time), 3)}s"
        f"-{round(float(end_time), 3)}s"
    )


@dataclass
class ActivityObservation:
    """One temporal-window activity prediction from a video model.

    `label` is the model's raw class name (e.g. Kinetics-400); it is never
    derived from the dataset's ground-truth category folders.
    """

    observation_id: str  # f"{video_id}:a{window_index}", deterministic
    video_id: str
    start_time: float
    end_time: float
    label: str  # raw model label, verbatim
    confidence: float
    model_name: str = "unknown"
    model_version: str = "unknown"
    top_k: list = field(default_factory=list)  # [{"label": str, "confidence": float}]
    frame_indices: list = field(default_factory=list)  # sampled source frames
    padded_frames: int = 0  # edge-repeated frames when a window ran short
    source_reference: str = ""
    schema_version: str = EVIDENCE_SCHEMA_VERSION

    def __post_init__(self):
        if not self.observation_id or not self.video_id:
            raise ValueError("observation_id and video_id are required")
        if not self.label:
            raise ValueError("label is required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence out of range: {self.confidence}")
        if self.start_time < 0 or self.end_time < self.start_time:
            raise ValueError(
                f"invalid window [{self.start_time}, {self.end_time}]"
            )
        if self.padded_frames < 0:
            raise ValueError("padded_frames must be >= 0")
        for entry in self.top_k:
            if not 0.0 <= float(entry["confidence"]) <= 1.0:
                raise ValueError(f"top-k confidence out of range: {entry}")
        self.start_time = _round3(self.start_time)
        self.end_time = _round3(self.end_time)
        self.confidence = round(float(self.confidence), 4)
        self.top_k = [
            {"label": str(e["label"]), "confidence": round(float(e["confidence"]), 4)}
            for e in self.top_k
        ]
        self.frame_indices = [int(i) for i in self.frame_indices]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ActivityObservation":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def frame_timestamp_seconds(frame_index: int, video_fps: float) -> float:
    """Original video timestamp of a frame. video_fps must be positive."""
    if video_fps is None or video_fps <= 0:
        raise ValueError(f"invalid video_fps: {video_fps}")
    if frame_index < 0:
        raise ValueError("frame_index must be >= 0")
    return round(frame_index / video_fps, 3)
