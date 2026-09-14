"""Phase 2D tests: fusion alignment, grouping, hypotheses, preservation,
traceability, scoring, missing sources, determinism, schema. Synthetic
fixtures only - no model inference, no real data files."""

import unittest

from src.evidence import fusion as F
from src.evidence.fusion import (
    FusedEvidence,
    IncidentRegion,
    VideoInvestigationScore,
)


def _act(vid, idx, start, end, label="punching", conf=0.5):
    return {
        "observation_id": f"{vid}:a{idx}", "video_id": vid,
        "start_time": start, "end_time": end, "label": label,
        "confidence": conf, "model_name": "kinetics-mock", "model_version": "k0",
        "top_k": [{"label": label, "confidence": conf}],
        "source_reference": f"{vid}@t={start}s-{end}s",
    }


def _evt(vid, idx, start, end, label="Fighting", conf=0.7):
    obs = _act(vid, idx, start, end, label, conf)
    obs["observation_id"] = f"{vid}:e{idx}"
    obs["model_name"] = "ucf-mock"
    return obs


def _det(vid, idx, t, cls="person", conf=0.8):
    return {
        "detection_id": f"{vid}:f{idx}:d0",
        "observation_id": f"{vid}:f{idx}", "video_id": vid,
        "timestamp_seconds": t, "class_name": cls, "confidence": conf,
        "bounding_box": [1.0, 2.0, 3.0, 4.0], "model_name": "yolo-mock",
    }


class OverlapAlignmentTest(unittest.TestCase):
    def test_overlapping_and_adjacent_windows_attach(self):
        acts = [_act("v", 0, 10.0, 12.0)]
        evts = [_evt("v", 0, 12.0, 14.0)]  # boundary-touching counts
        dets = [_det("v", 0, 11.0), _det("v", 1, 13.5)]
        recs, unaligned = F.fuse_video(
            "v", [(10.0, 12.0), (12.0, 14.0)], acts, evts, dets)
        self.assertEqual(len(recs), 2)
        self.assertEqual(len(recs[0].generic_action_evidence), 1)
        self.assertEqual(len(recs[0].object_evidence), 1)
        self.assertEqual(len(recs[1].surveillance_event_evidence), 1)
        self.assertEqual(len(recs[1].object_evidence), 1)
        self.assertEqual(unaligned, 0)

    def test_detection_outside_all_windows_counted_not_dropped(self):
        recs, unaligned = F.fuse_video(
            "v", [(0.0, 2.0)], [], [], [_det("v", 9, 99.0)])
        self.assertEqual(len(recs), 0)
        self.assertEqual(unaligned, 1)


class AdjacentGroupingTest(unittest.TestCase):
    def _windowed(self, spans_labels):
        acts = [_act("v", i, s, e) for i, (s, e, _) in enumerate(spans_labels)]
        evts = [_evt("v", i, s, e, lbl) for i, (s, e, lbl) in enumerate(spans_labels)]
        recs, _ = F.fuse_video("v", [(s, e) for (s, e, _) in spans_labels],
                               acts, evts, [])
        return recs

    def test_changing_labels_merge_into_one_region(self):
        spans = [(10.0, 12.0, "Fighting"), (12.0, 14.0, "Fighting"),
                 (14.0, 16.0, "Assault"), (16.0, 18.0, "Fighting")]
        recs = self._windowed(spans)
        incs = F.group_incidents("v", recs)
        self.assertEqual(len(incs), 1)
        self.assertEqual((incs[0].start_time, incs[0].end_time), (10.0, 18.0))
        self.assertEqual(incs[0].num_windows, 4)

    def test_gap_splits_regions(self):
        spans = [(0.0, 2.0, "Fighting"), (10.0, 12.0, "Fighting")]
        incs = F.group_incidents("v", self._windowed(spans))
        self.assertEqual(len(incs), 2)

    def test_normal_only_windows_seed_nothing(self):
        spans = [(0.0, 2.0, "Normal"), (2.0, 4.0, "Normal")]
        incs = F.group_incidents("v", self._windowed(spans))
        self.assertEqual(incs, [])


