"""Phase 3A tests: deterministic lexical retrieval over fused records.

Synthetic fixtures only - no model inference, no real data files."""

import unittest

from src.pipeline import retrieve_evidence as R


def _det(det_id, obs_id, t, cls, conf=0.9):
    return {"detection_id": det_id, "observation_id": obs_id,
            "timestamp_seconds": t, "class_name": cls, "confidence": conf,
            "bounding_box": [1.0, 2.0, 3.0, 4.0], "model_name": "yolo11n"}


def _obs(obs_id, label, conf, top_k=(), ref=""):
    return {"observation_id": obs_id, "label": label, "confidence": conf,
            "model_name": "m", "model_version": "v",
            "top_k": [{"label": lb, "confidence": cf} for (lb, cf) in top_k],
            "source_reference": ref or obs_id}


def _rec(evidence_id, video_id, start, end, objects=(), actions=(),
         events=(), score=0.5):
    return {"evidence_id": evidence_id, "video_id": video_id,
            "start_time": start, "end_time": end,
            "object_evidence": list(objects),
            "generic_action_evidence": list(actions),
            "surveillance_event_evidence": list(events),
            "source_references": [f"{video_id}@t={start}s-{end}s"],
            "temporal_support": {}, "anomaly_score": score}


def _fixtures():
    v1 = "anomaly/Assault/Assault001_x264.mp4"
    v2 = "anomaly/Fighting/Fighting002_x264.mp4"
    r1 = _rec(f"{v1}:f0", v1, 10.0, 12.0,
              objects=[_det(f"{v1}:f300:d0", f"{v1}:f300", 10.0, "person", 0.9)],
              actions=[_obs(f"{v1}:a5", "punching bag", 0.5)],
              events=[_obs(f"{v1}:e5", "Assault", 0.8,
                           [("Assault", 0.8), ("Fighting", 0.1)])],
              score=0.6)
    r2 = _rec(f"{v2}:f1", v2, 12.0, 14.0,
              objects=[_det(f"{v2}:f360:d0", f"{v2}:f360", 12.5, "car", 0.85)],
              actions=[_obs(f"{v2}:a6", "walking", 0.6)],
              events=[_obs(f"{v2}:e6", "Fighting", 0.7,
                           [("Fighting", 0.7), ("Assault", 0.2)])],
              score=0.55)
    r3 = _rec(f"{v1}:f2", v1, 20.0, 22.0,
              actions=[_obs(f"{v1}:a10", "sitting", 0.4)],
              events=[_obs(f"{v1}:e10", "Normal", 0.9,
                           [("Normal", 0.9)])],
              score=0.1)
    return [r1, r2, r3]


REQUIRED_KEYS = {"video_id", "evidence_id", "start_time", "end_time",
                 "matched_source", "matched_label", "confidence",
                 "source_reference"}


class ExactAndCaseInsensitiveTest(unittest.TestCase):
    def test_exact_label_match(self):
        hits = R.retrieve(_fixtures(), "Assault",
                          sources=[R.SOURCE_EVENT])
        labels = {(h["evidence_id"], h["matched_label"]) for h in hits}
        self.assertIn((_fixtures()[0]["evidence_id"], "Assault"), labels)

    def test_case_insensitive_matches_exact(self):
        lower = R.retrieve(_fixtures(), "assault")
        upper = R.retrieve(_fixtures(), "ASSAULT")
        self.assertEqual(
            [(h["evidence_id"], h["matched_label"]) for h in lower],
            [(h["evidence_id"], h["matched_label"]) for h in upper])
        self.assertTrue(lower)

    def test_top_k_match_reports_top_k_label(self):
        hits = R.retrieve(_fixtures(), "Fighting",
                          sources=[R.SOURCE_EVENT])
        by_record = {}
        for h in hits:
            by_record.setdefault(h["evidence_id"], []).append(h["matched_label"])
        self.assertIn("Fighting", by_record[_fixtures()[0]["evidence_id"]])
        self.assertIn("Fighting", by_record[_fixtures()[1]["evidence_id"]])


