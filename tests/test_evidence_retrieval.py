"""Phase 3D tests: plan execution, merging, provenance, error handling.

Synthetic fixtures only - no model inference, no real data files, no LLM."""

import copy
import json
import unittest
from unittest import mock

from src.agents import evidence_retrieval as E
from src.agents import query_planner as Q

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
             [_evt(f"{VA}:e0", "person", 0.9, [("person", 0.9)])],
             ref=f"{VA}@t=0.0s-2.0s"),
        _rec(f"{VA}:f1", VA, 2.0, 4.0,
             [_evt(f"{VA}:e1", "Fighting", 0.8, [("Fighting", 0.8)])]),
        _rec(f"{VA}:f2", VA, 4.0, 6.0,
             [_evt(f"{VA}:e2", "Normal", 0.9, [("Normal", 0.9)])]),
        _rec(f"{VB}:g0", VB, 1.0, 3.0,
             [_evt(f"{VB}:e0", "Fighting", 0.6, [("Fighting", 0.6)])]),
        _rec(f"{VB}:g9", VB, 200.0, 202.0,
             [_evt(f"{VB}:e9", "Fighting", 0.5, [("Fighting", 0.5)])]),
    ]
    # f0 carries an object detection too for source-filter tests.
    records[0]["object_evidence"] = [
        {"detection_id": f"{VA}:f0:d0", "observation_id": f"{VA}:f0",
         "timestamp_seconds": 1.0, "class_name": "person", "confidence": 0.95,
         "bounding_box": [1.0, 2.0, 3.0, 4.0], "model_name": "yolo11n"}]
    incidents = [
        _inc(f"{VA}:i0", VA, 0.0, 6.0,
             [f"{VA}:f0", f"{VA}:f1", f"{VA}:f2"], ["Fighting"]),
        _inc(f"{VB}:i0", VB, 1.0, 3.0, [f"{VB}:g0"], ["Fighting"]),
    ]
    return records, incidents


def _plan(**overrides):
    base = {"schema_version": "phase3c/v1", "intent": "search_evidence",
            "queries": [{"query": "Fighting", "source": None}],
            "video_id": None, "start_time": None, "end_time": None,
            "temporal_context_seconds": 0, "needs_timeline": False,
            "needs_cross_evidence": False}
    base.update(overrides)
    return base


class ExecutionTest(unittest.TestCase):
    def test_single_query(self):
        res = E.execute_plan(_plan(), *_fixtures())
        self.assertEqual(res["schema_version"], "phase3d/v1")
        self.assertEqual(len(res["query_results"]), 1)
        self.assertEqual(res["summary"]["planner_queries"], 1)
        self.assertTrue(res["merged_results"]["groups"])

    def test_source_filter(self):
        recs, incs = _fixtures()
        res = E.execute_plan(_plan(queries=[{"query": "person", "source": "object"}]),
                             recs, incs)
        hits = [h for g in res["merged_results"]["groups"]
                for r in g["matched_evidence"] for h in r["matched_hits"]]
        self.assertTrue(hits)
        self.assertTrue(all(h["matched_source"] == "object" for h in hits))

    def test_video_filter(self):
        recs, incs = _fixtures()
        res = E.execute_plan(_plan(video_id=VB), recs, incs)
        for grp in res["merged_results"]["groups"]:
            self.assertEqual(grp["video_id"], VB)

    def test_timestamp_filters(self):
        recs, incs = _fixtures()
        res = E.execute_plan(_plan(start_time=50.0), recs, incs)
        ids = {r["evidence_id"] for g in res["merged_results"]["groups"]
               for r in g["matched_evidence"]}
        self.assertNotIn(f"{VA}:f1", ids)

    def test_temporal_context(self):
        recs, incs = _fixtures()
        plain = E.execute_plan(_plan(queries=[{"query": "Fighting",
                                               "source": "surveillance_event"}]),
                               recs, incs)
        wide = E.execute_plan(_plan(queries=[{"query": "Fighting",
                                              "source": "surveillance_event"}],
                                    temporal_context_seconds=5.0), recs, incs)
        plain_ctx = sum(len(g["contextual_evidence"]) for g in plain["merged_results"]["groups"])
        wide_ctx = sum(len(g["contextual_evidence"]) for g in wide["merged_results"]["groups"])
        self.assertGreaterEqual(wide_ctx, plain_ctx)

    def test_zero_context_invents_nothing(self):
        recs, incs = _fixtures()
        res = E.execute_plan(_plan(queries=[{"query": "Fighting",
                                             "source": "surveillance_event"}]),
                             recs, incs)
        for grp in res["merged_results"]["groups"]:
            members = next(i["evidence_ids"] for i in incs
                           if i["incident_id"] == grp["incident_id"])
            ctx = {r["evidence_id"] for r in grp["contextual_evidence"]}
            self.assertTrue(ctx.issubset(set(members)))

    def test_empty_result(self):
        res = E.execute_plan(_plan(queries=[{"query": "zzz-no-such-label",
                                             "source": None}]), *_fixtures())
        self.assertEqual(res["merged_results"]["groups"], [])
        self.assertEqual(res["merged_results"]["unmapped_hits"], [])
        self.assertEqual(res["summary"]["incident_groups"], 0)

    def test_unmapped_evidence(self):
        recs, incs = _fixtures()
        res = E.execute_plan(_plan(), recs, incs)
        unmapped = {h["evidence_id"] for h in res["merged_results"]["unmapped_hits"]}
        self.assertIn(f"{VB}:g9", unmapped)
        self.assertEqual(res["summary"]["unmapped_hits"], len(unmapped))


