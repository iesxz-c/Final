# Colab runtime inventory (recovered, read-only)

## Sessions (all Tesla T4 15GB, CUDA 13.0 / driver 580.82.07)
| Notebook | Date (UTC) | Purpose | Key log lines |
|---|---|---|---|
| Final_yr_project.ipynb | 2026-09-14 | 40-video runs | health/inventory/subset, UCF limit2/max5, full UCF + activity + fusion, YOLO rerun |
| eval.ipynb | 2026-09-15 | 155-video UCF | nvidia-smi T4; 155 (112+43); smoke 1 video 20.2 s; full 155 run; resumable 702 start |
| eval2.ipynb | 2026-09-16 | 702 batches | T4 0/15360MiB; clone 196 objs; 702/702 unique; batch_001 (50) streaming |
| eval3.ipynb | 2026-09-16 | 702 resume+merge | COMPLETED 600→102; merge 702/44716 PASS; Drive copy |
| eval4.ipynb | 2026-09-17 | 155 YOLO/activity/fusion | Python 3.13.15, CUDA True; pip requirements; Explosion013 failure→fix; Drive backup |
| phase2c_ucf_videomae_colab.ipynb | undated | training template | gated RUN_FULL_TRAINING=False; sanity + full configs; never executed |

## Software (executed versions)
torch 2.11.0+cu128, torchvision 0.26.0+cu128, transformers 5.16.1,
ultralytics 8.4.154, numpy 2.1.3, sentence-transformers 5.6.0,
qdrant-client 1.19.1, PyYAML 6.0.3, Python 3.13.15 (Colab) / 3.14 (local).

## Model commits (frozen inference only)
- yolo11n / conf 0.4 / 1 fps
- MCG-NJU/videomae-base-finetuned-kinetics rev 488eb9a / 16f@8fps hop16 top5
- OPear/videomae-large-finetuned-UCF-Crime rev bc5f1c1 / 16f@8fps hop16 top5 224px
- sentence-transformers/all-MiniLM-L6-v2 rev 1110a24 / 384-dim cosine

## Training config (configured, NEVER executed)
--split 002 --epochs 10 --batch-size 4 --gradient-accumulation 2
--learning-rate 5e-5 --num-workers 4 --seed 0 --num-eval-clips 5.
Folds: train 532 lines (effective 531, Arson019 absent), test 168 (effective 167), overlap 0.
No checkpoints, metrics, or validation numbers exist in-repo.

## Wall-clock (manifest elapsed_seconds)
40-video: 2A 102.1 s, 2B 339.7 s, 2C 982.9 s, 2D 2.0 s.
155-video: 2A 823.1 s (+5.8 s Explosion013 fix), 2B 1439.0 s, 2C 3721.3 s, 2D 48.1 s.
Vector index: 250.6 s (CPU). 702: merged 2026-09-16, no elapsed field.

## Warnings/failures
HF Hub unauthenticated pulls; Explosion013 unreadable (recovered via merge);
eval4 `--max-videos` arg error (docs only); matplotlib optional skip.
