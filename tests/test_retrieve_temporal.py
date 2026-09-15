"""Phase 3B tests: temporal-context grouping over fused records + incidents.

Synthetic fixtures only - no model inference, no real data files."""

import json
import unittest

from src.pipeline import retrieve_temporal as T

VA = "anomaly/Robbery/vA.mp4"
VB = "anomaly/Shoplifting/vB.mp4"


def _evt(obs_id, label, conf, top_k=(), ref=""):
    return {"observation_id": obs_id, "label": label, "confidence": conf,
            "model_name": "m", "model_version": "v",
            "top_k": [{"label": lb, "confidence": cf} for (lb, cf) in top_k],
            "source_reference": ref or obs_id}


def _rec(evidence_id, video_id, start, end, events=(), ref=""):
    ref = ref or f"{video_id}@t={start}s-{end}s"
    return {"evidence_id": evidence_id, "video_id": video_id,
            "start_time": start, "end_time": end,
            "object_evidence": [], "generic_action_evidence": [],
            "surveillance_event_evidence": list(events),
            "source_references": [ref],
            "temporal_support": {}, "anomaly_score": 0.5}


def _inc(incident_id, video_id, start, end, members, hypotheses):
    return {"incident_id": incident_id, "video_id": video_id,
            "start_time": start, "end_time": end, "evidence_ids": list(members),
            "event_hypotheses": list(hypotheses), "num_windows": len(members),
            "span_seconds": end - start, "anomaly_score": 0.5,
            "schema_version": "phase2d/v1"}


def _fixtures():
    records = [
        _rec(f"{VA}:f0", VA, 0.0, 2.0,
             [_evt(f"{VA}:e0", "Fighting", 0.9, [("Fighting", 0.9)])]),
        _rec(f"{VA}:f1", VA, 2.0, 4.0,
             [_evt(f"{VA}:e1", "Assault", 0.8,
                   [("Assault", 0.8), ("Fighting", 0.2)])]),
        _rec(f"{VA}:f2", VA, 4.0, 6.0,
             [_evt(f"{VA}:e2", "Normal", 0.9, [("Normal", 0.9)])]),
        _rec(f"{VA}:f3", VA, 100.0, 102.0,
             [_evt(f"{VA}:e3", "Fighting", 0.7, [("Fighting", 0.7)])]),
        _rec(f"{VA}:f4", VA, 106.0, 108.0,
             [_evt(f"{VA}:e4", "Normal", 0.9, [("Normal", 0.9)])]),
        _rec(f"{VA}:f9", VA, 200.0, 202.0,
             [_evt(f"{VA}:e9", "Fighting", 0.5, [("Fighting", 0.5)])]),
        _rec(f"{VB}:g0", VB, 1.0, 3.0,
             [_evt(f"{VB}:e0", "Fighting", 0.6, [("Fighting", 0.6)])]),
        _rec(f"{VB}:g1", VB, 50.0, 52.0,
             [_evt(f"{VB}:e0b", "Normal", 0.9, [("Normal", 0.9)])]),
    ]
    incidents = [
        _inc(f"{VA}:i0", VA, 0.0, 6.0,
             [f"{VA}:f0", f"{VA}:f1", f"{VA}:f2"], ["Fighting", "Assault"]),
        _inc(f"{VA}:i1", VA, 100.0, 102.0, [f"{VA}:f3"], ["Fighting"]),
        _inc(f"{VB}:i0", VB, 1.0, 52.0, [f"{VB}:g0", f"{VB}:g1"], ["Fighting"]),
    ]
    return records, incidents


def _group_by_id(result):
    return {g["incident_id"]: g for g in result["groups"]}


