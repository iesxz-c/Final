"""Phase 2D - Evidence fusion (no models, no training, no inference).

Combines three already-produced evidence streams into timestamp-aligned
fused records, incident regions, and per-video investigation scores:

- Phase 2A YOLO11n object detections (1 fps frame samples)
- Phase 2B Kinetics VideoMAE generic-action observations (~2 s windows)
- Phase 2C UCF-Crime VideoMAE surveillance-event observations (~2 s windows)

SEMANTIC RULE: model predictions are never converted into ground truth.
UCF-Crime labels are stored as *event hypotheses*. Scores are transparent
evidence-aggregation arithmetic, never calibrated probabilities of crime.

Temporal alignment
------------------
Anchor windows are the union of the two temporal models' window intervals
per video (in practice identical 16-frame / 8 fps / 2 s non-overlapping
windows). Original timestamps are preserved verbatim; a YOLO detection with
timestamp ``t`` attaches to the anchor window with ``start <= t <= end``.
Detections falling outside every window are counted (never silently
dropped) in the run stats.

Incident regions
----------------
Seeded by fused records holding at least one *non-normal* UCF event
hypothesis, then extended across temporally adjacent records (gap between
consecutive records ``<= max_gap_seconds``) while each record holds at
least one temporal observation (Kinetics or UCF, any label). The predicted
class may change across windows: e.g. 10-12 Fighting, 12-14 Fighting,
14-16 Assault, 16-18 Fighting merge into one 10-18 s region with
hypotheses {Fighting, Assault}. "Non-normal" is a label-name heuristic
(``NORMAL_LABELS``); it is a grouping convenience, not a finding.

Scores (exact formulas, aggregation only - NOT probabilities of crime)
----------------------------------------------------------------------
Record anomaly score::

    E = max confidence among non-normal UCF hypotheses in the record (0 if none)
    score = min(1.0, 0.6*E + 0.1*has_action + 0.1*has_object
                     + 0.1*(num_source_types - 1))

where has_action/has_object are 0/1 presence flags and num_source_types is
how many of {object, generic-action, surveillance-event} support the record.

Video investigation score::

    strength      = max fused-record score in the video (0 if no records)
    persistence   = min(1.0, total incident span seconds / 10.0)
    concentration = min(1.0, fused records inside incidents / 5.0)
    agreement     = fraction of incident records with >= 2 source types
                    (0 when the video has no incidents)
    score = min(1.0, 0.4*strength + 0.25*persistence
                     + 0.2*concentration + 0.15*agreement)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

FUSION_SCHEMA_VERSION = "phase2d/v1"

# Label-name heuristic for incident seeding. A grouping convenience only:
# anything outside this set is treated as a *candidate* non-normal event
# hypothesis for grouping purposes, never as a confirmed finding.
NORMAL_LABELS = frozenset({"normal", "normalvideos", "normal_videos", "background"})

RECORD_EVENT_WEIGHT = 0.6
RECORD_PRESENCE_WEIGHT = 0.1
RECORD_AGREEMENT_WEIGHT = 0.1

VIDEO_STRENGTH_WEIGHT = 0.4
VIDEO_PERSISTENCE_WEIGHT = 0.25
VIDEO_CONCENTRATION_WEIGHT = 0.2
VIDEO_AGREEMENT_WEIGHT = 0.15
VIDEO_PERSISTENCE_SATURATION_SECONDS = 10.0
VIDEO_CONCENTRATION_SATURATION_RECORDS = 5.0


def _round3(value: float) -> float:
    return round(float(value), 3)


def _round4(value: float) -> float:
    return round(float(value), 4)


def is_non_normal_hypothesis(label: str, normal_labels: frozenset = NORMAL_LABELS) -> bool:
    """Label-name check used only to seed incident grouping."""
    return str(label).strip().lower() not in normal_labels


def windows_overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> bool:
    """Inclusive interval overlap (shared boundary counts as overlap)."""
    return not (a_end < b_start or b_end < a_start)


@dataclass
class FusedEvidence:
    """One anchor temporal window with all supporting source evidence.

    Timestamps are copied verbatim from the source anchor window.
    """

    evidence_id: str  # f"{video_id}:f{index}", deterministic per video
    video_id: str
    start_time: float
    end_time: float
    object_evidence: list = field(default_factory=list)
    generic_action_evidence: list = field(default_factory=list)
    surveillance_event_evidence: list = field(default_factory=list)
    source_references: list = field(default_factory=list)
    temporal_support: dict = field(default_factory=dict)
    anomaly_score: float = 0.0
    schema_version: str = FUSION_SCHEMA_VERSION

    def __post_init__(self):
        if not self.evidence_id or not self.video_id:
            raise ValueError("evidence_id and video_id are required")
        if self.start_time < 0 or self.end_time < self.start_time:
            raise ValueError(f"invalid window [{self.start_time}, {self.end_time}]")
        if not 0.0 <= self.anomaly_score <= 1.0:
            raise ValueError(f"anomaly_score out of range: {self.anomaly_score}")
        if not self.source_references:
            raise ValueError("fused record without source references is forbidden")
        self.start_time = _round3(self.start_time)
        self.end_time = _round3(self.end_time)
        self.anomaly_score = _round4(self.anomaly_score)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FusedEvidence":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class IncidentRegion:
    """Temporally grouped fused records seeded by non-normal event hypotheses."""

    incident_id: str  # f"{video_id}:i{index}", deterministic per video
    video_id: str
    start_time: float
    end_time: float
    evidence_ids: list = field(default_factory=list)
    event_hypotheses: list = field(default_factory=list)  # distinct UCF labels
    num_windows: int = 0
    span_seconds: float = 0.0
    anomaly_score: float = 0.0  # max fused-record score in the region
    schema_version: str = FUSION_SCHEMA_VERSION

    def __post_init__(self):
        if not self.incident_id or not self.video_id:
            raise ValueError("incident_id and video_id are required")
        if self.start_time < 0 or self.end_time < self.start_time:
            raise ValueError(f"invalid span [{self.start_time}, {self.end_time}]")
        if not self.evidence_ids:
            raise ValueError("incident region without evidence is forbidden")
        if not 0.0 <= self.anomaly_score <= 1.0:
            raise ValueError(f"anomaly_score out of range: {self.anomaly_score}")
        self.start_time = _round3(self.start_time)
        self.end_time = _round3(self.end_time)
        self.span_seconds = _round3(self.span_seconds)
        self.anomaly_score = _round4(self.anomaly_score)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "IncidentRegion":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class VideoInvestigationScore:
    """Evidence-aggregation score for one video. NOT a probability of crime."""

    video_id: str
    score: float
    components: dict = field(default_factory=dict)  # strength/persistence/...
    num_fused_records: int = 0
    num_incidents: int = 0
    interpretation: str = (
        "evidence aggregation score; NOT a probability of crime"
    )
    schema_version: str = FUSION_SCHEMA_VERSION

    def __post_init__(self):
        if not self.video_id:
            raise ValueError("video_id is required")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score out of range: {self.score}")
        self.score = _round4(self.score)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "VideoInvestigationScore":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


def _action_entry(obs: dict) -> dict:
    return {
        "observation_id": obs["observation_id"],
        "label": str(obs["label"]),
        "confidence": _round4(obs["confidence"]),
        "model_name": obs.get("model_name", "unknown"),
        "model_version": obs.get("model_version", "unknown"),
        "source_reference": obs.get("source_reference", ""),
        "top_k": [
            {"label": str(e["label"]), "confidence": _round4(e["confidence"])}
            for e in obs.get("top_k", [])
        ],
    }


def _event_entry(obs: dict) -> dict:
    entry = _action_entry(obs)
    return entry  # same retained fields; container name marks it a hypothesis


def _object_entry(det: dict) -> dict:
    return {
        "detection_id": det["detection_id"],
        "observation_id": det["observation_id"],
        "timestamp_seconds": _round3(det["timestamp_seconds"]),
        "class_name": str(det["class_name"]),
        "confidence": _round4(det["confidence"]),
        "bounding_box": list(det.get("bounding_box", [])),
        "model_name": det.get("model_name", "unknown"),
    }


def record_anomaly_score(object_evidence: list, action_evidence: list,
                         event_evidence: list,
                         normal_labels: frozenset = NORMAL_LABELS) -> float:
    """Exact record formula (see module docstring)."""
    event_confs = [
        float(e["confidence"]) for e in event_evidence
        if is_non_normal_hypothesis(e["label"], normal_labels)
    ]
    present = sum(bool(x) for x in (object_evidence, action_evidence, event_evidence))
    score = (RECORD_EVENT_WEIGHT * (max(event_confs) if event_confs else 0.0)
             + RECORD_PRESENCE_WEIGHT * (1.0 if action_evidence else 0.0)
             + RECORD_PRESENCE_WEIGHT * (1.0 if object_evidence else 0.0)
             + RECORD_AGREEMENT_WEIGHT * max(0, present - 1))
    return _round4(min(1.0, score))


def fuse_video(video_id: str, anchor_windows: list,
               activities: list, events: list, detections: list,
               normal_labels: frozenset = NORMAL_LABELS) -> tuple:
    """Fuse one video's sources over its anchor windows.

    Returns (records, unaligned_detection_count). Records are sorted by
    start_time; evidence within a record is sorted by source observation id
    so output is deterministic.
    """
    records = []
    unaligned = 0
    for index, (start, end) in enumerate(anchor_windows):
        acts = sorted(
            (o for o in activities
             if o["video_id"] == video_id
             and windows_overlap(start, end, o["start_time"], o["end_time"])),
            key=lambda o: o["observation_id"],
        )
        evts = sorted(
            (o for o in events
             if o["video_id"] == video_id
             and windows_overlap(start, end, o["start_time"], o["end_time"])),
            key=lambda o: o["observation_id"],
        )
        dets = sorted(
            (d for d in detections
             if d["video_id"] == video_id and start <= d["timestamp_seconds"] <= end),
            key=lambda d: d["detection_id"],
        )
        if not acts and not evts and not dets:
            continue  # anchor with zero supporting evidence carries nothing
        action_entries = [_action_entry(o) for o in acts]
        event_entries = [_event_entry(o) for o in evts]
        object_entries = [_object_entry(d) for d in dets]
        refs = ([o.get("source_reference", "") for o in acts]
                + [o.get("source_reference", "") for o in evts]
                + [f"{d['video_id']}@t={_round3(d['timestamp_seconds'])}s"
                   for d in dets])
        refs = sorted({r for r in refs if r})
        support = {
            "num_observations": len(acts) + len(evts) + len(dets),
            "num_source_types": sum(bool(x) for x in (dets, acts, evts)),
            "span_seconds": _round3(end - start),
        }
        records.append(FusedEvidence(
            evidence_id=f"{video_id}:f{index}",
            video_id=video_id,
            start_time=start,
            end_time=end,
            object_evidence=object_entries,
            generic_action_evidence=action_entries,
            surveillance_event_evidence=event_entries,
            source_references=refs,
            temporal_support=support,
            anomaly_score=record_anomaly_score(
                object_entries, action_entries, event_entries, normal_labels),
        ))
    for det in detections:
        if det["video_id"] != video_id:
            continue
        if not any(s <= det["timestamp_seconds"] <= e for (s, e) in anchor_windows):
            unaligned += 1
    return records, unaligned


def collect_anchor_windows(activities: list, events: list, video_id: str) -> list:
    """Sorted unique temporal-model window intervals for one video."""
    bounds = {(o["start_time"], o["end_time"]) for o in activities + events
              if o["video_id"] == video_id}
    return sorted(bounds)


def _record_has_temporal(record: FusedEvidence) -> bool:
    return bool(record.generic_action_evidence or record.surveillance_event_evidence)


def _record_seed_hypotheses(record: FusedEvidence,
                            normal_labels: frozenset) -> list:
    return sorted({e["label"] for e in record.surveillance_event_evidence
                   if is_non_normal_hypothesis(e["label"], normal_labels)})


def group_incidents(video_id: str, records: list, max_gap_seconds: float = 1.0,
                    normal_labels: frozenset = NORMAL_LABELS) -> list:
    """Group adjacent fused records into incident regions.

    A region starts at a record holding a non-normal event hypothesis and
    extends while the next record starts within ``max_gap_seconds`` of the
    current end AND holds at least one temporal observation (any label).
    """
    ordered = sorted(records, key=lambda r: (r.start_time, r.end_time))
    incidents = []
    current = None
    for record in ordered:
        if current is None:
            if _record_seed_hypotheses(record, normal_labels):
                current = [record]
            continue
        gap = record.start_time - current[-1].end_time
        if gap <= max_gap_seconds and _record_has_temporal(record):
            current.append(record)
        else:
            incidents.append(current)
            current = ([record] if _record_seed_hypotheses(record, normal_labels)
                       else None)
    if current is not None:
        incidents.append(current)
    regions = []
    for i, group in enumerate(incidents):
        hypotheses = sorted({h for r in group
                             for h in _record_seed_hypotheses(r, normal_labels)})
        regions.append(IncidentRegion(
            incident_id=f"{video_id}:i{i}",
            video_id=video_id,
            start_time=group[0].start_time,
            end_time=max(r.end_time for r in group),
            evidence_ids=[r.evidence_id for r in group],
            event_hypotheses=hypotheses,
            num_windows=len(group),
            span_seconds=max(r.end_time for r in group) - group[0].start_time,
            anomaly_score=max(r.anomaly_score for r in group),
        ))
    return regions


def score_video(video_id: str, records: list, incidents: list) -> VideoInvestigationScore:
    """Exact video formula (see module docstring)."""
    in_incident = {eid for inc in incidents for eid in inc.evidence_ids}
    incident_records = [r for r in records if r.evidence_id in in_incident]
    strength = max((r.anomaly_score for r in records), default=0.0)
    total_span = sum(inc.span_seconds for inc in incidents)
    persistence = min(1.0, total_span / VIDEO_PERSISTENCE_SATURATION_SECONDS)
    concentration = min(1.0, len(incident_records) / VIDEO_CONCENTRATION_SATURATION_RECORDS)
    if incident_records:
        multi = sum(1 for r in incident_records
                    if r.temporal_support.get("num_source_types", 0) >= 2)
        agreement = multi / len(incident_records)
    else:
        agreement = 0.0
    score = min(1.0, VIDEO_STRENGTH_WEIGHT * strength
                + VIDEO_PERSISTENCE_WEIGHT * persistence
                + VIDEO_CONCENTRATION_WEIGHT * concentration
                + VIDEO_AGREEMENT_WEIGHT * agreement)
    return VideoInvestigationScore(
        video_id=video_id,
        score=_round4(score),
        components={
            "strength": _round4(strength),
            "persistence": _round4(persistence),
            "concentration": _round4(concentration),
            "agreement": _round4(agreement),
        },
        num_fused_records=len(records),
        num_incidents=len(incidents),
    )


def fuse_all(video_ids: list, activities: list, events: list, detections: list,
             max_gap_seconds: float = 1.0,
             normal_labels: frozenset = NORMAL_LABELS) -> dict:
    """Deterministic full fusion over the given video universe."""
    all_records, all_incidents, all_scores = [], [], []
    unaligned_total = 0
    for video_id in sorted(video_ids):
        windows = collect_anchor_windows(activities, events, video_id)
        if not windows and not any(d["video_id"] == video_id for d in detections):
            continue
        records, unaligned = fuse_video(
            video_id, windows, activities, events, detections, normal_labels)
        unaligned_total += unaligned
        incidents = group_incidents(video_id, records, max_gap_seconds, normal_labels)
        all_records.extend(records)
        all_incidents.extend(incidents)
        all_scores.append(score_video(video_id, records, incidents))
    all_scores.sort(key=lambda s: s.video_id)
    return {
        "records": all_records,
        "incidents": all_incidents,
        "scores": all_scores,
        "unaligned_detections": unaligned_total,
    }