class SourceMatchTest(unittest.TestCase):
    def test_yolo_object_match(self):
        hits = R.retrieve(_fixtures(), "person")
        self.assertTrue(hits)
        self.assertTrue(all(h["matched_source"] == R.SOURCE_OBJECT for h in hits))
        self.assertEqual(hits[0]["matched_label"], "person")
        self.assertEqual(hits[0]["confidence"], 0.9)
        self.assertIn("@t=10.0s", hits[0]["source_reference"])

    def test_generic_action_match(self):
        hits = R.retrieve(_fixtures(), "walking")
        self.assertTrue(any(h["matched_source"] == R.SOURCE_ACTION
                            and h["matched_label"] == "walking"
                            for h in hits))

    def test_surveillance_event_match(self):
        hits = R.retrieve(_fixtures(), "Assault",
                          sources=[R.SOURCE_EVENT])
        self.assertTrue(all(h["matched_source"] == R.SOURCE_EVENT for h in hits))

    def test_source_filter_restricts(self):
        hits = R.retrieve(_fixtures(), "a", sources=[R.SOURCE_OBJECT])
        self.assertTrue(hits)
        self.assertTrue(all(h["matched_source"] == R.SOURCE_OBJECT for h in hits))


class FilterTest(unittest.TestCase):
    def test_video_filter(self):
        recs = _fixtures()
        hits = R.retrieve(recs, "person", video_id=recs[1]["video_id"])
        self.assertEqual(hits, [])
        hits = R.retrieve(recs, "person", video_id=recs[0]["video_id"])
        self.assertTrue(hits)
        self.assertTrue(all(h["video_id"] == recs[0]["video_id"] for h in hits))

    def test_timestamp_filter_excludes(self):
        recs = _fixtures()
        hits = R.retrieve(recs, "Fighting", sources=[R.SOURCE_EVENT],
                          start_time=14.5)
        ids = {h["evidence_id"] for h in hits}
        self.assertNotIn(recs[1]["evidence_id"], ids)
        hits = R.retrieve(recs, "Fighting", sources=[R.SOURCE_EVENT],
                          end_time=11.0)
        ids = {h["evidence_id"] for h in hits}
        self.assertNotIn(recs[1]["evidence_id"], ids)

    def test_timestamp_filter_includes_overlap(self):
        recs = _fixtures()
        hits = R.retrieve(recs, "Fighting", sources=[R.SOURCE_EVENT],
                          start_time=13.0, end_time=13.5)
        self.assertTrue(any(h["evidence_id"] == recs[1]["evidence_id"]
                            for h in hits))


class DeterminismTest(unittest.TestCase):
    def test_same_query_same_ordering(self):
        recs = _fixtures()
        first = R.retrieve(recs, "a")
        second = R.retrieve(list(reversed(recs)), "a")
        self.assertEqual(
            [(h["evidence_id"], h["matched_source"], h["matched_label"])
             for h in first],
            [(h["evidence_id"], h["matched_source"], h["matched_label"])
             for h in second])

    def test_exact_before_substring_and_confidence_desc(self):
        recs = _fixtures()
        hits = R.retrieve(recs, "Assault", sources=[R.SOURCE_EVENT])
        exact_first = [h["matched_label"].lower() == "assault" for h in hits]
        self.assertTrue(exact_first[0])
        confs = [h["confidence"] for h in hits
                 if h["matched_label"].lower() == "assault"]
        self.assertEqual(confs, sorted(confs, reverse=True))

    def test_limit_caps_without_reordering(self):
        recs = _fixtures()
        all_hits = R.retrieve(recs, "a")
        capped = R.retrieve(recs, "a", limit=1)
        self.assertEqual(len(capped), 1)
        self.assertEqual(capped[0], all_hits[0])


class EmptyAndTraceabilityTest(unittest.TestCase):
    def test_empty_query_matches_nothing(self):
        self.assertEqual(R.retrieve(_fixtures(), ""), [])
        self.assertEqual(R.retrieve(_fixtures(), "   "), [])

    def test_no_match_query(self):
        self.assertEqual(R.retrieve(_fixtures(), "zzz-no-such-label"), [])

    def test_result_schema_and_traceability(self):
        recs = _fixtures()
        ids = {r["evidence_id"] for r in recs}
        by_id = {r["evidence_id"]: r for r in recs}
        for hit in R.retrieve(recs, "a"):
            self.assertTrue(REQUIRED_KEYS.issubset(hit))
            self.assertIn(hit["evidence_id"], ids)
            src = by_id[hit["evidence_id"]]
            self.assertEqual(hit["video_id"], src["video_id"])
            self.assertEqual(hit["start_time"], src["start_time"])
            self.assertEqual(hit["end_time"], src["end_time"])
            self.assertTrue(hit["source_reference"])


if __name__ == "__main__":
    unittest.main()
