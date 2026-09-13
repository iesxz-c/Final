# AGENTS.md — Project Rules & Architectural Constraints

This file governs all work in this repository. Read it fully before making any
change. The AI agent (and human contributors) must follow it.

## Project identity

- Name: **Agentic Framework for Crime Investigation Using CCTV Video Analysis**
- Type: **academic research prototype** — not a production surveillance system.
- Base works are fixed (see README). They provide: cross-modal post-hoc
  surveillance (ingestion, object-focused processing, embeddings, vector
  search, text/image search, recursive search/filtering) and smart surveillance
  narration (object detection, activity recognition, timestamped event
  narration, keyword incident retrieval).
- **Our research contribution:** an *investigation layer* that operates on
  CCTV-derived evidence. That is the only contribution.

## Fixed architecture (do not redesign)

The pipeline is fixed:

```
CCTV VIDEO
 → video processing
 → object/activity/person/timestamp evidence
 → structured events
 → case memory
 → investigator natural-language query
 → query planning
 → evidence retrieval
 → temporal correlation
 → evidence verification
 → evidence-grounded investigation answer/report
```

The four logical investigation agents are fixed:

1. **Query Planning Agent**
2. **Evidence Retrieval Agent**
3. **Temporal/Correlation Agent**
4. **Verification + Report Agent**

Do **not**:
- replace, rename, reorder, or merge the pipeline stages;
- add new agents or new research contributions;
- invent features not present in the fixed architecture;
- expand scope beyond the current phase.

## Evidence-grounding (invariant)

- The LLM **must never invent facts**.
- Every claim in an answer/report must be traceable to evidence stored in the
  case memory.
- Claims lacking stored support must be omitted or explicitly flagged as
  unverified.
- Verification is a mandatory pipeline stage before report emission.

## Research / model constraints

- Do **not** build or propose new object detectors, activity-recognition
  models, foundation models, or VideoMAE-style architectures.
- Reuse existing/pretrained models and libraries where appropriate.
- Keep dependencies minimal: add a package only when a phase actually needs it.
- Do not download large models or datasets as part of normal development
  commands; weights and datasets are external/gitignored.

## Dataset policy

- The UCF-Crime dataset is **external** to this repository.
- Reference it only through configuration (`config/config.example.yaml`).
- Never copy, commit, or re-upload dataset content or video files.
- Keep dataset/normal-video directories in `.gitignore` (root-level entries
  already cover `Anomaly-Videos-Part-1/`,
  `Normal_Videos_for_Event_Recognition/`, etc.).
- Structure of the anomaly videos (fixed categories):
  `Abuse, Arrest, Arson, Assault, Burglary, Explosion, Fighting,
  RoadAccidents, Robbery, Shooting, Shoplifting, Stealing, Vandalism`
  plus separate normal surveillance videos.

## Configuration rules

- All paths (dataset, weights, outputs) are external/configurable — never
  hard-coded into source.
- Config lives in `config/`. Ship `config.example.yaml`; commit-time personal
  overrides (`config/config.yaml`) are gitignored.
- Environment overrides exist in `src/settings.py`
  (`CCTV_CASE_CONFIG`, `CCTV_ANOMALY_VIDEOS_DIR`, `CCTV_NORMAL_VIDEOS_DIR`).

## Code & repo conventions

- Layout: `src/<package>` layout; packages mirror the fixed pipeline
  (`src/pipeline`), evidence domain (`src/evidence`), and the four logical
  agents (`src/agents/*`).
- Phase discipline: implement only the current phase's scope. The roadmap is
  Phase 0 (skeleton/config/health check), Phase 1 (video processing →
  evidence → structured events), Phase 2 (case memory + four agents),
  Phase 3 (verification, report, evaluation).
- Keep the environment healthy: after changes run
  `python scripts/health_check.py`.
- No comments unless they add value; keep code minimal and typed where easy.

## Do / don't (operational)

- Do: create structure, config support, health checks, tests per phase.
- Do: reuse pretrained models, add minimal deps only when required.
- Don't: download datasets, bulk-process videos, implement agents/vector
  search/YOLO/frontend in phases that do not call for them.
- Don't: commit weights, embeddings, databases, videos, caches, or secrets
  (see `.gitignore`).