class MatchAndGroupTest(unittest.TestCase):
    def test_query_match_returns_group(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting")
        self.assertTrue(res["groups"])
        ids = {r["evidence_id"] for g in res["groups"] for r in g["matched_evidence"]}
        self.assertIn(f"{VA}:f0", ids)

    def test_multiple_matches_one_incident(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting")
        grp = _group_by_id(res)[f"{VA}:i0"]
        matched = {r["evidence_id"] for r in grp["matched_evidence"]}
        self.assertEqual(matched, {f"{VA}:f0", f"{VA}:f1"})
        context = {r["evidence_id"] for r in grp["contextual_evidence"]}
        self.assertEqual(context, {f"{VA}:f2"})

    def test_multiple_incidents_same_video(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting")
        va_groups = [g for g in res["groups"] if g["video_id"] == VA]
        self.assertEqual([g["incident_id"] for g in va_groups],
                         [f"{VA}:i0", f"{VA}:i1"])

    def test_hits_different_videos_not_mixed(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting")
        videos = {g["video_id"] for g in res["groups"]}
        self.assertEqual(videos, {VA, VB})
        for grp in res["groups"]:
            for rec in grp["matched_evidence"] + grp["contextual_evidence"]:
                self.assertEqual(rec["video_id"], grp["video_id"])

    def test_contextual_non_matching(self):
        recs, incs = _fixtures()
        from src.pipeline import retrieve_evidence as R
        lone = [r for r in recs if r["evidence_id"] == f"{VA}:f2"]
        self.assertEqual(R.retrieve(lone, "Fighting"), [])
        res = T.retrieve_temporal(recs, incs, "Fighting")
        grp = _group_by_id(res)[f"{VA}:i0"]
        self.assertIn(f"{VA}:f2",
                      {r["evidence_id"] for r in grp["contextual_evidence"]})


class ExpansionTest(unittest.TestCase):
    def test_expansion_pulls_neighbor(self):
        recs, incs = _fixtures()
        plain = T.retrieve_temporal(recs, incs, "Fighting")
        grp = _group_by_id(plain)[f"{VA}:i1"]
        self.assertEqual(grp["contextual_evidence"], [])
        expanded = T.retrieve_temporal(recs, incs, "Fighting", context_seconds=5.0)
        grp = _group_by_id(expanded)[f"{VA}:i1"]
        self.assertIn(f"{VA}:f4",
                      {r["evidence_id"] for r in grp["contextual_evidence"]})

    def test_expansion_never_crosses_videos(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting", context_seconds=1000.0)
        for grp in res["groups"]:
            for rec in grp["contextual_evidence"]:
                self.assertEqual(rec["video_id"], grp["video_id"])

    def test_negative_expansion_rejected(self):
        recs, incs = _fixtures()
        with self.assertRaises(ValueError):
            T.retrieve_temporal(recs, incs, "Fighting", context_seconds=-1.0)


class FilterTest(unittest.TestCase):
    def test_source_filter(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting",
                                  sources=["surveillance_event"])
        self.assertTrue(res["groups"])
        res = T.retrieve_temporal(recs, incs, "Fighting", sources=["object"])
        self.assertEqual(res["groups"], [])
        self.assertEqual(res["unmapped_hits"], [])

    def test_timestamp_filter(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting", start_time=50.0)
        ids = {r["evidence_id"] for g in res["groups"] for r in g["matched_evidence"]}
        self.assertNotIn(f"{VA}:f0", ids)
        self.assertIn(f"{VA}:f3", ids)

    def test_limit_caps_groups(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting", limit=1)
        self.assertEqual(len(res["groups"]), 1)
        self.assertEqual(res["summary"]["incident_groups"], 1)


class EdgeTest(unittest.TestCase):
    def test_empty_query(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "")
        self.assertEqual(res["groups"], [])
        self.assertEqual(res["unmapped_hits"], [])
        self.assertEqual(res["summary"],
                         {"matched_hits": 0, "matched_records": 0,
                          "incident_groups": 0, "context_records": 0,
                          "unmapped_hits": 0})

    def test_unmapped_hit(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting")
        unmapped_ids = {h["evidence_id"] for h in res["unmapped_hits"]}
        self.assertIn(f"{VA}:f9", unmapped_ids)
        note = [h for h in res["unmapped_hits"]
                if h["evidence_id"] == f"{VA}:f9"][0]
        self.assertIn("mapping_note", note)
        self.assertEqual(note["matched_label"], "Fighting")
        self.assertEqual(res["summary"]["unmapped_hits"], len(res["unmapped_hits"]))

    def test_deterministic_ordering(self):
        recs, incs = _fixtures()
        first = T.retrieve_temporal(recs, incs, "Fighting", context_seconds=5.0)
        second = T.retrieve_temporal(list(reversed(recs)), list(reversed(incs)),
                                     "Fighting", context_seconds=5.0)
        self.assertEqual(json.dumps(first, sort_keys=True, default=str),
                         json.dumps(second, sort_keys=True, default=str))

    def test_no_duplicate_context(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting", context_seconds=1000.0)
        for grp in res["groups"]:
            ids = [r["evidence_id"] for r in grp["contextual_evidence"]]
            self.assertEqual(len(ids), len(set(ids)))
            matched = {r["evidence_id"] for r in grp["matched_evidence"]}
            self.assertTrue(matched.isdisjoint(ids))

    def test_preservation(self):
        recs, incs = _fixtures()
        by_id = {r["evidence_id"]: r for r in recs}
        res = T.retrieve_temporal(recs, incs, "Fighting")
        for grp in res["groups"]:
            for rec in grp["contextual_evidence"]:
                self.assertEqual(rec, by_id[rec["evidence_id"]])
            for rec in grp["matched_evidence"]:
                bare = {k: v for k, v in rec.items() if k != "matched_hits"}
                self.assertEqual(bare, by_id[rec["evidence_id"]])
                self.assertTrue(rec["matched_hits"])
                self.assertEqual(rec["source_references"],
                                 by_id[rec["evidence_id"]]["source_references"])

    def test_incident_ordering_by_start_time(self):
        recs, incs = _fixtures()
        res = T.retrieve_temporal(recs, incs, "Fighting")
        starts = [(g["incident_start_time"], g["incident_id"]) for g in res["groups"]]
        self.assertEqual(starts, sorted(starts))


if __name__ == "__main__":
    unittest.main()
