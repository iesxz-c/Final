"""Phase 2C - VideoMAE fine-tuning on the official UCF-Crime splits.

Fine-tunes the Phase 2B VideoMAE backbone (reusing its q_bias/v_bias
checkpoint remap) with a fresh 14-class head. Reads videos lazily from a
mounted dataset root (Drive on Colab); nothing is bulk-copied to RAM.
CUDA + mixed precision when available, frequent checkpoints + resume so
Colab interruptions are survivable.

Usage (Colab):
    python -m src.pipeline.train_activity --split 002 --device cuda \
        --epochs 10 --batch-size 4 --output-dir /content/drive/.../phase2c
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

from src.pipeline.activity import MODEL_ID, _load_kinetics_state_dict
from src.pipeline.ucf_splits import CLASS_NAMES, find_missing, load_fold


def set_seed(seed: int) -> None:
    import numpy as np
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def resolve_device(requested: str) -> str:
    import torch

    requested = (requested or "auto").lower()
    if requested in ("auto", "cuda") and torch.cuda.is_available():
        return "cuda"
    if requested == "cuda":
        print("CUDA requested but unavailable; falling back to cpu")
    return "cpu"


def build_model(model_id: str, device: str):
    from transformers import AutoConfig, AutoModelForVideoClassification

    config = AutoConfig.from_pretrained(model_id)
    config.num_labels = len(CLASS_NAMES)
    config.id2label = {i: name for i, name in enumerate(CLASS_NAMES)}
    config.label2id = {name: i for i, name in enumerate(CLASS_NAMES)}
    model = AutoModelForVideoClassification.from_config(config)
    notes = _load_kinetics_state_dict(model, model_id)  # backbone; fresh 14-class head
    head_shape = tuple(model.classifier.weight.shape)
    print(f"classifier head: {head_shape} (fresh, 14 UCF classes)")
    print(f"weights: {notes}")
    return model.to(device), notes


def compute_metrics(true: list, pred: list, num_classes: int) -> dict:
    import numpy as np

    true = np.asarray(true)
    pred = np.asarray(pred)
    confusion = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(true.tolist(), pred.tolist()):
        confusion[t, p] += 1
    per_class_f1 = []
    precisions, recalls = [], []
    for c in range(num_classes):
        tp = confusion[c, c]
        fp = confusion[:, c].sum() - tp
        fn = confusion[c, :].sum() - tp
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        precisions.append(prec)
        recalls.append(rec)
        per_class_f1.append(round(f1, 4))
    return {
        "accuracy": round(float((true == pred).mean()), 4),
        "macro_precision": round(float(sum(precisions) / num_classes), 4),
        "macro_recall": round(float(sum(recalls) / num_classes), 4),
        "macro_f1": round(float(sum(per_class_f1) / num_classes), 4),
        "per_class_f1": {CLASS_NAMES[c]: per_class_f1[c] for c in range(num_classes)},
        "confusion_matrix": confusion.tolist(),
        "n_videos": len(true),
    }


def load_inventory_frame_counts(config: dict) -> dict:
    """Map split-style references to known frame counts from Phase 1 inventory.

    Returns {} when no inventory is available (dataset falls back to counting
    by decoding). Keys are split references like 'Abuse/x.mp4' so lookups
    need no path translation.
    """
    inventory_cfg = config.get("inventory") or {}
    inventory_path = PROJECT_ROOT / inventory_cfg.get("output_dir", "data/inventory") / "videos.json"
    if not inventory_path.exists():
        return {}
    try:
        with inventory_path.open("r", encoding="utf-8") as fh:
            records = json.load(fh)
    except (OSError, ValueError):
        return {}
    counts = {}
    for record in records:
        rel = record.get("path", "")
        category = record.get("category", "")
        count = record.get("frame_count")
        if not rel or not count:
            continue
        if category == "Normal":
            counts["Normal_Videos_event/" + rel.split("/")[-1]] = int(count)
        else:
            counts[rel] = int(count)
    return counts


def save_checkpoint(path: Path, model, optimizer, scheduler, scaler, epoch: int,
                    global_step: int, best_acc: float) -> None:
    import numpy as np
    import torch

    path.mkdir(parents=True, exist_ok=True)
    torch.save({
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict() if optimizer else None,
        "scheduler_state": scheduler.state_dict() if scheduler else None,
        "scaler_state": scaler.state_dict() if scaler else None,
        "epoch": epoch,
        "global_step": global_step,
        "best_acc": best_acc,
        "torch_rng": torch.get_rng_state(),
        "cuda_rng": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        "numpy_rng": np.random.get_state(),
        "python_rng": random.getstate(),
    }, path / "checkpoint.pt")
    with (path / "meta.json").open("w", encoding="utf-8") as fh:
        json.dump({"epoch": epoch, "global_step": global_step, "best_acc": best_acc,
                   "saved_utc": datetime.now(timezone.utc).isoformat()}, fh, indent=2)


def load_checkpoint(path: Path, model, optimizer=None, scheduler=None, scaler=None) -> dict:
    import numpy as np
    import torch

    ckpt = torch.load(path / "checkpoint.pt", map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt["model_state"])
    if optimizer is not None and ckpt.get("optimizer_state"):
        optimizer.load_state_dict(ckpt["optimizer_state"])
    if scheduler is not None and ckpt.get("scheduler_state"):
        scheduler.load_state_dict(ckpt["scheduler_state"])
    if scaler is not None and ckpt.get("scaler_state"):
        scaler.load_state_dict(ckpt["scaler_state"])
    torch.set_rng_state(ckpt["torch_rng"])
    if ckpt.get("cuda_rng") is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(ckpt["cuda_rng"])
    np.random.set_state(ckpt["numpy_rng"])
    random.setstate(ckpt["python_rng"])
    return {"epoch": ckpt["epoch"], "global_step": ckpt["global_step"],
            "best_acc": ckpt.get("best_acc", 0.0)}


def latest_checkpoint(output_dir: Path) -> Path | None:
    candidates = sorted(output_dir.glob("checkpoint-epoch*"), key=lambda p: p.stat().st_mtime)
    return candidates[-1] if candidates else None


def resolve_eval_checkpoint(output_dir: Path, resume_from: str | None) -> Path:
    """Pick the checkpoint an eval-only run must load.

    Precedence: explicit --resume-from, then checkpoint-best, final_model,
    newest checkpoint-epoch*/checkpoint-step*. Raises FileNotFoundError when
    the output dir holds no trained checkpoint (evaluating a fresh head
    would silently report ~0 metrics).
    """
    if resume_from:
        path = Path(resume_from)
        if not (path / "checkpoint.pt").exists():
            raise FileNotFoundError(f"no checkpoint.pt in --resume-from {path}")
        return path
    for name in ("checkpoint-best", "final_model"):
        path = output_dir / name
        if (path / "checkpoint.pt").exists():
            return path
    stepped = sorted(list(output_dir.glob("checkpoint-epoch*")) + list(output_dir.glob("checkpoint-step*")),
                     key=lambda p: p.stat().st_mtime)
    stepped = [p for p in stepped if (p / "checkpoint.pt").exists()]
    if stepped:
        return stepped[-1]
    raise FileNotFoundError(
        f"no trained checkpoint in {output_dir} (looked for checkpoint-best, "
        f"final_model, checkpoint-epoch*/checkpoint-step*). Train first or "
        f"pass --resume-from <checkpoint dir>.")


def train_one_epoch(model, loader, optimizer, scheduler, scaler, device: str,
                    accum_steps: int, global_step: int, log, save_every: int = 0,
                    output_dir: Path | None = None, epoch: int = 0,
                    best_acc: float = 0.0) -> int:
    import torch

    model.train()
    optimizer.zero_grad(set_to_none=True)
    use_amp = device == "cuda"
    for clips, labels, _ in loader:
        clips = clips.to(device)
        labels = labels.to(device)
        with torch.amp.autocast("cuda", enabled=use_amp):
            loss = model(pixel_values=clips, labels=labels).loss / accum_steps
        if scaler is not None:
            scaler.scale(loss).backward()
        else:
            loss.backward()
        global_step += 1
        if global_step % accum_steps == 0:
            if scaler is not None:
                scaler.step(optimizer)
                scaler.update()
            else:
                optimizer.step()
            if scheduler is not None:
                scheduler.step()
            optimizer.zero_grad(set_to_none=True)
        if global_step % 25 == 0:
            log({"step": global_step, "loss": round(float(loss * accum_steps), 4)})
        if save_every and output_dir is not None and global_step % save_every == 0:
            save_checkpoint(output_dir / f"checkpoint-step{global_step}", model, optimizer,
                            scheduler, scaler, epoch, global_step, best_acc)
    return global_step


def evaluate(model, loader, device: str, num_classes: int) -> dict:
    """Video-level evaluation: average clip softmax probabilities per video."""
    import numpy as np
    import torch

    model.eval()
    video_probs: dict = {}
    video_labels: dict = {}
    with torch.no_grad():
        for clips, labels, positions in loader:
            clips = clips.to(device)
            logits = model(pixel_values=clips).logits
            probs = torch.softmax(logits, dim=1).cpu().numpy()
            for prob, label, pos in zip(probs, labels.tolist(), positions.tolist()):
                video_probs.setdefault(pos, []).append(prob)
                video_labels[pos] = label
    true, pred = [], []
    for pos in sorted(video_probs):
        mean_prob = np.mean(np.stack(video_probs[pos]), axis=0)
        true.append(video_labels[pos])
        pred.append(int(mean_prob.argmax()))
    return compute_metrics(true, pred, num_classes)


def main(argv: list | None = None) -> int:
    import numpy as np
    import torch
    from torch.utils.data import DataLoader
    from transformers import get_linear_schedule_with_warmup

    from src.settings import dataset_paths, load_config
    from src.pipeline.activity_data import UCFClipDataset

    parser = argparse.ArgumentParser(description="Phase 2C: fine-tune VideoMAE on UCF-Crime")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--split", default="002")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--gradient-accumulation", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output-dir", default="data/evidence/phase2c")
    parser.add_argument("--max-train-videos", type=int, default=None)
    parser.add_argument("--max-test-videos", type=int, default=None)
    parser.add_argument("--config", default=None)
    parser.add_argument("--anomaly-root", default=None)
    parser.add_argument("--normal-root", default=None)
    parser.add_argument("--split-root", default=None)
    parser.add_argument("--model-id", default=MODEL_ID)
    parser.add_argument("--num-eval-clips", type=int, default=5)
    parser.add_argument("--save-every", type=int, default=100)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--resume-from", default=None)
    parser.add_argument("--eval-only", action="store_true")
    args = parser.parse_args(argv)

    set_seed(args.seed)
    device = resolve_device(args.device)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(args.config)
    paths = dataset_paths(config)
    anomaly_root = Path(args.anomaly_root) if args.anomaly_root else paths["anomaly_videos"]
    normal_root = Path(args.normal_root) if args.normal_root else paths["normal_videos"]
    split_root = Path(args.split_root) if args.split_root else (
        PROJECT_ROOT / "UCF_Crimes-Train-Test-Split" / "Action_Regnition_splits")

    train_entries, test_entries = load_fold(split_root, args.split)
    train_missing = find_missing(anomaly_root, normal_root, [r for (r, _) in train_entries])
    test_missing = find_missing(anomaly_root, normal_root, [r for (r, _) in test_entries])
    train_entries = [(r, l) for (r, l) in train_entries if r not in set(train_missing)]
    test_entries = [(r, l) for (r, l) in test_entries if r not in set(test_missing)]
    if args.max_train_videos is not None:
        train_entries = train_entries[: args.max_train_videos]
    if args.max_test_videos is not None:
        test_entries = test_entries[: args.max_test_videos]
    print(f"train videos: {len(train_entries)} (skipped {len(train_missing)} missing), "
          f"test videos: {len(test_entries)} (skipped {len(test_missing)} missing)")

    with (output_dir / "config_used.json").open("w", encoding="utf-8") as fh:
        json.dump({"args": vars(args), "anomaly_root": str(anomaly_root),
                   "normal_root": str(normal_root), "split_root": str(split_root),
                   "classes": CLASS_NAMES,
                   "skipped_missing": {"train": train_missing, "test": test_missing}},
                  fh, indent=2, default=str)
    with (output_dir / "label_map.json").open("w", encoding="utf-8") as fh:
        json.dump({str(i): name for i, name in enumerate(CLASS_NAMES)}, fh, indent=2)

    model, weight_notes = build_model(args.model_id, device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    frame_counts = load_inventory_frame_counts(config)
    train_ds = UCFClipDataset(train_entries, anomaly_root, normal_root, mode="train",
                              seed=args.seed, frame_counts=frame_counts)
    test_ds = UCFClipDataset(test_entries, anomaly_root, normal_root, mode="eval",
                             num_eval_clips=args.num_eval_clips, seed=args.seed,
                             frame_counts=frame_counts)
    print(f"frame counts known for {len(frame_counts)} videos "
          f"(0 = fallback: decode to count)")
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              num_workers=args.num_workers)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False,
                             num_workers=args.num_workers)

    steps_per_epoch = max(1, (len(train_loader) + args.gradient_accumulation - 1)
                           // args.gradient_accumulation)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=max(1, steps_per_epoch // 10),
        num_training_steps=max(1, steps_per_epoch * args.epochs))
    scaler = torch.amp.GradScaler("cuda") if device == "cuda" else None

    start_epoch, global_step, best_acc = 0, 0, 0.0
    resume_path = Path(args.resume_from) if args.resume_from else None
    if resume_path is None and args.resume:
        resume_path = latest_checkpoint(output_dir)
    if resume_path is not None:
        state = load_checkpoint(resume_path, model, optimizer, scheduler, scaler)
        start_epoch, global_step, best_acc = state["epoch"] + 1, state["global_step"], state["best_acc"]
        print(f"resumed from {resume_path} at epoch {start_epoch}, step {global_step}")
    model.to(device)

    log_path = output_dir / "training_log.jsonl"
    def log(record: dict):
        record["utc"] = datetime.now(timezone.utc).isoformat()
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    if not args.eval_only:
        t0 = time.perf_counter()
        for epoch in range(start_epoch, args.epochs):
            train_ds.set_epoch(epoch)
            global_step = train_one_epoch(
                model, train_loader, optimizer, scheduler, scaler, device,
                args.gradient_accumulation, global_step, log,
                save_every=args.save_every, output_dir=output_dir,
                epoch=epoch, best_acc=best_acc)
            metrics = evaluate(model, test_loader, device, len(CLASS_NAMES))
            metrics.update({"epoch": epoch, "global_step": global_step})
            with (output_dir / f"metrics_epoch{epoch}.json").open("w", encoding="utf-8") as fh:
                json.dump(metrics, fh, indent=2)
            log({"epoch": epoch, **{k: metrics[k] for k in ("accuracy", "macro_f1")}})
            print(f"epoch {epoch}: acc={metrics['accuracy']} macro_f1={metrics['macro_f1']}")
            save_checkpoint(output_dir / f"checkpoint-epoch{epoch}", model, optimizer,
                            scheduler, scaler, epoch, global_step, best_acc)
            if metrics["accuracy"] > best_acc:
                best_acc = metrics["accuracy"]
                save_checkpoint(output_dir / "checkpoint-best", model, optimizer,
                                scheduler, scaler, epoch, global_step, best_acc)
        print(f"training done in {round(time.perf_counter() - t0, 1)}s, best_acc={best_acc}")

    if args.eval_only:
        eval_ckpt = resolve_eval_checkpoint(output_dir, args.resume_from)
        load_checkpoint(eval_ckpt, model)
        print(f"eval-only: loaded trained weights from {eval_ckpt}")

    final = evaluate(model, test_loader, device, len(CLASS_NAMES))
    final["weight_notes"] = weight_notes
    with (output_dir / "metrics_final.json").open("w", encoding="utf-8") as fh:
        json.dump(final, fh, indent=2)
    save_checkpoint(output_dir / "final_model", model, None, None, None,
                    args.epochs - 1, global_step, best_acc)
    print(f"FINAL accuracy={final['accuracy']} macro_f1={final['macro_f1']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
