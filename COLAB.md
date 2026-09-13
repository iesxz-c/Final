# Colab GPU runbook — full 40-video Phase 2B inference

> Videos are **never** committed to git. Keep them in Google Drive and mount
> it in Colab. Re-running inventory + subset on the same folder structure
> reproduces the identical 40-video subset (selection is deterministic on
> relative `video_id`s).

## 0. Prepare Google Drive (one-time, on your machine)

Upload the dataset folders to Drive, preserving structure, e.g.:

```
MyDrive/ucf-crime/Anomaly-Videos-Part-1/Anomaly-Videos-Part-1/<Abuse,...>/*.mp4
MyDrive/ucf-crime/Normal_Videos_for_Event_Recognition/Normal_Videos_for_Event_Recognition/*.mp4
```

(Alternative: `python scripts/make_colab_package.py` zips just the 40 subset
videos + inventory for upload; after unzipping on Drive, the steps below are
identical.)

## 1. New Colab notebook (GPU: Runtime → Change runtime type → T4 GPU)

```python
!nvidia-smi
!git clone https://github.com/iesxz-c/Final.git
%cd Final
```

## 2. Mount Drive + install deps

```python
from google.colab import drive
drive.mount('/content/drive')
```

```python
!pip install -q ultralytics transformers pyyaml safetensors huggingface_hub
```

(Colab already ships CUDA-enabled torch; the above must not downgrade it —
if `pip` tries to replace torch, reinstall Colab's default torch build.)

## 3. Point the project at Drive (no config files needed)

```python
import os
os.environ['CCTV_ANOMALY_VIDEOS_DIR'] = '/content/drive/MyDrive/ucf-crime/Anomaly-Videos-Part-1/Anomaly-Videos-Part-1'
os.environ['CCTV_NORMAL_VIDEOS_DIR'] = '/content/drive/MyDrive/ucf-crime/Normal_Videos_for_Event_Recognition/Normal_Videos_for_Event_Recognition'
```

(`os.environ` set here is inherited by the `!python` subshells below.)

## 4. Verify, inventory, subset

```python
!python scripts/health_check.py
!python -m src.pipeline.inventory
!python -m src.pipeline.select_subset
```

Expect: 994 videos inventoried, subset = exactly 40 (8×5).

## 5. Full Phase 2B inference on GPU

```python
!python -m src.pipeline.extract_activity --device cuda
```

Writes `data/evidence/phase2b/{videos.json, activities.json, manifest.json}`.
Rough estimate on a T4: tens of minutes for ~2000 windows; progress prints
per video, and one bad video never stops the run (see `manifest.failures`).

## 6. Copy results back to Drive

```python
!mkdir -p /content/drive/MyDrive/ucf-crime-output/phase2b
!cp data/evidence/phase2b/*.json /content/drive/MyDrive/ucf-crime-output/phase2b/
```

Then download from Drive to this machine and place under
`data/evidence/phase2b/` (gitignored) for analysis.
