"""Phase 4B tests: voting, tIoU, annotations, fusion stats, grounding.

Synthetic fixtures only - no inference, no API, no real data files."""

import json
import unittest

from src.pipeline import evaluate_quantitative as Q


def _event(video_id, label, conf=0.8):
    return {"observation_id": video_id + ":e0", "video_id": video_id,
            "start_time": 0.0, "end_time": 2.0, "label": label,
            "confidence": conf, "model_name": "m", "model_version": "v",
            "top_k": [], "frame_indices": [], "padded_frames": 0,
            "source_reference": "r"}


class VotingTest(unittest.TestCase):
    def test_majority_vote(self):
        self.assertEqual(Q.majority_vote(["b", "a", "b"]), "b")
        self.assertIsNone(Q.majority_vote([]))

    def test_deterministic_tie_break(self):
        self.assertEqual(Q.majority_vote(["b", "a"]), "a")
        self.assertEqual(Q.majority_vote(["b", "a"]),
                         Q.majority_vote(["a", "b"]))

    def test_confidence_weighted_vote(self):
        entries = [("b", 0.9), ("a", 0.5), ("a", 0.5)]
        self.assertEqual(Q.confidence_weighted_vote(entries), "a")
        self.assertIsNone(Q.confidence_weighted_vote([]))

    def test_per_class_agreement(self):
        subset = [{"video_id": "v1", "ground_truth_category": "X"},
                  {"video_id": "v2", "ground_truth_category": "X"},
                  {"video_id": "v3", "ground_truth_category": "Y"}]
        events = [_event("v1", "X"), _event("v1", "X"),
                  _event("v2", "Z"), _event("v3", "Y")]
        result = Q.video_level_agreement(subset, events)
        self.assertEqual((result["videos"], result["agreement_count"]), (3, 2))
        self.assertEqual(result["agreement_rate"], round(2 / 3, 4))
        self.assertEqual(result["per_class_agreement"]["X"],
                         {"videos": 2, "agreement": 1, "rate": 0.5})

    def test_confusion_matrix(self):
        subset = [{"video_id": "v1", "ground_truth_category": "X"}]
        result = Q.video_level_agreement(subset, [_event("v1", "Z")])
        self.assertEqual(result["confusion_reference_vs_majority"], {"X": {"Z": 1}})
        self.assertFalse(result["per_video"][0]["match"])


class TemporalTest(unittest.TestCase):
    def test_frame_conversion(self):
        self.assertEqual(Q.frames_to_seconds(90, 30.0), 3.0)
        with self.assertRaises(ValueError):
            Q.frames_to_seconds(10, 0)
        with self.assertRaises(ValueError):
            Q.frames_to_seconds(-1, 30.0)

    def test_tiou_exact(self):
        self.assertEqual(Q.tiou(10.0, 20.0, 10.0, 20.0), 1.0)

    def test_tiou_partial(self):
        self.assertEqual(Q.tiou(10.0, 20.0, 15.0, 25.0), round(5 / 15, 4))

    def test_tiou_zero(self):
        self.assertEqual(Q.tiou(0.0, 5.0, 10.0, 15.0), 0.0)
        with self.assertRaises(ValueError):
            Q.tiou(5.0, 0.0, 0.0, 1.0)

    def test_normal_markers_skipped_in_pilot(self):
        annotations = {"a.mp4": [{"label": "Normal", "start_frame": -1, "end_frame": -1}]}
        result = Q.temporal_pilot([], annotations, {})
        self.assertEqual(result["n"], 0)

    def test_pilot_uses_inventory_fps(self):
        annotations = {"a.mp4": [{"label": "X", "start_frame": 0, "end_frame": 60}]}
        incidents = [{"video_id": "d/a.mp4", "start_time": 0.0, "end_time": 2.0,
                      "evidence_ids": []}]
        result = Q.temporal_pilot(incidents, annotations, {"a.mp4": 30.0})
        self.assertEqual(result["n"], 1)
        self.assertEqual(result["per_video"][0]["annotation_seconds"], [0.0, 2.0])
        self.assertEqual(result["per_video"][0]["tiou"], 1.0)


class FusionTest(unittest.TestCase):
    def _rec(self, evidence_id, objects=0, actions=0, events=0, refs=1):
        return {"evidence_id": evidence_id, "video_id": "v",
                "start_time": 0.0, "end_time": 2.0,
                "object_evidence": [{}] * objects,
                "generic_action_evidence": [{}] * actions,
                "surveillance_event_evidence": [{}] * events,
                "source_references": ["r"] * refs}

    def test_source_counting(self):
        records = [self._rec("a", objects=1), self._rec("b", events=1),
                   self._rec("c", actions=1, events=1)]
        stats = Q.fusion_statistics(records, [])
        self.assertEqual(stats["records_with_object_evidence"]["count"], 1)
        self.assertEqual(stats["records_with_surveillance_event_evidence"]["count"], 2)

    def test_multi_source_percentage(self):
        records = [self._rec("a", objects=1, actions=1, events=1),
                   self._rec("b", events=1)]
        stats = Q.fusion_statistics(records, [])
        self.assertEqual(stats["records_with_two_or_more_sources"]["rate"], 0.5)
        self.assertEqual(stats["records_with_all_three_sources"]["count"], 1)
        self.assertEqual(stats["total_source_references"], 2)
        self.assertEqual(stats["records_per_video"]["max"], 2)


class GroundingTest(unittest.TestCase):
    def _incident(self, evidence_ids, start=0.0, end=2.0, video="v"):
        return {"incident_id": "i", "video_id": video, "start_time": start,
                "end_time": end, "evidence_ids": list(evidence_ids),
                "event_hypotheses": [], "num_windows": len(evidence_ids),
                "span_seconds": end - start, "anomaly_score": 0.0,
                "schema_version": "phase2d/v1"}

    def _rec(self, evidence_id, video="v", start=0.0, end=2.0):
        return {"evidence_id": evidence_id, "video_id": video,
                "start_time": start, "end_time": end, "object_evidence": [],
                "generic_action_evidence": [], "surveillance_event_evidence": [],
                "source_references": ["r"]}

    def test_structural_grounding_clean(self):
        records = [self._rec("a"), self._rec("b")]
        result = Q.structural_grounding(records, [self._incident(["a", "b"])])
        self.assertEqual(result["unknown_evidence_ids"], 0)
        self.assertEqual(result["duplicate_id_lists"], 0)
        self.assertEqual(result["cross_video_incidents"], 0)
        self.assertEqual(result["uncontained_incident_spans"], 0)
        self.assertEqual(result["evidence_id_existence_rate"], 1.0)

    def test_grounding_violations_counted(self):
        records = [self._rec("a")]
        result = Q.structural_grounding(
            records, [self._incident(["a", "a", "ghost"], start=0.0, end=99.0)])
        self.assertEqual(result["unknown_evidence_ids"], 1)
        self.assertEqual(result["duplicate_id_lists"], 1)
        self.assertEqual(result["uncontained_incident_spans"], 1)

    def test_deterministic_output(self):
        records = [self._rec("b"), self._rec("a")]
        first = Q.fusion_statistics(records, [])
        second = Q.fusion_statistics(list(reversed(records)), [])
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