class HypothesesTest(unittest.TestCase):
    def test_multiple_hypotheses_preserved(self):
        recs, _ = F.fuse_video(
            "v", [(0.0, 2.0), (2.0, 4.0)], [],
            [_evt("v", 0, 0.0, 2.0, "Fighting", 0.8),
             _evt("v", 1, 2.0, 4.0, "Assault", 0.6)], [])
        incs = F.group_incidents("v", recs)
        self.assertEqual(len(incs), 1)
        self.assertEqual(incs[0].event_hypotheses, ["Assault", "Fighting"])


class PreservationTest(unittest.TestCase):
    def test_timestamps_and_confidences_verbatim(self):
        acts = [_act("v", 0, 3.333333, 5.0, conf=0.123456)]
        evts = [_evt("v", 0, 3.333333, 5.0, conf=0.654321)]
        dets = [_det("v", 0, 4.0, conf=0.789)]
        recs, _ = F.fuse_video("v", [(3.333333, 5.0)], acts, evts, dets)
        rec = recs[0]
        self.assertEqual((rec.start_time, rec.end_time), (3.333, 5.0))
        self.assertEqual(rec.generic_action_evidence[0]["confidence"], 0.1235)
        self.assertEqual(rec.generic_action_evidence[0]["label"], "punching")
        self.assertEqual(rec.surveillance_event_evidence[0]["confidence"], 0.6543)
        self.assertEqual(rec.object_evidence[0]["confidence"], 0.789)
        self.assertEqual(rec.object_evidence[0]["bounding_box"], [1.0, 2.0, 3.0, 4.0])


class TraceabilityTest(unittest.TestCase):
    def test_every_record_resolves_to_sources(self):
        acts = [_act("v", 0, 0.0, 2.0)]
        evts = [_evt("v", 0, 0.0, 2.0)]
        dets = [_det("v", 0, 1.0)]
        recs, _ = F.fuse_video("v", [(0.0, 2.0)], acts, evts, dets)
        rec = recs[0]
        self.assertIn("v@t=0.0s-2.0s", rec.source_references[0])
        self.assertEqual(rec.generic_action_evidence[0]["observation_id"], "v:a0")
        self.assertEqual(rec.surveillance_event_evidence[0]["observation_id"], "v:e0")
        self.assertEqual(rec.object_evidence[0]["detection_id"], "v:f0:d0")
        self.assertGreaterEqual(rec.temporal_support["num_source_types"], 3)

    def test_record_without_refs_forbidden(self):
        with self.assertRaises(ValueError):
            FusedEvidence(evidence_id="v:f0", video_id="v", start_time=0.0,
                          end_time=2.0, source_references=[])

    def test_incident_without_evidence_forbidden(self):
        with self.assertRaises(ValueError):
            IncidentRegion(incident_id="v:i0", video_id="v", start_time=0.0,
                           end_time=2.0, evidence_ids=[])


class ScoreTest(unittest.TestCase):
    def test_record_formula_exact(self):
        # 0.6*0.8 + 0.1 + 0.1 + 0.1*(3-1) = 0.88
        score = F.record_anomaly_score([{"confidence": 0.9}],
                                       [{"confidence": 0.5}],
                                       [{"label": "Fighting", "confidence": 0.8}])
        self.assertAlmostEqual(score, 0.88, places=4)

    def test_normal_hypothesis_contributes_no_event_strength(self):
        score = F.record_anomaly_score([], [],
                                       [{"label": "Normal", "confidence": 0.99}])
        self.assertAlmostEqual(score, 0.0, places=4)  # no strength, no agreement

    def test_video_formula_exact(self):
        recs, _ = F.fuse_video(
            "v", [(0.0, 2.0), (2.0, 4.0)],
            [_act("v", 0, 0.0, 2.0), _act("v", 1, 2.0, 4.0)],
            [_evt("v", 0, 0.0, 2.0, "Fighting", 0.8),
             _evt("v", 1, 2.0, 4.0, "Fighting", 0.6)],
            [_det("v", 0, 1.0), _det("v", 1, 3.0)])
        incs = F.group_incidents("v", recs)
        scored = F.score_video("v", recs, incs)
        # strength .88; persistence 4/10=.4; concentration 2/5=.4; agreement 1.0
        expect = min(1.0, 0.4 * 0.88 + 0.25 * 0.4 + 0.2 * 0.4 + 0.15 * 1.0)
        self.assertAlmostEqual(scored.score, round(expect, 4), places=4)
        self.assertIn("strength", scored.components)
        self.assertIn("NOT a probability", scored.interpretation)

    def test_empty_video_scores_zero(self):
        scored = F.score_video("v", [], [])
        self.assertEqual(scored.score, 0.0)


