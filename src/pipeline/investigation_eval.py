"""Phase 5B.3 - End-to-end investigation evaluation (two arms, mechanical only).

ARM 1 (full): question -> 3C plan -> hybrid retrieval (3C-planned lexical
terms + verbatim-question vector, RRF-60) -> frozen 3D -> 3E -> 3F.
ARM 2 (baseline): same through frozen 3D, then a deterministic templated
evidence report. No 3E/3F/LLM beyond 3C planning in arm 2.

Controlled arms (retrieval-interface experiment only): full-lexical
(frozen lexical ranking, top-10) and full-hybrid (frozen lexical + vector
fused with frozen RRF-60, top-10) assembled directly into phase3d/v1 via
assemble_fused_evidence with no second lexical gate, then shared 3E -> 3F.
The locked full arm path is unchanged.

Ground truth is used ONLY by this evaluation layer, never supplied to
agents, retrieval, or prompts. Expected-fact coverage requires later
human grading: output carries mechanical_metrics plus
human_evaluation_pending=true, with every claim preserved for review.

Ablation arms: no-temporal (empty-timeline adapter into unmodified 3F),
no-verification (3E timeline IS the answer; claim metrics stay null),
no-planning (fixed validated plan, no LLM planning call).
Grading mapping for no-verification: grade timeline observation /
correlation / inference texts against expected facts exactly as report
findings would be graded; claim-status metrics do not apply.

Usage:
    python -m src.pipeline.investigation_eval --mock --output /tmp/inv.json
    python -m src.pipeline.investigation_eval --benchmark eval/investigation_benchmark_v1.json
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.agents import evidence_retrieval as D3
from src.agents import query_planner as Q
from src.agents import timeline_correlation as E
from src.agents import verification_report as F
from src.pipeline import retrieve_evidence as R3A
from src.pipeline import retrieve_temporal as R3B
from src.pipeline import run_investigation as R
from src.pipeline.api_eval import RecordingClient, SAFETY_BUCKETS
from src.pipeline.retrieve_evidence import load_evidence
from src.pipeline.retrieve_temporal import load_incidents
from src.pipeline.retrieval_eval import rrf_fuse, RetrievalResult

SCHEMA_VERSION = "investigation-eval/v1"
BENCHMARK_VERSION = "investigation_benchmark/v1"
RRF_CONSTANT = 60
RETRIEVAL_TOP_K = 10


def load_cases(path: str | Path) -> list:
    """Read investigation benchmark cases (ground truth for eval layer only)."""
    with Path(path).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("schema_version") != BENCHMARK_VERSION:
        raise ValueError("bad investigation benchmark schema_version")
    cases = data.get("cases", [])
    if not cases:
        raise ValueError("benchmark has no cases")
    return cases


def hybrid_retrieve_for_case(records: list, question: str, plan: dict,
                             retriever, scope: dict, top_k: int = 10) -> list:
    """Hybrid evidence set for one case (evaluation-side retrieval).

    Lexical branch: one frozen 3A call per 3C plan query (production
    behavior), scope-filtered. Vector branch: verbatim question over the
    collection, scope-filtered. RRF-60 fuses full branch rankings; only
    the fused list is cut to top_k. Returns full record dicts in corpus
    order. Ground truth never enters here.
    """
    scope_video = (scope or {}).get("video_id")
    lexical_lists = []
    for pq in plan.get("queries", []) or []:
        text = (pq.get("query") or "").strip()
        if not text:
            continue
        start = pq.get("start_time")
        end = pq.get("end_time")
        if (scope or {}).get("start_time") is not None:
            start = max([s for s in (start, scope["start_time"]) if s is not None],
                        default=None)
        if (scope or {}).get("end_time") is not None:
            end = min([e for e in (end, scope["end_time"]) if e is not None],
                      default=None)
        video = pq.get("video_id") or scope_video
        sources = [pq["source"]] if pq.get("source") else None
        hits = R3A.retrieve(records, text, video_id=video, start_time=start,
                            end_time=end, sources=sources, limit=None)
        lexical_lists.append([
            RetrievalResult(h["evidence_id"], pos, float(h["confidence"]), "lexical")
            for pos, h in enumerate(hits)])
    lexical: dict = {}
    for table in lexical_lists:
        for item in table:
            if item.evidence_id not in lexical \
                    or item.rank < lexical[item.evidence_id].rank:
                lexical[item.evidence_id] = item
    lex_ranked = sorted(lexical.values(), key=lambda r: (r.rank, r.evidence_id))
    vec_ranked = vector_branch(records, question, retriever, scope, top_k=None)
    fused = rrf_fuse([lex_ranked, vec_ranked], constant=RRF_CONSTANT)
    wanted = [h.evidence_id for h in fused[:max(0, top_k)]]
    by_id = {r.get("evidence_id"): r for r in records}
    return [by_id[e] for e in wanted if e in by_id]


def vector_branch(records: list, question: str, retriever, scope: dict,
                  top_k: int | None = 10) -> list:
    """Verbatim-question vector ranking, scope-filtered, order preserved."""
    ranked = retriever.search(question, top_k=len(records))
    by_id = {r.get("evidence_id"): r for r in records}
    start, end = (scope or {}).get("start_time"), (scope or {}).get("end_time")
    kept = []
    for hit in ranked:
        record = by_id.get(hit.evidence_id)
        if record is None:
            continue
        if (scope or {}).get("video_id") is not None \
                and record.get("video_id") != scope.get("video_id"):
            continue
        if start is not None and float(record.get("end_time", 0)) < start:
            continue
        if end is not None and float(record.get("start_time", 0)) > end:
            continue
        kept.append(hit)
    if top_k is None:
        return kept
    return kept[:max(0, top_k)]


class AssemblyError(ValueError):
    """Direct-evidence assembly failed (fail closed, never fabricate)."""


def lexical_ranking_for_plan(records: list, plan: dict, scope: dict) -> list:
    """Full deduped lexical ranking for one plan (no cut).

    Same frozen 3A calls and plan/scope intersection as the lexical branch
    of hybrid_retrieve_for_case, so the FULL-LEXICAL arm measures the same
    lexical behavior. Ranks are 0-based positions, deduplicated across plan
    queries keeping the best rank, sorted by (rank, evidence_id).
    """
    scope_video = (scope or {}).get("video_id")
    lexical_lists = []
    for pq in plan.get("queries", []) or []:
        text = (pq.get("query") or "").strip()
        if not text:
            continue
        start = pq.get("start_time")
        end = pq.get("end_time")
        if (scope or {}).get("start_time") is not None:
            start = max([s for s in (start, scope["start_time"]) if s is not None],
                        default=None)
        if (scope or {}).get("end_time") is not None:
            end = min([e for e in (end, scope["end_time"]) if e is not None],
                      default=None)
        video = pq.get("video_id") or scope_video
        sources = [pq["source"]] if pq.get("source") else None
        hits = R3A.retrieve(records, text, video_id=video, start_time=start,
                            end_time=end, sources=sources, limit=None)
        lexical_lists.append([
            RetrievalResult(h["evidence_id"], pos, float(h["confidence"]), "lexical")
            for pos, h in enumerate(hits)])
    lexical: dict = {}
    for table in lexical_lists:
        for item in table:
            if item.evidence_id not in lexical \
                    or item.rank < lexical[item.evidence_id].rank:
                lexical[item.evidence_id] = item
    return sorted(lexical.values(), key=lambda r: (r.rank, r.evidence_id))


def ranking_for_arm(arm: str, records: list, question: str, plan: dict,
                    retriever, scope: dict) -> list:
    """Branch ranking for the controlled arms (full ranking, no cut).

    full-lexical: frozen lexical ranking only. full-hybrid: frozen lexical
    plus verbatim-question vector ranking fused with frozen RRF-60. The
    top-K cut happens in assemble_fused_evidence so both arms share it.
    """
    lex_ranked = lexical_ranking_for_plan(records, plan, scope)
    if arm == "full-lexical":
        return lex_ranked
    if arm != "full-hybrid":
        raise AssemblyError(f"unknown controlled arm: {arm!r}")
    if retriever is None:
        raise AssemblyError("full-hybrid needs a vector retriever; none supplied")
    vec_ranked = vector_branch(records, question, retriever, scope, top_k=None)
    return rrf_fuse([lex_ranked, vec_ranked], constant=RRF_CONSTANT)


def _require_record_identity(record: dict) -> None:
    if not isinstance(record, dict) or not isinstance(
            record.get("evidence_id"), str) or not record["evidence_id"]:
        raise AssemblyError("assembled record needs a non-empty evidence_id")
    if not isinstance(record.get("video_id"), str) or not record["video_id"]:
        raise AssemblyError("assembled record needs a non-empty video_id")
    for field in ("start_time", "end_time"):
        value = record.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or value < 0:
            raise AssemblyError(f"assembled record needs numeric {field} >= 0")
    if float(record["end_time"]) < float(record["start_time"]):
        raise AssemblyError("assembled record needs end_time >= start_time")


def direct_records_for_ranking(ranking: list, records: list,
                               top_k: int = 10) -> tuple:
    """Dedupe ranking IDs in ranking order, cut to top_k, map verbatim.

    Returns (ordered_ids, record_list) with original record dicts passed
    through unmodified. Fail closed on unknown IDs or malformed records.
    """
    ordered: list = []
    for item in ranking:
        if item.evidence_id not in ordered:
            ordered.append(item.evidence_id)
    wanted = ordered[:max(0, top_k)]
    by_id = {r.get("evidence_id"): r for r in records}
    missing = [e for e in wanted if e not in by_id]
    if missing:
        raise AssemblyError(
            f"ranking cites unknown evidence: {missing[:5]}")
    picked = [by_id[e] for e in wanted]
    for record in picked:
        _require_record_identity(record)
    return wanted, picked


def _synthesized_hit(record: dict, matched_source: str, matched_id: str,
                     matched_label: str, confidence: float,
                     source_reference: str, provenance: dict) -> dict:
    hit = {
        "video_id": record.get("video_id", ""),
        "evidence_id": record.get("evidence_id", ""),
        "start_time": record.get("start_time"),
        "end_time": record.get("end_time"),
        "matched_source": matched_source,
        "matched_id": matched_id,
        "matched_label": matched_label,
        "confidence": confidence,
        "source_reference": source_reference,
        "anomaly_score": record.get("anomaly_score", 0.0),
    }
    for key in ("retrieval_method", "rank", "score"):
        if provenance.get(key) is not None:
            hit[key] = provenance[key]
    return hit


def synthesize_matched_hits(record: dict, provenance: dict | None = None) -> list:
    """One matched_hit per non-empty evidence stream plus a record fallback.

    matched_source keeps WHAT-matched semantics only (object /
    generic_action / surveillance_event / record); retrieval provenance
    travels in separate retrieval_method/rank/score fields that validators
    never read as source types.
    """
    provenance = dict(provenance or {})
    hits = []
    streams = (
        ("object", record.get("object_evidence") or []),
        ("generic_action", record.get("generic_action_evidence") or []),
        ("surveillance_event",
         record.get("surveillance_event_evidence") or []),
    )
    for source, entries in streams:
        if not entries:
            continue
        first = entries[0] if isinstance(entries[0], dict) else {}
        if source == "object":
            matched_id = str(first.get("detection_id", ""))
            matched_label = str(first.get("class_name", ""))
            confidence = float(first.get("confidence", 0.0))
            stamp = first.get("timestamp_seconds", record.get("start_time"))
            reference = f"{record.get('video_id', '')}@t={stamp}s"
        else:
            matched_id = str(first.get("observation_id", ""))
            matched_label = str(first.get("label", ""))
            confidence = float(first.get("confidence", 0.0))
            reference = str(first.get("source_reference", ""))
        hits.append(_synthesized_hit(record, source, matched_id, matched_label,
                                     confidence, reference, provenance))
    refs = record.get("source_references", []) or []
    hits.append(_synthesized_hit(
        record, "record", str(record.get("evidence_id", "")),
        str(record.get("evidence_id", "")), float(record.get("anomaly_score", 0.0)),
        str(refs[0] if refs else ""), provenance))
    return hits


def _within_window(record: dict, anchor: dict, context_seconds: float) -> bool:
    if record.get("video_id") != anchor.get("video_id"):
        return False
    return (float(record.get("start_time", 0)) <= float(anchor.get("end_time", 0))
            + context_seconds
            and float(record.get("end_time", 0)) >= float(anchor.get("start_time", 0))
            - context_seconds)


def assemble_fused_evidence(plan: dict, fused_ranking: list, records: list,
                            incidents: list, context_seconds,
                            top_k: int = RETRIEVAL_TOP_K) -> dict:
    """Direct phase3d/v1 assembly from an already-fused ranking (no lexical gate).

    Direct evidence is exactly the top-K ranking IDs mapped to verbatim
    corpus records in ranking order. Incident mates of direct evidence
    become contextual evidence; with context_seconds > 0, same-video
    records inside the window around direct evidence are added too. No
    corpus record outside those rules is introduced. Records are never
    re-searched lexically, so vector-only evidence survives as direct
    (matched) evidence with synthesized matched_hits.
    """
    norm_plan = D3.validate_plan(plan)
    if context_seconds is None:
        context_seconds = 0.0
    if context_seconds < 0:
        raise AssemblyError(f"context_seconds must be >= 0: {context_seconds}")
    wanted_ids, _ = direct_records_for_ranking(fused_ranking, records, top_k)
    provenance: dict = {}
    for item in fused_ranking:
        provenance.setdefault(item.evidence_id,
                              {"retrieval_method": item.retrieval_method,
                               "rank": item.rank, "score": item.score})
    by_id = {r.get("evidence_id"): r for r in records}
    membership = R3B.build_membership(incidents)
    direct_ids = set(wanted_ids)

    matched: dict = {}
    order: list = []
    unmapped_ids: list = []
    for eid in wanted_ids:
        incident = membership.get(eid)
        if incident is None:
            unmapped_ids.append(eid)
            continue
        iid = incident.get("incident_id", "")
        if iid not in matched:
            matched[iid] = {"incident": incident, "ids": []}
            order.append(iid)
        matched[iid]["ids"].append(eid)

    used_context: set = set()
    groups = []
    for iid in sorted(
            order, key=lambda i: (float(matched[i]["incident"].get("start_time", 0)),
                                  i)):
        incident = matched[iid]["incident"]
        anchors = [by_id[e] for e in matched[iid]["ids"]]
        context_ids = [e for e in incident.get("evidence_ids", []) or []
                       if e not in direct_ids and e in by_id]
        context_ids = list(dict.fromkeys(context_ids))
        if context_seconds > 0:
            extra = [r.get("evidence_id") for r in records
                     if r.get("evidence_id") not in direct_ids
                     and r.get("evidence_id") not in context_ids
                     and r.get("evidence_id") not in used_context
                     and any(_within_window(r, a, context_seconds)
                             for a in anchors)]
            context_ids.extend(sorted(set(extra)))
        fresh = [e for e in context_ids if e not in used_context]
        used_context.update(fresh)
        matched_evidence = []
        for eid in sorted(matched[iid]["ids"],
                          key=lambda e: (float(by_id[e].get("start_time", 0)), e)):
            record = dict(by_id[eid])
            record["matched_hits"] = synthesize_matched_hits(
                by_id[eid], provenance.get(eid, {}))
            matched_evidence.append(record)
        contextual_evidence = [
            by_id[e] for e in sorted(
                fresh, key=lambda e: (float(by_id[e].get("start_time", 0)), e))]
        groups.append({
            "incident_id": iid,
            "video_id": incident.get("video_id", ""),
            "incident_start_time": incident.get("start_time"),
            "incident_end_time": incident.get("end_time"),
            "event_hypotheses": list(incident.get("event_hypotheses", []) or []),
            "matched_evidence": matched_evidence,
            "contextual_evidence": contextual_evidence,
        })

    unmapped = []
    for eid in unmapped_ids:
        unmapped.extend(synthesize_matched_hits(by_id[eid],
                                                provenance.get(eid, {})))
    unmapped.sort(key=lambda h: (str(h["video_id"]), float(h["start_time"]),
                                 str(h["evidence_id"]),
                                 str(h["matched_source"])))
    query_results = [{"query": item["query"], "source": item["source"],
                      "planner_query_index": index, "groups": [],
                      "unmapped_hits": [],
                      "summary": {"matched_hits": 0, "matched_records": 0,
                                  "incident_groups": 0, "context_records": 0,
                                  "unmapped_hits": 0}}
                     for index, item in enumerate(norm_plan["queries"])]
    matched_hit_count = (sum(len(r.get("matched_hits", []))
                             for g in groups for r in g["matched_evidence"])
                         + len(unmapped))
    return {
        "schema_version": D3.SCHEMA_VERSION,
        "plan": norm_plan,
        "query_results": query_results,
        "query_errors": [],
        "merged_results": {"groups": groups, "unmapped_hits": unmapped},
        "summary": {"planner_queries": len(norm_plan["queries"]),
                    "matched_hits": matched_hit_count,
                    "incident_groups": len(groups),
                    "context_records": sum(len(g["contextual_evidence"])
                                           for g in groups),
                    "unmapped_hits": len(unmapped),
                    "query_errors": 0},
        "assembly": {"mode": "direct", "direct_ids": list(wanted_ids),
                     "context_seconds": context_seconds},
    }


def templated_report(question: str, result_3d: dict) -> dict:
    """Deterministic evidence report for the baseline arm (no LLM)."""
    groups = ((result_3d.get("merged_results", {}) or {}).get("groups", []) or [])
    lines = []
    for group in groups:
        for record in (group.get("matched_evidence", []) or []) \
                + (group.get("contextual_evidence", []) or []):
            labels = sorted({e.get("label", "") for e in
                             record.get("surveillance_event_evidence", []) or []
                             if e.get("label")})
            lines.append({"evidence_id": record.get("evidence_id"),
                          "video_id": record.get("video_id"),
                          "start_time": record.get("start_time"),
                          "end_time": record.get("end_time"),
                          "event_labels": labels})
    lines.sort(key=lambda l: (str(l["video_id"]), float(l["start_time"] or 0),
                              str(l["evidence_id"])))
    return {"schema_version": "phase5b-baseline/v1", "question": question,
            "evidence_records": lines,
            "limitations": ["templated baseline: no timeline, correlation, "
                            "verification, or inference was performed"]}


def _timed(bundle_timings: dict, verdicts: dict, stage: str, func, *args,
           **kwargs):
    start = time.perf_counter()
    try:
        result = func(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - recorded, never fabricated
        bundle_timings[stage] = round(time.perf_counter() - start, 3)
        verdicts[stage] = "error"
        return None, {"stage": stage, "type": R.classify_failure(exc),
                      "error": str(exc)[:500]}
    bundle_timings[stage] = round(time.perf_counter() - start, 3)
    verdicts[stage] = "pass"
    return result, None


def run_case(case: dict, records: list, incidents: list, mode: str,
             make_client, settings: dict, model_name: str,
             arm: str, retriever=None) -> dict:
    """Execute one case under one arm. Returns the investigation bundle."""
    snapshot = copy.deepcopy(records)
    question = case["question"]
    bundle: dict = {
        "schema_version": SCHEMA_VERSION,
        "query_id": case["query_id"], "question": question,
        "pattern": case.get("pattern"), "arm": arm,
        "plan": None, "retrieved_evidence_ids": [], "result_3d": None,
        "result_3e": None, "result_3f": None, "baseline_report": None,
        "timings": {}, "validator_verdicts": {}, "failure": None,
        "integrity_audit": None, "git_hash": R.get_git_hash(),
        "model": model_name, "mode": mode,
        "settings": {"provider": settings.get("provider"),
                     "model": settings.get("model"),
                     "temperature": settings.get("temperature", 0.0)},
        "retrieval": {"method": "hybrid-rrf", "constant": RRF_CONSTANT,
                      "top_k": RETRIEVAL_TOP_K},
        "run_utc": datetime.now(timezone.utc).isoformat(),
    }
    total_start = time.perf_counter()
    temperature = settings.get("temperature", 0.0)
    client = make_client()
    recording = RecordingClient(client) if mode == "real" and client is not None else None
    llm = recording if recording is not None else client

    if arm == "no-planning":
        plan, failure = _timed(bundle["timings"], bundle["validator_verdicts"],
                               "3c", fixed_plan, question)
    elif mode == "mock":
        plan, failure = _timed(bundle["timings"], bundle["validator_verdicts"],
                               "3c", R._mock_plan, question)
    else:
        plan, failure = _timed(bundle["timings"], bundle["validator_verdicts"],
                               "3c", Q.plan_query, llm, question, temperature)
    if failure:
        bundle["failure"] = failure
        return _finish(bundle, snapshot, records, total_start)
    bundle["plan"] = plan
    if arm in ("full-lexical", "full-hybrid"):
        ranking, failure = _timed(
            bundle["timings"], bundle["validator_verdicts"], "retr",
            ranking_for_arm, arm, records, question, plan, retriever,
            case.get("scope") or {})
        if failure:
            bundle["failure"] = failure
            return _finish(bundle, snapshot, records, total_start, recording)
        bundle["retrieval"] = ({"method": "lexical", "top_k": RETRIEVAL_TOP_K}
                               if arm == "full-lexical" else
                               {"method": "hybrid-rrf", "constant": RRF_CONSTANT,
                                "top_k": RETRIEVAL_TOP_K})
        result_3d, failure = _timed(
            bundle["timings"], bundle["validator_verdicts"], "3d",
            assemble_fused_evidence, plan, ranking, records, incidents,
            plan.get("temporal_context_seconds", 0))
    else:
        subset, failure = _timed(
            bundle["timings"], bundle["validator_verdicts"], "retr",
            hybrid_retrieve_for_case, records, question, plan, retriever,
            case.get("scope") or {}, RETRIEVAL_TOP_K) \
            if mode == "real" else _timed(
            bundle["timings"], bundle["validator_verdicts"], "retr",
            _mock_subset, records)
        if failure:
            bundle["failure"] = failure
            return _finish(bundle, snapshot, records, total_start, recording)
        bundle["retrieved_evidence_ids"] = [r.get("evidence_id") for r in subset]

        if mode == "mock":
            result_3d, failure = _timed(bundle["timings"], bundle["validator_verdicts"],
                                        "3d", D3.execute_plan, plan, list(subset), incidents)
        else:
            result_3d, failure = _timed(bundle["timings"], bundle["validator_verdicts"],
                                        "3d", D3.execute_plan, plan, list(subset), incidents)
    if arm in ("full-lexical", "full-hybrid"):
        if failure:
            bundle["failure"] = failure
            return _finish(bundle, snapshot, records, total_start, recording)
        bundle["retrieved_evidence_ids"] = list(
            (result_3d.get("assembly") or {}).get("direct_ids", []))
    if failure:
        bundle["failure"] = failure
        return _finish(bundle, snapshot, records, total_start, recording)
    bundle["result_3d"] = result_3d
    if result_3d["summary"].get("query_errors"):
        bundle["failure"] = {"stage": "3d", "type": "retrieval",
                             "error": "planner query(ies) failed"}
        bundle["validator_verdicts"]["3d"] = "error"
        return _finish(bundle, snapshot, records, total_start, recording)

    if arm == "baseline":
        bundle["baseline_report"], _ = _timed(
            bundle["timings"], bundle["validator_verdicts"], "report",
            templated_report, question, result_3d)
        return _finish(bundle, snapshot, records, total_start, recording)

    if arm == "no-temporal":
        result_3e, failure = _timed(bundle["timings"], bundle["validator_verdicts"],
                                    "3e", empty_timeline_adapter, result_3d)
        bundle["adapter"] = "empty-timeline"
    elif mode == "mock":
        result_3e, failure = _timed(bundle["timings"], bundle["validator_verdicts"],
                                    "3e", R._mock_timeline, result_3d, question)
    else:
        result_3e, failure = _timed(bundle["timings"], bundle["validator_verdicts"],
                                    "3e", E.run_timeline, llm, result_3d, question,
                                    temperature)
    if failure:
        bundle["failure"] = failure
        return _finish(bundle, snapshot, records, total_start, recording)
    bundle["result_3e"] = result_3e
    if arm == "no-verification":
        # Timeline/correlation/inference output IS this arm's answer; 3F
        # never runs, so claim-level verification metrics stay null.
        return _finish(bundle, snapshot, records, total_start, recording)
    if mode == "mock":
        result_3f, failure = _timed(bundle["timings"], bundle["validator_verdicts"],
                                    "3f", R._mock_report, result_3e, result_3d,
                                    question)
    else:
        result_3f, failure = _timed(bundle["timings"], bundle["validator_verdicts"],
                                    "3f", F.run_verification_report, llm, result_3e,
                                    result_3d, question, temperature,
                                    F.REPORT_MAX_TOKENS)
    if failure:
        bundle["failure"] = failure
    else:
        bundle["result_3f"] = result_3f
    return _finish(bundle, snapshot, records, total_start, recording)


def _mock_subset(records):
    """Mock-mode evidence subset (no retrieval; exercises downstream)."""
    return list(records)


def fixed_plan(question: str) -> dict:
    """Question-independent plan for the no-planning arm (validated).

    Single query carrying the verbatim question, no source, no video or
    time bounds: intent classification, source selection, and question
    decomposition are all removed. Validated through the EXISTING
    parse_and_validate_plan unchanged.
    """
    return Q.parse_and_validate_plan(json.dumps({
        "schema_version": Q.SCHEMA_VERSION,
        "intent": "search_evidence",
        "queries": [{"query": question.strip(), "source": None}],
        "video_id": None, "start_time": None, "end_time": None,
        "temporal_context_seconds": 0,
        "needs_timeline": True, "needs_cross_evidence": False}))


def empty_timeline_adapter(result_3d: dict) -> dict:
    """Stand-in 3E output for the no-temporal arm (deterministic).

    Returns exactly the empty-timeline shape run_timeline itself returns
    for empty evidence (same schema, same list fields); the limitations
    text honestly states temporal reasoning was ablated. No retrieval
    groups are converted into timeline events.
    """
    _ = result_3d
    return {"schema_version": E.SCHEMA_VERSION, "timeline": [],
            "correlations": [], "inferences": [],
            "limitations": ["Temporal reasoning ablated: no timeline or "
                            "correlations were constructed."]}


def _finish(bundle, snapshot, records, total_start, recording=None):
    bundle["timings"]["total"] = round(time.perf_counter() - total_start, 3)
    bundle["integrity_audit"] = R.audit_integrity(
        snapshot, records, bundle["result_3d"], bundle["result_3e"],
        bundle["result_3f"])
    usages = list(getattr(recording, "usages", []) or []) if recording else []
    bundle["token_usage"] = {
        stage: (usages[i] if i < len(usages) else None)
        for i, stage in enumerate(("3c", "3e", "3f"))}
    return bundle


def _claim_texts(bundle: dict) -> list:
    return [str(v.get("claim", "")) for v in
            ((bundle.get("result_3f") or {}).get("verification", []) or [])]


def _report_text(bundle: dict) -> str:
    report = (bundle.get("result_3f") or {}).get("report", {}) or {}
    parts = [str(report.get("title", "")), str(report.get("summary", ""))]
    for item in report.get("timeline", []) or []:
        parts.append(str(item.get("description", "")))
    for item in report.get("findings", []) or []:
        parts.append(str(item.get("text", "")))
    baseline = bundle.get("baseline_report") or {}
    for line in baseline.get("evidence_records", []) or []:
        parts.append(str(line.get("evidence_id", "")))
    return "\n".join(parts)


def forbidden_hits(bundle: dict, forbidden: list) -> list:
    """Exact forbidden-claim substrings present in output (mechanical)."""
    haystack = (_report_text(bundle) + "\n" + "\n".join(_claim_texts(bundle))).lower()
    return [c for c in forbidden if c and str(c).lower() in haystack]


def phrase_hits(bundle: dict) -> dict:
    """Generic safety-phrase scan over output prose (mechanical)."""
    haystack = (_report_text(bundle) + "\n" + "\n".join(_claim_texts(bundle))).lower()
    counts = {}
    for bucket, phrases in SAFETY_BUCKETS.items():
        counts[bucket] = sum(haystack.count(p.lower()) for p in phrases)
    return counts


def _rate(numerator: int, denominator: int) -> dict | None:
    if not denominator:
        return None
    return {"value": round(numerator / denominator, 4),
            "numerator": numerator, "denominator": denominator}


def _latency(values: list) -> dict:
    stats: dict = {"n": len(values)}
    if not values:
        return stats
    ordered = sorted(values)
    stats["mean"] = round(statistics.mean(values), 3)
    stats["median"] = round(statistics.median(values), 3)
    stats["p95"] = round(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)], 3)
    return stats


def evaluate_case(case: dict, bundle: dict) -> dict:
    """Mechanical per-case evaluation against frozen ground truth (pure)."""
    expected_ids = set(case.get("expected_evidence_ids", []))
    retrieved = set(bundle.get("retrieved_evidence_ids", []))
    verification = (bundle.get("result_3f") or {}).get("verification", []) or []
    statuses = [v.get("status") for v in verification]
    cited = {e for v in verification for e in v.get("evidence_ids", []) or []}
    audit = bundle.get("integrity_audit", {}) or {}
    uncontained = sum((audit.get("stages", {}) or {}).get(s, {}).get(
        "uncontained_ranges", 0) for s in ("3e", "3f"))
    expected_relations = case.get("expected_temporal_relations", []) or []
    supported_relations = 0
    for rel in expected_relations:
        pair = {rel.get("a_evidence_id"), rel.get("b_evidence_id")}
        if pair <= cited:
            supported_relations += 1
    no_claims = not verification and bundle.get("failure") is None
    abstention_expected = bool(case.get("abstention_expected"))
    # Abstention is only assessable where expected; non-abstention quality
    # belongs to pending human answer review, not to this flag.
    abstention_correct = (no_claims if abstention_expected else None)
    timings = bundle.get("timings", {}) or {}
    failure = bundle.get("failure")
    if bundle.get("arm") == "no-verification":
        # 3F never ran: claim-level verification metrics are N/A, never zero.
        claim_counts = {"supported": None, "partially_supported": None,
                        "unsupported": None}
        supported_list: list = []
        cited_count = None
        cited_total = None
    else:
        claim_counts = {"supported": statuses.count("supported"),
                        "partially_supported": statuses.count("partially_supported"),
                        "unsupported": statuses.count("unsupported")}
        supported_list = [
            {"claim_id": v.get("claim_id"),
             "evidence_ids": list(v.get("evidence_ids", []) or [])}
            for v in verification if v.get("status") == "supported"]
        cited_count = sum(1 for v in verification if v.get("evidence_ids"))
        cited_total = len(verification)
    return {
        "query_id": case["query_id"], "arm": bundle.get("arm"),
        "pattern": case.get("pattern"),
        "retrieved_count": len(retrieved),
        "expected_count": len(expected_ids),
        "retrieved_expected_count": len(retrieved & expected_ids),
        "failure": failure,
        "failure_type": (failure or {}).get("type") if failure else None,
        "failure_stage": (failure or {}).get("stage") if failure else None,
        "empty_evidence": not retrieved and failure is None,
        "schema_valid": bool(bundle.get("validator_verdicts")) and all(
            v == "pass" for k, v in bundle["validator_verdicts"].items()
            if k in ("3c", "3e", "3f", "report")),
        "claims": claim_counts,
        "supported_claims": supported_list,
        "citation": {"cited": cited_count, "total": cited_total},
        "audit_pass": audit.get("overall_pass"),
        "temporal_uncontained": uncontained,
        "relations_supported": supported_relations,
        "relations_total": len(expected_relations),
        "forbidden_hits": forbidden_hits(bundle, case.get("forbidden_claims", [])),
        "safety_phrases": phrase_hits(bundle),
        "abstention_expected": abstention_expected,
        "abstention_correct": abstention_correct,
        "answer_fact_coverage": None,
        "supported_answer_rate": None,
        "token_usage": bundle.get("token_usage", {}),
        "latencies": {s: timings.get(s)
                      for s in ("3c", "retr", "3d", "3e", "3f", "report", "total")},
    }
    return {
        "query_id": case["query_id"], "arm": bundle.get("arm"),
        "retrieved_count": len(retrieved),
        "expected_count": len(expected_ids),
        "retrieved_expected_count": len(retrieved & expected_ids),
        "failure": failure,
        "failure_type": (failure or {}).get("type") if failure else None,
        "empty_evidence": not retrieved and failure is None,
        "schema_valid": bool(bundle.get("validator_verdicts")) and all(
            v == "pass" for k, v in bundle["validator_verdicts"].items()
            if k in ("3c", "3e", "3f", "report")),
        "claims": {"supported": statuses.count("supported"),
                   "partially_supported": statuses.count("partially_supported"),
                   "unsupported": statuses.count("unsupported")},
        "citation_coverage": _rate(len([v for v in verification if v.get("evidence_ids")]),
                                   len(verification)),
        "audit_pass": audit.get("overall_pass"),
        "temporal_uncontained": uncontained,
        "temporal_relations_supported": _rate(supported_relations,
                                             len(expected_relations)),
        "forbidden_hits": forbidden_hits(bundle, case.get("forbidden_claims", [])),
        "safety_phrases": phrase_hits(bundle),
        "abstention_expected": abstention_expected,
        "abstention_correct": abstention_correct,
        "answer_fact_coverage": None,
        "supported_answer_rate": None,
    }


def aggregate_arm(evaluations: list) -> dict:
    """Aggregate one arm's per-case evaluations (pure, no composites)."""
    total = len(evaluations)
    ok = sum(1 for e in evaluations if e["failure"] is None)
    scored = [e for e in evaluations if e["claims"]["supported"] is not None]
    claims = {k: sum(e["claims"][k] for e in scored)
              for k in ("supported", "partially_supported", "unsupported")}
    total_claims = sum(claims.values())
    cited = sum(e["citation"]["cited"] for e in scored)
    cited_total = sum(e["citation"]["total"] for e in scored)
    if not scored:
        claims = {k: None for k in claims}
        cited = cited_total = None
    total_claims = sum(claims.values()) if scored else None
    claim_rates = ({"supported_claim_rate": _rate(claims["supported"], total_claims),
                    "unsupported_claim_rate": _rate(claims["unsupported"], total_claims),
                    "citation_coverage": _rate(cited, cited_total)}
                   if scored else
                   {"supported_claim_rate": None, "unsupported_claim_rate": None,
                    "citation_coverage": None})
    abstention_cases = [e for e in evaluations if e["abstention_expected"]]
    safety = {}
    for e in evaluations:
        for bucket, count in e["safety_phrases"].items():
            safety[bucket] = safety.get(bucket, 0) + count
    forbidden = sum(len(e["forbidden_hits"]) for e in evaluations)
    ins = [u["input_tokens"] for e in evaluations for u in
           (e["token_usage"][s] for s in ("3c", "3e", "3f")) if u]
    outs = [u["output_tokens"] for e in evaluations for u in
            (e["token_usage"][s] for s in ("3c", "3e", "3f")) if u]
    with_usage = sum(1 for e in evaluations
                     if any(e["token_usage"][s] for s in ("3c", "3e", "3f")))
    taxonomy: dict = {}
    for e in evaluations:
        if e["failure_type"]:
            taxonomy[e["failure_type"]] = taxonomy.get(e["failure_type"], 0) + 1
    return {
        "investigations": total,
        "completed": ok,
        "completion_rate": _rate(ok, total),
        "failure_taxonomy": taxonomy,
        "claims": claims,
        "supported_claim_rate": claim_rates["supported_claim_rate"],
        "unsupported_claim_rate": claim_rates["unsupported_claim_rate"],
        "citation_coverage": claim_rates["citation_coverage"],
        "audit_pass_rate": _rate(sum(1 for e in evaluations if e["audit_pass"]),
                                 total),
        "temporal_uncontained_total": sum(e["temporal_uncontained"]
                                          for e in evaluations),
        "temporal_relations_supported": _rate(
            sum(e["relations_supported"] for e in evaluations),
            sum(e["relations_total"] for e in evaluations)),
        "schema_valid_rate": _rate(sum(1 for e in evaluations if e["schema_valid"]),
                                   total),
        "validator_rejection_rate": _rate(
            sum(1 for e in evaluations if e["failure_type"] == "validation"), total),
        "abstention_expected_n": len(abstention_cases),
        "abstention_correct": _rate(
            sum(1 for e in abstention_cases if e["abstention_correct"] is True),
            sum(1 for e in abstention_cases
                if e["abstention_correct"] is not None)),
        "forbidden_claim_hits": forbidden,
        "safety_phrase_counts": safety,
        "false_support_review": [
            {"query_id": e["query_id"], "claim_id": c["claim_id"],
             "evidence_ids": c["evidence_ids"]}
            for e in evaluations for c in e["supported_claims"]],
        "answer_fact_coverage": None,
        "supported_answer_rate": None,
        "tokens": {"investigations_with_usage": with_usage, "total": total,
                   "input_total": sum(ins), "output_total": sum(outs)} if ins or outs
        else {"investigations_with_usage": 0, "total": total,
              "status": "unavailable"},
        "latency": {stage: _latency([e["latencies"][stage] for e in evaluations
                                     if e["latencies"][stage] is not None])
                    for stage in ("3c", "retr", "3d", "3e", "3f", "report", "total")},
    }