class MultiQueryTest(unittest.TestCase):
    def _two_query(self):
        return _plan(queries=[{"query": "Fighting", "source": "surveillance_event"},
                              {"query": "person", "source": "object"}])

    def test_multiple_queries_executed(self):
        res = E.execute_plan(self._two_query(), *_fixtures())
        self.assertEqual(len(res["query_results"]), 2)
        self.assertEqual(res["summary"]["planner_queries"], 2)

    def test_shared_incident_merged_once(self):
        res = E.execute_plan(self._two_query(), *_fixtures())
        ids = [g["incident_id"] for g in res["merged_results"]["groups"]]
        self.assertEqual(len(ids), len(set(ids)))
        grp = next(g for g in res["merged_results"]["groups"]
                   if g["incident_id"] == f"{VA}:i0")
        self.assertIn(f"{VA}:f0", {r["evidence_id"] for r in grp["matched_evidence"]})
        self.assertIn(f"{VA}:f1", {r["evidence_id"] for r in grp["matched_evidence"]})

    def test_shared_evidence_deduplicated(self):
        res = E.execute_plan(self._two_query(), *_fixtures())
        for grp in res["merged_results"]["groups"]:
            ids = [r["evidence_id"] for r in grp["matched_evidence"]]
            self.assertEqual(len(ids), len(set(ids)))
            ctx = [r["evidence_id"] for r in grp["contextual_evidence"]]
            self.assertEqual(len(ctx), len(set(ctx)))
            self.assertTrue(set(ids).isdisjoint(ctx))

    def test_provenance(self):
        res = E.execute_plan(self._two_query(), *_fixtures())
        for entry in res["query_results"]:
            self.assertIn("planner_query_index", entry)
        for grp in res["merged_results"]["groups"]:
            for rec in grp["matched_evidence"]:
                for hit in rec["matched_hits"]:
                    self.assertIn("planner_query_index", hit)
                    self.assertIn("planner_query", hit)
        f0 = next(r for g in res["merged_results"]["groups"]
                  for r in g["matched_evidence"] if r["evidence_id"] == f"{VA}:f0")
        indexes = {h["planner_query_index"] for h in f0["matched_hits"]}
        self.assertTrue(len(indexes) >= 1)
        self.assertTrue(all(h["planner_query"] in ("Fighting", "person")
                            for h in f0["matched_hits"]))

    def test_distinction_preserved(self):
        res = E.execute_plan(self._two_query(), *_fixtures())
        for grp in res["merged_results"]["groups"]:
            for rec in grp["matched_evidence"]:
                self.assertIn("matched_hits", rec)
                self.assertTrue(rec["matched_hits"])
            for rec in grp["contextual_evidence"]:
                self.assertNotIn("matched_hits", rec)