class MissingSourceTest(unittest.TestCase):
    def test_yolo_only_still_fuses(self):
        windows = F.collect_anchor_windows([_act("v", 0, 0.0, 2.0)], [], "v")
        recs, _ = F.fuse_video("v", windows, [_act("v", 0, 0.0, 2.0)], [], [])
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].surveillance_event_evidence, [])
        incs = F.group_incidents("v", recs)
        self.assertEqual(incs, [])  # no UCF hypotheses -> no incidents, no crash

    def test_no_windows_but_detections_keeps_video(self):
        out = F.fuse_all(["v"], [], [], [_det("v", 0, 1.0)])
        self.assertEqual(len(out["scores"]), 1)
        self.assertEqual(out["scores"][0].score, 0.0)

    def test_unknown_video_ignored(self):
        out = F.fuse_all(["nope"], [_act("v", 0, 0.0, 2.0)], [], [])
        self.assertEqual(out["records"], [])


class DeterminismTest(unittest.TestCase):
    def test_repeated_runs_identical(self):
        acts = [_act("v", i, float(i * 2), float(i * 2 + 2)) for i in range(5)]
        evts = [_evt("v", i, float(i * 2), float(i * 2 + 2)) for i in range(5)]
        dets = [_det("v", i, float(i * 2 + 1)) for i in range(5)]
        first = F.fuse_all(["v"], acts, evts, dets)
        second = F.fuse_all(["v"], list(reversed(acts)), list(reversed(evts)),
                            list(reversed(dets)))
        self.assertEqual(
            [r.to_dict() for r in first["records"]],
            [r.to_dict() for r in second["records"]])
        self.assertEqual(
            [i.to_dict() for i in first["incidents"]],
            [i.to_dict() for i in second["incidents"]])
        self.assertEqual(first["scores"][0].score, second["scores"][0].score)


class SchemaTest(unittest.TestCase):
    def test_versioned_roundtrips(self):
        rec = FusedEvidence(evidence_id="v:f0", video_id="v", start_time=0.0,
                            end_time=2.0, source_references=["v@t=0.0s-2.0s"],
                            anomaly_score=0.5)
        self.assertEqual(FusedEvidence.from_dict(rec.to_dict()), rec)
        self.assertEqual(rec.schema_version, F.FUSION_SCHEMA_VERSION)
        inc = IncidentRegion(incident_id="v:i0", video_id="v", start_time=0.0,
                             end_time=2.0, evidence_ids=["v:f0"])
        self.assertEqual(IncidentRegion.from_dict(inc.to_dict()), inc)
        sc = VideoInvestigationScore(video_id="v", score=0.2)
        self.assertEqual(VideoInvestigationScore.from_dict(sc.to_dict()), sc)

    def test_rejects_bad_ranges(self):
        with self.assertRaises(ValueError):
            FusedEvidence(evidence_id="v:f0", video_id="v", start_time=2.0,
                          end_time=1.0, source_references=["x"])
        with self.assertRaises(ValueError):
            VideoInvestigationScore(video_id="v", score=1.5)


if __name__ == "__main__":
    unittest.main()