def run_benchmark(cases, records, incidents, mode, make_client, settings,
                  model_name, output_dir, retriever=None,
                  arms=("full", "baseline"), only=None):
    """Execute selected cases under selected arms; write bundles + evaluations."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluations = {arm: [] for arm in arms}
    for case in cases:
        if only and case["query_id"] not in only:
            continue
        for arm in arms:
            bundle = run_case(case, records, incidents, mode, make_client,
                              settings, model_name, arm, retriever)
            evaluation = evaluate_case(case, bundle)
            evaluations[arm].append(evaluation)
            with (output_dir / (case["query_id"] + "." + arm + ".json")).open(
                    "w", encoding="utf-8") as fh:
                json.dump(bundle, fh, indent=2, sort_keys=True)
    return evaluations


def main(argv=None):
    parser = argparse.ArgumentParser(description="Phase 5B.3: investigation evaluation")
    parser.add_argument("--benchmark", default=None)
    parser.add_argument("--evidence", default=None)
    parser.add_argument("--incidents", default=None)
    parser.add_argument("--vector-store", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--arm", default="both",
                        choices=("full", "baseline", "no-temporal",
                                 "no-verification", "no-planning", "full-lexical",
                                 "full-hybrid", "both"))
    parser.add_argument("--only", default=None)
    parser.add_argument("--timeout", type=float, default=None,
                        help="per-call overall LLM seconds (default: frozen 60s)")
    parser.add_argument("--no-total-timeout", action="store_true")
    parser.add_argument("--no-socket-timeout", action="store_true")
    args = parser.parse_args(argv)

    benchmark = Path(args.benchmark) if args.benchmark else \
        PROJECT_ROOT / "eval/investigation_benchmark_v1.json"
    output = Path(args.output) if args.output else \
        PROJECT_ROOT / "data/evaluations/investigation/v1"
    try:
        cases = load_cases(benchmark)
        default_evidence = PROJECT_ROOT / "data/data_155n/fused_155/evidence.json"
        default_incidents = PROJECT_ROOT / "data/data_155n/fused_155/incidents.json"
        records = load_evidence(
            Path(args.evidence) if args.evidence else default_evidence)
        incidents = load_incidents(
            Path(args.incidents) if args.incidents else default_incidents)
    except (OSError, ValueError) as exc:
        print("investigation eval error: bad input: " + str(exc))
        return 2
    only = [q.strip() for q in args.only.split(",")] if args.only else None
    arms = ("full", "baseline") if args.arm == "both" else (args.arm,)
    settings = Q.load_llm_settings()
    mode = "mock" if args.mock else "real"

    def _factory():
        if mode == "mock":
            return None
        client = Q.create_client(settings)
        if args.no_total_timeout:
            client.total_timeout = None
        elif args.timeout is not None:
            client.total_timeout = float(args.timeout)
        if args.no_socket_timeout:
            client.timeout = None
        return client

    retriever = None
    if mode == "real":
        from src.pipeline.vector_store import QdrantVectorRetriever
        store = Path(args.vector_store) if args.vector_store else \
            PROJECT_ROOT / "data/vector_155"
        retriever = QdrantVectorRetriever(store)
    import hashlib
    meta = {
        "benchmark": str(benchmark),
        "benchmark_sha256": hashlib.sha256(benchmark.read_bytes()).hexdigest(),
        "corpus": "data/data_155n/fused_155/evidence.json",
        "vector_index": "data/vector_155",
        "vector_model": "sentence-transformers/all-MiniLM-L6-v2",
        "rrf_constant": RRF_CONSTANT,
        "retrieval_top_k": RETRIEVAL_TOP_K,
        "provider": "mock" if mode == "mock" else settings.get("provider"),
        "model": "mock" if mode == "mock" else settings.get("model"),
        "arms": list(arms),
        "timeouts": {"timeout": args.timeout,
                     "total_unbounded": bool(args.no_total_timeout),
                     "socket_unbounded": bool(args.no_socket_timeout)},
        "git_revision": R.get_git_hash(),
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "n_cases": len([c for c in cases
                        if only is None or c["query_id"] in only]),
    }
    try:
        evaluations = run_benchmark(cases, records, incidents, mode, _factory,
                                    settings, meta["model"], output, retriever,
                                    arms, only)
    except (OSError, ValueError, KeyError) as exc:
        print("investigation eval error: " + str(exc))
        return 2
    finally:
        if retriever is not None:
            retriever.close()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "meta": meta,
        "mechanical_metrics": {arm: aggregate_arm(evaluations[arm]) for arm in arms},
        "evaluations": {arm: sorted(evaluations[arm],
                                    key=lambda e: e["query_id"]) for arm in arms},
        "human_evaluation_pending": True,
    }
    with (output / "results_investigation_v1.json").open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    for arm in arms:
        done = sum(1 for e in evaluations[arm] if e["failure"] is None)
        print("arm " + arm + ": " + str(done) + "/" + str(len(evaluations[arm])) +
              " completed -> " + str(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
