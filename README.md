# Agentic Framework for Crime Investigation Using CCTV Video Analysis

Academic **research prototype** (not a production surveillance system).

We build an **investigation layer** on top of CCTV-derived evidence: instead of
merely detecting and indexing what happens in surveillance video, the system
gives an investigator a natural-language interface to interrogate a case, plan
queries, retrieve evidence, correlate it across time, verify claims against
stored evidence, and produce an **evidence-grounded** investigation report.

## Fixed architecture

The research direction is fixed and builds on two base works:

- **Base paper 1** — cross-modal post-hoc surveillance: video ingestion,
  visual/object-focused processing, embeddings, vector search, text/image
  search, recursive search and filtering.
- **Base paper 2** — smart surveillance narrator: object detection, activity
  recognition, timestamped event narration, keyword-based incident retrieval.

**Our contribution** is the investigation layer that operates on top of that
CCTV-derived evidence.

### Intended pipeline

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

### The four logical investigation agents

1. **Query Planning Agent** — decompose the investigator's natural-language
   query into retrievable sub-queries over the case memory.
2. **Evidence Retrieval Agent** — pull evidence from the case memory
   (semantic / keyword / temporal lookups).
3. **Temporal/Correlation Agent** — correlate timestamped evidence into
   timelines and a coherent narrative of events.
4. **Verification + Report Agent** — check every claim of the draft answer
   against stored evidence and emit the final investigation report.

### Evidence-grounding rule

The language model **must not invent facts**. Every assertion in an answer or
report must be supported by evidence actually stored in the case memory,
otherwise it is either omitted or explicitly flagged as unverified.

### What this project is NOT

- It does **not** propose a new object detector, activity model, foundation
  model, or VideoMAE-style architecture.
- Pretrained/existing models are reused where appropriate.

## Dataset (external, not in this repo)