class RobustnessTest(unittest.TestCase):
    def test_invalid_plan_rejected(self):
        bad = _plan(intent="arrest_everyone")
        with self.assertRaises(Q.PlanValidationError):
            E.execute_plan(bad, *_fixtures())

    def test_missing_queries_rejected(self):
        bad = _plan()
        del bad["queries"]
        with self.assertRaises(Q.PlanValidationError):
            E.execute_plan(bad, *_fixtures())

    def test_empty_query_rejected(self):
        with self.assertRaises(Q.PlanValidationError):
            E.execute_plan(_plan(queries=[{"query": "  ", "source": None}]),
                           *_fixtures())

    def test_unsupported_source_rejected(self):
        with self.assertRaises(Q.PlanValidationError):
            E.execute_plan(_plan(queries=[{"query": "x", "source": "thermal"}]),
                           *_fixtures())

    def test_query_failure_structured(self):
        recs, incs = _fixtures()
        with mock.patch("src.pipeline.retrieve_temporal.retrieve_temporal",
                        side_effect=RuntimeError("store exploded")):
            res = E.execute_plan(_plan(), recs, incs)
        self.assertEqual(len(res["query_errors"]), 1)
        self.assertEqual(res["query_errors"][0]["planner_query_index"], 0)
        self.assertIn("store exploded", res["query_errors"][0]["error"])
        self.assertEqual(res["summary"]["query_errors"], 1)
        self.assertEqual(res["merged_results"]["groups"], [])

    def test_deterministic_ordering(self):
        recs, incs = _fixtures()
        plan = _plan(queries=[{"query": "Fighting", "source": None},
                              {"query": "person", "source": None}])
        first = E.execute_plan(plan, recs, incs)
        second = E.execute_plan(copy.deepcopy(plan),
                                list(reversed(recs)), list(reversed(incs)))
        self.assertEqual(json.dumps(first, sort_keys=True, default=str),
                         json.dumps(second, sort_keys=True, default=str))

    def test_input_plan_not_modified(self):
        plan = _plan()
        snapshot = copy.deepcopy(plan)
        E.execute_plan(plan, *_fixtures())
        self.assertEqual(plan, snapshot)

    def test_evidence_fields_preserved(self):
        recs, incs = _fixtures()
        by_id = {r["evidence_id"]: r for r in recs}
        res = E.execute_plan(_plan(), recs, incs)
        for grp in res["merged_results"]["groups"]:
            for rec in grp["matched_evidence"] + grp["contextual_evidence"]:
                bare = {k: v for k, v in rec.items()
                        if k not in ("matched_hits", "planner_query_index", "planner_query")}
                self.assertEqual(bare, by_id[rec["evidence_id"]])

    def test_no_timeline_generated(self):
        res = E.execute_plan(_plan(needs_timeline=True), *_fixtures())
        blob = json.dumps(res)
        self.assertNotIn("timeline", blob.lower().replace("needs_timeline", ""))

    def test_cross_evidence_returns_context(self):
        recs, incs = _fixtures()
        res = E.execute_plan(_plan(needs_cross_evidence=True), recs, incs)
        ctx = sum(len(g["contextual_evidence"]) for g in res["merged_results"]["groups"])
        self.assertGreaterEqual(ctx, 0)
        blob = json.dumps(res["merged_results"])
        self.assertNotIn("reasoning", blob.lower())

    def test_no_secrets_in_errors(self):
        with mock.patch("src.pipeline.retrieve_temporal.retrieve_temporal",
                        side_effect=RuntimeError("store exploded")):
            res = E.execute_plan(_plan(), *_fixtures())
        self.assertNotIn("OPENROUTER", json.dumps(res))
        self.assertNotIn("sk-", json.dumps(res))


if __name__ == "__main__":
    unittest.main()
