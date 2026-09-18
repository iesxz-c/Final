"""Phase 5B.2 investigation benchmark validation (synthetic + frozen file).

Validator functions live here (not in src/) because the 5B.3 evaluation
module they would belong to does not exist yet. All checks run against
the frozen corpus; no model, retrieval, or agent output is involved."""

import json
import unittest
from pathlib import Path

BENCHMARK = Path("eval/investigation_benchmark_v1.json")
CORPUS = Path("data/data_155n/fused_155/evidence.json")
RELATIONS = ("before", "after", "during", "overlaps")
ALLOWED_KEYS = {"query_id", "question", "pattern", "scope",
                "ground_truth_source", "expected_evidence_ids",
                "expected_facts", "forbidden_claims",
                "expected_temporal_relations", "abstention_expected",
                "provenance", "notes"}


def _records():
    return json.load(CORPUS.open(encoding="utf-8"))


def _by_id(records):
    return {r["evidence_id"]: r for r in records}


def validate_case(case, by_id, videos):
    """Return a list of violation strings (empty = valid)."""
    problems = []
    extra = set(case) - ALLOWED_KEYS
    if extra:
        problems.append(f"unknown keys: {sorted(extra)}")
    qid = case.get("query_id", "?")
    scope = case.get("scope") or {}
    video = scope.get("video_id")
    if video not in videos:
        problems.append(f"{qid}: unknown scope video {video!r}")
    lo, hi = scope.get("start_time"), scope.get("end_time")
    if lo is not None and hi is not None and lo > hi:
        problems.append(f"{qid}: scope start > end")
    ids = case.get("expected_evidence_ids", [])
    if any(not isinstance(v, str) for v in ids):
        problems.append(f"{qid}: non-string evidence ID")
    if len(set(ids)) != len(ids):
        problems.append(f"{qid}: duplicate expected IDs")
    for eid in ids:
        if eid not in by_id:
            problems.append(f"{qid}: unknown evidence ID {eid}")
            continue
        rec = by_id[eid]
        if video is not None and rec.get("video_id") != video:
            problems.append(f"{qid}: {eid} outside scope video")
        if lo is not None and (rec.get("end_time", 0) < lo
                               or rec.get("start_time", 0) > hi):
            problems.append(f"{qid}: {eid} outside scope window")
    for fact in case.get("expected_facts", []):
        if not isinstance(fact, str) or not fact.strip():
            problems.append(f"{qid}: empty fact")
        elif len(fact) > 300 or "\n" in fact:
            problems.append(f"{qid}: fact not atomic: {fact[:60]!r}")
    if not case.get("expected_facts") and not case.get("abstention_expected"):
        problems.append(f"{qid}: no facts without abstention")
    for claim in case.get("forbidden_claims", []):
        if not isinstance(claim, str) or not claim.strip():
            problems.append(f"{qid}: empty forbidden claim")
    for rel in case.get("expected_temporal_relations", []):
        if rel.get("relation") not in RELATIONS:
            problems.append(f"{qid}: bad relation {rel.get('relation')!r}")
            continue
        for side in ("a_evidence_id", "b_evidence_id"):
            if rel.get(side) not in by_id:
                problems.append(f"{qid}: relation cites unknown {rel.get(side)!r}")
        if rel.get("a_evidence_id") in by_id and rel.get("b_evidence_id") in by_id:
            a = by_id[rel["a_evidence_id"]]
            b = by_id[rel["b_evidence_id"]]
            ok = {"before": a["end_time"] <= b["start_time"],
                  "after": a["start_time"] >= b["end_time"],
                  "during": a["start_time"] >= b["start_time"]
                  and a["end_time"] <= b["end_time"],
                  "overlaps": a["start_time"] <= b["end_time"]
                  and a["end_time"] >= b["start_time"]}[rel["relation"]]
            if not ok:
                problems.append(f"{qid}: relation inconsistent with timestamps")
    if not isinstance(case.get("abstention_expected"), bool):
        problems.append(f"{qid}: abstention_expected must be bool")
    if case.get("abstention_expected") and ids:
        problems.append(f"{qid}: abstention with non-empty evidence")
    return problems


def validate_benchmark(data, records):
    """Validate the whole file; return violation strings."""
    problems = []
    if data.get("schema_version") != "investigation_benchmark/v1":
        problems.append("bad schema_version")
    cases = data.get("cases", [])
    if len(cases) != 30:
        problems.append(f"expected 30 cases, got {len(cases)}")
    qids = [c.get("query_id") for c in cases]
    if len(set(qids)) != len(qids):
        problems.append("duplicate query IDs")
    by_id = _by_id(records)
    videos = {r.get("video_id") for r in records}
    for case in cases:
        problems.extend(validate_case(case, by_id, videos))
    return problems


class InvestigationBenchmarkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.load(BENCHMARK.open(encoding="utf-8"))
        cls.records = _records()

    def test_frozen_file_valid(self):
        problems = validate_benchmark(self.data, self.records)
        self.assertEqual(problems, [])

    def test_counts(self):
        cases = self.data["cases"]
        self.assertEqual(len(cases), 30)
        abstain = sum(1 for c in cases if c["abstention_expected"])
        self.assertEqual(abstain, 1)

    def test_rejects_bad_relation(self):
        recs = [{"evidence_id": "v:f0", "video_id": "v", "start_time": 0.0,
                 "end_time": 2.0},
                {"evidence_id": "v:f1", "video_id": "v", "start_time": 5.0,
                 "end_time": 7.0}]
        by_id = _by_id(recs)
        case = {"query_id": "X", "pattern": "p", "question": "q",
                "scope": {"video_id": "v", "start_time": None, "end_time": None},
                "ground_truth_source": "s", "expected_evidence_ids": ["v:f0"],
                "expected_facts": ["fact"], "forbidden_claims": ["no"],
                "expected_temporal_relations": [
                    {"relation": "before", "a_evidence_id": "v:f1",
                     "b_evidence_id": "v:f0"}],
                "abstention_expected": False, "provenance": "p", "notes": "n"}
        problems = validate_case(case, by_id, {"v"})
        self.assertTrue(any("inconsistent" in p for p in problems))

    def test_rejects_out_of_scope_id(self):
        recs = [{"evidence_id": "v:f0", "video_id": "v", "start_time": 0.0,
                 "end_time": 2.0}]
        case = {"query_id": "X", "pattern": "p", "question": "q",
                "scope": {"video_id": "v", "start_time": 90.0, "end_time": 99.0},
                "ground_truth_source": "s", "expected_evidence_ids": ["v:f0"],
                "expected_facts": ["fact"], "forbidden_claims": ["no"],
                "expected_temporal_relations": [],
                "abstention_expected": False, "provenance": "p", "notes": "n"}
        problems = validate_case(case, _by_id(recs), {"v"})
        self.assertTrue(any("outside scope window" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