The [UCF-Crime](https://webpages.charlotte.edu/cchen62/dataset.html) dataset is
kept **outside** this repository. Only paths are configured
(`config/config.example.yaml`). Anomaly videos are organised into categories:

```
Abuse, Arrest, Arson, Assault, Burglary, Explosion, Fighting, RoadAccidents,
Robbery, Shooting, Shoplifting, Stealing, Vandalism
```

plus separate normal surveillance videos.

## Getting started (Phase 0)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# optional: copy the example config and adjust dataset paths
Copy-Item config\config.example.yaml config\config.yaml

# verify the environment
python scripts\health_check.py
```

## Phase 1 — dataset inventory (current)

Read-only scan of the configured UCF-Crime dataset into a machine-readable
inventory. No video is modified; metadata is read from container headers
only (no decoding, no full-file loads). Zero new dependencies.

```powershell
# scan the configured dataset and write data/inventory/{videos.json,videos.csv,summary.json}
python -m src.pipeline.inventory

# useful options
python -m src.pipeline.inventory --help
python -m src.pipeline.inventory --limit 5        # debug: cap files per source
python -m src.pipeline.inventory --output-dir data/inventory-test
python -m src.pipeline.inventory --absolute-paths # also store absolute paths

# run the inventory tests (self-contained, no dataset needed)
python -m unittest discover -s tests -t .
```

Inventory records store paths **relative** to each configured dataset root
(`path: "Burglary/Burglary001_x264.mp4"`), so outputs stay portable across
machines. `data/` is gitignored and never committed.

Each record contains: `video_id`, `filename`, `source_type`
(`anomaly`/`normal`), `category` (anomaly folder name, or `"Normal"`),
`path`, `format`, `file_size_bytes`, `duration_seconds`, `fps`, `width`,
`height`, `frame_count`, `metadata_ok`, `metadata_error`. The summary
reports totals, per-category counts/durations, format counts, and any files
whose metadata could not be read.

## Phase 2A — experimental subset + video evidence extraction (current)

First working CCTV evidence pipeline on a small, controlled experiment:
**exactly 40 videos** (5 each of Fighting, Assault, Robbery, Shooting,
Shoplifting, Stealing, Vandalism, Normal), selected **deterministically**
from the Phase 1 inventory (stable sort by `video_id`, first N per
category). Videos stay external; nothing is copied into the repo.

```powershell
pip install -r requirements.txt  # adds ultralytics for detection

# 1. select the deterministic 40-video subset
python -m src.pipeline.select_subset
# -> data/experiments/phase2_subset.json (validates 8x5 = 40)

# 2. sample frames (1 FPS default) + run pretrained YOLO11n on CPU
python -m src.pipeline.extract_evidence
# -> data/evidence/phase2/{videos,observations,detections,manifest}.json

# useful options
python -m src.pipeline.extract_evidence --limit-videos 1 --max-frames 3
python -m src.pipeline.extract_evidence --device cuda   # when a GPU exists
python -m src.pipeline.extract_evidence --skip-detection  # sampling only
python -m src.pipeline.extract_evidence --save-frames 5  # debug stills

# tests (self-contained: tiny synthetic videos + mocked detections)
python -m unittest discover -s tests -t .
```

### CPU/GPU configuration

`detection.device` in config (`cpu` default, `cuda` when available).
CUDA is never required: the detector falls back to CPU with a warning.
Weights (`data/models/yolo11n.pt`, ~5MB, gitignored) are reused as-is;
**no model is trained** in this phase. The setup is portable to Colab for
later GPU runs.

### Evidence schema (`src/evidence/models.py`)

- `VideoRecord` — video_id, source_type, `ground_truth_category`,
  dataset_root/path, duration/fps/dimensions.
- `FrameObservation` — observation_id (`video_id:f{frame}`), timestamp,
  frame_index, source_reference (`video_id@t=..s#f..`).
- `ObjectDetection` — detection_id, observation/ video ids, timestamp,
  model-native `class_name` + `confidence`, bounding box, model name.
  Every detection traces back to video → timestamp → frame/observation.

### Ground truth vs model evidence (research rule)

- `ground_truth_category` (e.g. `"Fighting"`) is **dataset metadata only**.
- The system never emits `activity = "Fighting"` from the folder name;
  activity labels may only come from a future inference step.
- Detections store the detector's actual class names (person, car, …);
  COCO-pretrained YOLO has limited weapon classes, so no weapon-detection
  reliability is claimed.

## Phase 2B — activity evidence extraction (current)

Independent temporal stream alongside Phase 2A objects: each video of the
same deterministic 40-video subset is split into sliding 16-frame windows,
classified by pretrained **VideoMAE-Base fine-tuned on Kinetics-400**
(`MCG-NJU/videomae-base-finetuned-kinetics`, inference only — never
trained/fine-tuned), producing timestamped `ActivityObservation` records
with raw Kinetics labels + top-5 predictions.

```powershell
pip install -r requirements.txt  # adds transformers for VideoMAE

# run activity inference on the 40-video subset (CPU unless CUDA exists)
python -m src.pipeline.extract_activity
# -> data/evidence/phase2b/{videos,activities,manifest}.json

# useful options
python -m src.pipeline.extract_activity --limit-videos 1 --max-windows 1
python -m src.pipeline.extract_activity --device cuda   # when a GPU exists

# tests (mocks/synthetic frames only: no download, no GPU, no inference)
python -m unittest discover -s tests -t .
```

Defaults (`activity_model` in config): 16 frames/window, 8 FPS sampling
(~2s windows), non-overlapping hop, top-5, `device: auto` (CUDA → GPU,
otherwise CPU; never requires CUDA). Videos stream window-by-window; only
the current 16 frames sit in memory.

### Ground truth vs model evidence (research rule)

- `ground_truth_category` (e.g. `"Fighting"`) is dataset metadata only. It
  is never passed to VideoMAE, never copied into `ActivityObservation.label`.
- Labels are raw Kinetics-400 names (`"jumpstyle dancing"`, `"tai chi"`,
  …). Kinetics has no surveillance-crime classes, so no claim is made that
  VideoMAE recognizes crimes; confidence varies with how salient the
  motion is (peaked ~0.45 on strong motion, near-uniform on static scenes).

### Known weight-loading note

The published checkpoint stores DeiT-style `q_bias`/`v_bias` tensors while
current `transformers` expects `query/key/value.bias` (checkpoint config
has `qkv_bias=True`). Stock `from_pretrained` therefore loads all weights
except the 24 learned query/value biases, which silently stay at HF
default zero-init — verified weight-for-weight, and same-window inference
collapses from a peaked 0.45 to near-uniform 0.03 without the fix. The
pipeline maps q/v onto their learned values and zeroes the
(upstream-absent) key bias, recorded per-run as `model.weight_notes` in
the manifest.

## Phase 2C — VideoMAE fine-tuning on UCF-Crime (Colab GPU, in preparation)

Fine-tunes the Phase 2B VideoMAE backbone (same q_bias/v_bias remap, fresh
14-class head) on the **official** Action Recognition splits — Fold 2
(`train_002.txt`/`test_002.txt`): 532 train / 168 test videos (effective
532/167; `Arson/Arson019_x264.mp4` is the single locally missing file).
No random splits; folder labels are training targets only for this
fine-tuning stage, never model outputs elsewhere.

```powershell
# validate the official split (read-only, local)
python -m src.pipeline.ucf_splits --split 002

# clip-dataset smoke test (decodes 2 real videos, no model/training)
python -m src.pipeline.activity_data --split 002 --num-videos 2

# full run happens on Colab — see notebooks/phase2c_ucf_videomae_colab.ipynb
```

Colab cells in order: env check → install → Drive mount → paths →
split validation → data smoke → load VideoMAE → 14-class head check →
20/10-video 1-epoch sanity → sanity eval → **gated** full Fold-2 training
(`RUN_FULL_TRAINING` must be set True) → full eval → metrics (accuracy,
macro P/R/F1, per-class F1, confusion matrix) → copy artifacts to Drive.

Training features: lazy 16-frame windows (train: seeded random window per
epoch; eval: evenly spaced windows with per-video softmax averaging),
CUDA + mixed precision, checkpoints every N steps + every epoch + best,
resume from checkpoint, all metrics/checkpoints under the output dir
(kept on Drive on Colab).

## Repository layout

```
config/
  config.example.yaml      dataset paths (external) + reserved pipeline config
scripts/
  health_check.py          phase 0 environment verification
src/
  settings.py              configuration loading + env overrides
  pipeline/
    inventory.py           phase 1 dataset inventory (CLI: python -m src.pipeline.inventory)
    select_subset.py       phase 2A deterministic 40-video subset
    extract_evidence.py    phase 2A sampling + detection pipeline
    detect.py              YOLO / mock detector backends
    activity.py            phase 2B VideoMAE / mock activity backends
    extract_activity.py    phase 2B windowed activity pipeline
  evidence/
    models.py              VideoRecord, FrameObservation, ObjectDetection,
                           ActivityObservation
    __init__.py            (package skeleton for future models)
  agents/
    query_planning/        Agent 1 (Phase 2+)
    evidence_retrieval/    Agent 2 (Phase 2+)
    temporal_correlation/  Agent 3 (Phase 2+)
    verification_report/   Agent 4 (Phase 2+)
tests/
  test_inventory.py        phase 1 tests (unittest, no dataset needed)
data/                      local outputs (gitignored)
  inventory/               generated inventory outputs (videos.json/csv, summary.json)
```

## Roadmap

- **Phase 0** (done): project skeleton, configuration support, health check.
- **Phase 1** (done): dataset inventory → video ingestion +
  video processing → object/activity/person/timestamp evidence →
  structured events.
- **Phase 2** (current, step A): 40-video experimental subset + frame
  sampling + pretrained object evidence (no agents/LLM/memory yet).
- **Phase 2** (current, step B): windowed VideoMAE activity evidence on the
  same 40 videos (no agents/LLM/memory/fusion yet).
- **Phase 2**: case memory construction and the four investigation agents.
- **Phase 3**: evidence verification, report generation, evaluation.

Phases are implemented strictly in this order; no stage is skipped.

## Contributing / working here

Read `AGENTS.md` — it contains the project rules and architectural
constraints. The research direction and architecture are **fixed**; do not
replace, rename, or extend them without explicit instruction.

## Ethics notice

This is an academic prototype used with research datasets. It is not intended
for real-world deployment, and no production surveillance use is implied.