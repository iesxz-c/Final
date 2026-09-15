"""Phase 4B - Offline quantitative evaluator (no inference, no API, stdlib).

Computes only metrics defensible from existing artifacts:

- video_level_hypothesis_agreement: majority-vote UCF hypothesis vs the
  video-level dataset reference category (DESCRIPTIVE agreement, not
  crime-detection accuracy; folders are metadata, not model outputs).
- temporal_localization_pilot (n=6): tIoU of fused incident spans vs
  annotated anomaly intervals. Pilot only, not general accuracy.
- normal_controls: descriptive check of the five -1/-1 annotated normals.
- fusion_statistics: coverage/source-support descriptives from storage.
- structural_grounding: ID-existence, containment, dedupe, single-video
  invariants over fused artifacts (system checks, not accuracy).

Usage:
    python -m src.pipeline.evaluate_quantitative \
        --output data/evaluations/quantitative/metrics.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.evidence.fusion import is_non_normal_hypothesis

SCHEMA_VERSION = "phase4b/v1"

DEFAULT_SUBSET = "data/experiments/phase2_subset.json"
DEFAULT_INVENTORY = "data/inventory/videos.json"
DEFAULT_UCF_EVENTS = "data/evidence/phase2c_ucf/ucf_events.json"
DEFAULT_EVIDENCE = "data/evidence/fused/evidence.json"
DEFAULT_INCIDENTS = "data/evidence/fused/incidents.json"
DEFAULT_MANIFEST = "data/evidence/fused/manifest.json"
DEFAULT_ANNOTATIONS = "Temporal_Anomaly_Annotation_for_Testing_Videos.txt"
DEFAULT_OUTPUT = "data/evaluations/quantitative/metrics.json"


def _round4(value: float) -> float:
    return round(float(value), 4)


def majority_vote(labels: list) -> str | None:
    """Most common label; ties resolve to the lexicographically smallest."""
    if not labels:
        return None
    counts = Counter(labels)
    top = max(counts.values())
    return sorted(label for label, count in counts.items() if count == top)[0]


def confidence_weighted_vote(entries: list) -> str | None:
    """Label with the largest summed top-1 confidence; ties lexicographic."""
    if not entries:
        return None
    totals: dict = {}
    for label, confidence in entries:
        totals[label] = totals.get(label, 0.0) + float(confidence)
    top = max(totals.values())
    return sorted(label for label, total in totals.items() if total == top)[0]


def video_level_agreement(subset: list, events: list) -> dict:
    """Majority-vote hypothesis vs dataset reference category per video."""
    by_video: dict = {}
    for event in events:
        by_video.setdefault(event["video_id"], []).append(event)
    per_video, confusion = [], {}
    for entry in sorted(subset, key=lambda e: e["video_id"]):
        video_id = entry["video_id"]
        reference = entry.get("ground_truth_category", "Unknown")
        observations = by_video.get(video_id, [])
        top1 = [o["label"] for o in observations]
        majority = majority_vote(top1)
        weighted = confidence_weighted_vote([(o["label"], o["confidence"])
                                             for o in observations])
        per_video.append({"video_id": video_id, "reference_category": reference,
                          "windows": len(observations), "majority_hypothesis": majority,
                          "confidence_weighted_hypothesis": weighted,
                          "match": majority == reference})
        confusion.setdefault(reference, {}).setdefault(majority, 0)
        confusion[reference][majority] += 1
    by_class: dict = {}
    for item in per_video:
        slot = by_class.setdefault(item["reference_category"],
                                   {"videos": 0, "agreement": 0})
        slot["videos"] += 1
        slot["agreement"] += item["match"]
    for slot in by_class.values():
        slot["rate"] = _round4(slot["agreement"] / slot["videos"])
    matches = sum(item["match"] for item in per_video)
    return {"videos": len(per_video), "agreement_count": matches,
            "agreement_rate": _round4(matches / len(per_video)) if per_video else 0.0,
            "per_class_agreement": dict(sorted(by_class.items())),
            "confusion_reference_vs_majority": {k: dict(sorted(v.items()))
                                                for k, v in sorted(confusion.items())},
            "per_video": per_video}


def frames_to_seconds(frame: int, fps: float) -> float:
    """Convert an annotation frame number using verified inventory FPS."""
    if fps is None or fps <= 0:
        raise ValueError(f"invalid fps for conversion: {fps}")
    if frame < 0:
        raise ValueError(f"negative frame has no timestamp: {frame}")
    return _round4(frame / fps)


def tiou(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    """Temporal intersection-over-union of two closed intervals."""
    if a_end < a_start or b_end < b_start:
        raise ValueError(f"invalid interval: [{a_start}, {a_end}] vs [{b_start}, {b_end}]")
    intersection = max(0.0, min(a_end, b_end) - max(a_start, b_start))
    union = max(a_end, b_end) - min(a_start, b_start)
    return _round4(intersection / union) if union > 0 else 0.0


def load_annotations(path: str | Path) -> dict:
    """Parse '<file> <class> <start_frame> <end_frame> ...' annotation lines."""
    parsed: dict = {}
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 4:
                continue
            try:
                start, end = int(parts[2]), int(parts[3])
            except ValueError:
                continue
            parsed.setdefault(parts[0], []).append(
                {"label": parts[1], "start_frame": start, "end_frame": end})
    return parsed


def _fps_map(inventory: list) -> dict:
    mapping = {}
    for record in inventory:
        filename = record.get("path", "").split("/")[-1]
        if record.get("fps"):
            mapping[filename] = record["fps"]
    return mapping


def temporal_pilot(incidents: list, annotations: dict, fps_by_file: dict) -> dict:
    """tIoU of fused incident spans vs annotated anomaly intervals (n=6 pilot)."""
    by_video: dict = {}
    for incident in incidents:
        by_video.setdefault(incident["video_id"], []).append(incident)
    per_video = []
    for filename in sorted(annotations):
        segments = [s for s in annotations[filename]
                    if s["start_frame"] >= 0 and s["end_frame"] >= 0]
        if not segments:
            continue
        video_id = next((v for v in by_video if v.split("/")[-1] == filename), None)
        if video_id is None or filename not in fps_by_file:
            continue
        fps = fps_by_file[filename]
        for segment in segments:
            lo = frames_to_seconds(segment["start_frame"], fps)
            hi = frames_to_seconds(segment["end_frame"], fps)
            spans = [(i["start_time"], i["end_time"]) for i in by_video[video_id]]
            fused_lo = min(s for s, _ in spans)
            fused_hi = max(e for _, e in spans)
            per_video.append({
                "video_id": video_id,
                "annotation_label": segment["label"],
                "annotation_seconds": [lo, hi],
                "fused_span_seconds": [_round4(fused_lo), _round4(fused_hi)],
                "tiou": tiou(lo, hi, fused_lo, fused_hi),
            })
    scores = [item["tiou"] for item in per_video]
    return {"n": len(per_video),
            "mean_tiou": _round4(statistics.mean(scores)) if scores else 0.0,
            "median_tiou": _round4(statistics.median(scores)) if scores else 0.0,
            "min_tiou": _round4(min(scores)) if scores else 0.0,
            "max_tiou": _round4(max(scores)) if scores else 0.0,
            "per_video": per_video}


def normal_control_check(incidents: list, annotations: dict) -> dict:
    """Descriptive check: do -1/-1 annotated normals carry incident regions?"""
    by_video: dict = {}
    for incident in incidents:
        by_video.setdefault(incident["video_id"], []).append(incident)
    controls = []
    for filename in sorted(annotations):
        if not all(s["start_frame"] < 0 or s["end_frame"] < 0
                   for s in annotations[filename]):
            continue
        video_id = next((v for v in by_video if v.split("/")[-1] == filename), None)
        if video_id is None:
            continue  # annotated file outside our fused evidence universe
        regions = by_video.get(video_id, [])
        hypotheses = sorted({h for i in regions
                             for h in i.get("event_hypotheses", []) or []})
        controls.append({
            "video_id": video_id,
            "annotation": "-1/-1 (no anomaly interval)",
            "incident_regions": len(regions),
            "event_hypotheses": hypotheses,
            "non_normal_hypotheses": sorted(
                h for h in hypotheses if is_non_normal_hypothesis(h)),
        })
    with_regions = sum(1 for c in controls if c["incident_regions"] > 0)
    return {"controls": len(controls),
            "with_incident_regions": with_regions,
            "without_incident_regions": len(controls) - with_regions,
            "per_video": controls}


def fusion_statistics(evidence: list, incidents: list) -> dict:
    """Coverage and source-support descriptives from stored structures."""
    per_video = Counter(r["video_id"] for r in evidence)
    counts = sorted(per_video.values())
    spans = [_round4(i["end_time"] - i["start_time"]) for i in incidents]
    support = Counter()
    multi2 = multi3 = 0
    references = 0
    for record in evidence:
        kinds = [k for k, key in (("object", "object_evidence"),
                                  ("generic_action", "generic_action_evidence"),
                                  ("surveillance_event", "surveillance_event_evidence"))
                 if record.get(key)]
        for kind in kinds:
            support[kind] += 1
        multi2 += len(kinds) >= 2
        multi3 += len(kinds) >= 3
        references += len(record.get("source_references", []) or [])
    total = len(evidence)
    return {
        "videos": len(per_video),
        "fused_records": total,
        "records_per_video": _min_mean_median_max(counts),
        "incidents": len(incidents),
        "incident_duration_seconds": _min_mean_median_max(sorted(spans)),
        "records_with_object_evidence": _share(support["object"], total),
        "records_with_generic_action_evidence": _share(support["generic_action"], total),
        "records_with_surveillance_event_evidence": _share(
            support["surveillance_event"], total),
        "records_with_two_or_more_sources": _share(multi2, total),
        "records_with_all_three_sources": _share(multi3, total),
        "total_source_references": references,
    }


def _min_mean_median_max(values: list) -> dict:
    if not values:
        return {"min": 0, "mean": 0.0, "median": 0.0, "max": 0}
    return {"min": values[0], "mean": _round4(statistics.mean(values)),
            "median": _round4(statistics.median(values)), "max": values[-1]}


def _share(count: int, total: int) -> dict:
    return {"count": count, "rate": _round4(count / total) if total else 0.0}


def structural_grounding(evidence: list, incidents: list) -> dict:
    """ID-existence, containment, dedupe, single-video invariants (not accuracy)."""
    known = {r["evidence_id"] for r in evidence}
    by_id = {r["evidence_id"]: r for r in evidence}
    unknown = duplicates = cross_video = uncontained = checked = 0
    for incident in incidents:
        ids = list(incident.get("evidence_ids", []) or [])
        checked += 1
        unknown += sum(1 for e in ids if e not in known)
        duplicates += len(ids) != len(set(ids))
        videos = {by_id[e]["video_id"] for e in ids if e in by_id}
        cross_video += len(videos) > 1
        known_spans = [(by_id[e]["start_time"], by_id[e]["end_time"])
                       for e in ids if e in by_id]
        if known_spans:
            lo, hi = min(s for s, _ in known_spans), max(e for _, e in known_spans)
            uncontained += not (incident.get("start_time", lo) >= lo
                                and incident.get("end_time", hi) <= hi)
    return {"incidents_checked": checked,
            "unknown_evidence_ids": unknown,
            "duplicate_id_lists": duplicates,
            "cross_video_incidents": cross_video,
            "uncontained_incident_spans": uncontained,
            "evidence_id_existence_rate": _round4(
                1 - unknown / max(1, sum(len(i.get("evidence_ids", []) or [])
                                         for i in incidents)))}


def _read_json(path: Path):
    with Path(path).open("r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4B: offline quantitative metrics")
    parser.add_argument("--output", default=None)
    parser.add_argument("--subset", default=None)
    parser.add_argument("--inventory", default=None)
    parser.add_argument("--ucf-events", default=None)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--incidents", default=None)
    parser.add_argument("--annotations", default=None)
    args = parser.parse_args(argv)

    def _resolve(override, default):
        return Path(override) if override else PROJECT_ROOT / default

    try:
        subset = _read_json(_resolve(args.subset, DEFAULT_SUBSET))["videos"]
        inventory = _read_json(_resolve(args.inventory, DEFAULT_INVENTORY))
        events = _read_json(_resolve(args.ucf_events, DEFAULT_UCF_EVENTS))
        evidence = _read_json(_resolve(args.evidence, DEFAULT_EVIDENCE))
        incidents = _read_json(_resolve(args.incidents, DEFAULT_INCIDENTS))
        annotations = load_annotations(_resolve(args.annotations, DEFAULT_ANNOTATIONS))
    except (OSError, ValueError, KeyError) as exc:
        print(f"quantitative error: bad input: {exc}")
        return 2

    metrics = {
        "schema_version": SCHEMA_VERSION,
        "scope": {"videos": len(subset),
                  "note": "40-video Phase 2 subset; dataset categories are "
                          "video-level reference metadata and model outputs are "
                          "temporal hypotheses, never detections of confirmed crime."},
        "video_level_hypothesis_agreement": video_level_agreement(subset, events),
        "temporal_localization_pilot": temporal_pilot(
            incidents, annotations, _fps_map(inventory)),
        "normal_controls": normal_control_check(incidents, annotations),
        "fusion_statistics": fusion_statistics(evidence, incidents),
        "structural_grounding": structural_grounding(evidence, incidents),
    }
    output = Path(args.output) if args.output else PROJECT_ROOT / DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2, sort_keys=True)
    agree = metrics["video_level_hypothesis_agreement"]
    pilot = metrics["temporal_localization_pilot"]
    print(f"agreement: {agree['agreement_count']}/{agree['videos']} "
          f"({agree['agreement_rate']}) | pilot n={pilot['n']} "
          f"mean_tiou={pilot['mean_tiou']} -> {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
