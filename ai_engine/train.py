"""
Training Pipeline for Traffic Prediction Models
Handles data preprocessing, dataset creation, training loop, evaluation, and checkpointing.
"""

import os
import sys
import json
import time
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_engine.model import TrafficLSTM, TrafficTransformer, count_parameters


# ────────────────────────────────────────────
# DATASET
# ────────────────────────────────────────────
FEATURE_COLUMNS = [
    "Traffic_Volume", "Cars", "Motorcycles", "Buses", "Trucks",
    "Emergency_Vehicles", "Queue_Length", "Average_Wait_Time_min",
    "Average_Speed_kmh", "Throughput", "V_C_Ratio", "CO2_Emissions_g",
]

TARGET_COLUMNS = [
    "Traffic_Volume",       # regression
    "Congestion_Numeric",   # classification (0-3)
    "Average_Speed_kmh",    # regression
    "Green_Signal_sec",     # regression (target optimal)
    "Average_Wait_Time_min",# regression
]

CONGESTION_MAP = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}


class TrafficDataset(Dataset):
    """Sliding window dataset for time-series traffic prediction."""

    def __init__(self, data: np.ndarray, targets: np.ndarray, seq_len: int = 16):
        self.seq_len = seq_len
        self.data = data
        self.targets = targets

    def __len__(self):
        return len(self.data) - self.seq_len

    def __getitem__(self, idx):
        x = self.data[idx : idx + self.seq_len]
        y = self.targets[idx + self.seq_len]
        return torch.FloatTensor(x), {
            "volume": torch.FloatTensor([y[0]]),
            "congestion": torch.LongTensor([int(y[1])]),
            "speed": torch.FloatTensor([y[2]]),
            "green_time": torch.FloatTensor([y[3]]),
            "wait_time": torch.FloatTensor([y[4]]),
        }


def prepare_data(csv_path: str, seq_len: int = 16, test_ratio: float = 0.15, val_ratio: float = 0.15):
    """
    Load CSV, preprocess, and split into train/val/test datasets.
    Data is split temporally (no shuffle) to respect time ordering.
    """
    df = pd.read_csv(csv_path)
    df["Congestion_Numeric"] = df["Congestion_Level"].map(CONGESTION_MAP)

    # Process per-intersection sequences, then concatenate
    intersections = df["Intersection_ID"].unique()
    all_features = []
    all_targets = []

    for junction in sorted(intersections):
        jdf = df[df["Intersection_ID"] == junction].sort_values("Timestamp").reset_index(drop=True)

        features = jdf[FEATURE_COLUMNS].values.astype(np.float32)
        targets = jdf[TARGET_COLUMNS].values.astype(np.float32)

        all_features.append(features)
        all_targets.append(targets)

    # Stack all intersections (process each independently during windowing)
    # Normalize features
    all_features_flat = np.concatenate(all_features, axis=0)
    feature_mean = all_features_flat.mean(axis=0)
    feature_std = all_features_flat.std(axis=0) + 1e-8

    # Target normalization (for volume, speed, green_time, wait_time — NOT congestion)
    target_mean = all_features_flat[:, 0].mean()  # volume mean
    target_std = all_features_flat[:, 0].std() + 1e-8

    datasets = {"train": [], "val": [], "test": []}

    for features, targets in zip(all_features, all_targets):
        n = len(features)
        if n <= seq_len + 3:
            continue

        # Normalize features
        features_norm = (features - feature_mean) / feature_std

        # Temporal split
        train_end = int(n * (1 - test_ratio - val_ratio))
        val_end = int(n * (1 - test_ratio))

        splits = {
            "train": (0, train_end),
            "val": (train_end, val_end),
            "test": (val_end, n),
        }

        for split_name, (start, end) in splits.items():
            if end - start > seq_len:
                datasets[split_name].append((features_norm[start:end], targets[start:end]))

    # Concatenate per-intersection datasets
    result = {}
    normalization_params = {
        "feature_mean": feature_mean.tolist(),
        "feature_std": feature_std.tolist(),
        "target_mean": float(target_mean),
        "target_std": float(target_std),
    }

    for split_name in ["train", "val", "test"]:
        if datasets[split_name]:
            all_f = np.concatenate([d[0] for d in datasets[split_name]], axis=0)
            all_t = np.concatenate([d[1] for d in datasets[split_name]], axis=0)
            result[split_name] = TrafficDataset(all_f, all_t, seq_len)
        else:
            result[split_name] = None

    return result, normalization_params


# ────────────────────────────────────────────
# TRAINING
# ────────────────────────────────────────────
class MultiTaskLoss(nn.Module):
    """Combined loss for multi-task traffic prediction."""

    def __init__(self, volume_weight=1.0, congestion_weight=1.0,
                 speed_weight=0.5, green_weight=0.5, wait_weight=0.5):
        super().__init__()
        self.mse = nn.MSELoss()
        self.ce = nn.CrossEntropyLoss()
        self.weights = {
            "volume": volume_weight,
            "congestion": congestion_weight,
            "speed": speed_weight,
            "green": green_weight,
            "wait": wait_weight,
        }

    def forward(self, predictions, targets):
        loss_volume = self.mse(predictions["volume"], targets["volume"].squeeze())
        loss_congestion = self.ce(predictions["congestion_logits"], targets["congestion"].squeeze())
        loss_speed = self.mse(predictions["speed"], targets["speed"].squeeze())
        loss_green = self.mse(predictions["green_time"], targets["green_time"].squeeze())
        loss_wait = self.mse(predictions["wait_time"], targets["wait_time"].squeeze())

        total = (
            self.weights["volume"] * loss_volume +
            self.weights["congestion"] * loss_congestion +
            self.weights["speed"] * loss_speed +
            self.weights["green"] * loss_green +
            self.weights["wait"] * loss_wait
        )

        return total, {
            "volume": loss_volume.item(),
            "congestion": loss_congestion.item(),
            "speed": loss_speed.item(),
            "green": loss_green.item(),
            "wait": loss_wait.item(),
            "total": total.item(),
        }


def train_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_losses = {}
    n_batches = 0

    for batch_x, batch_y in dataloader:
        batch_x = batch_x.to(device)
        batch_y = {k: v.to(device) for k, v in batch_y.items()}

        optimizer.zero_grad()
        predictions = model(batch_x)
        loss, loss_dict = criterion(predictions, batch_y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        for k, v in loss_dict.items():
            total_losses[k] = total_losses.get(k, 0) + v
        n_batches += 1

    avg_losses = {k: v / max(n_batches, 1) for k, v in total_losses.items()}
    return avg_losses


def evaluate(model, dataloader, criterion, device):
    model.eval()
    total_losses = {}
    n_batches = 0
    all_preds = {"congestion": [], "volume": [], "speed": []}
    all_targets = {"congestion": [], "volume": [], "speed": []}

    with torch.no_grad():
        for batch_x, batch_y in dataloader:
            batch_x = batch_x.to(device)
            batch_y = {k: v.to(device) for k, v in batch_y.items()}

            predictions = model(batch_x)
            _, loss_dict = criterion(predictions, batch_y)

            for k, v in loss_dict.items():
                total_losses[k] = total_losses.get(k, 0) + v
            n_batches += 1

            # Collect predictions for metrics
            all_preds["congestion"].append(predictions["congestion_logits"].argmax(dim=1).cpu().numpy())
            all_preds["volume"].append(predictions["volume"].cpu().numpy())
            all_preds["speed"].append(predictions["speed"].cpu().numpy())
            all_targets["congestion"].append(batch_y["congestion"].squeeze().cpu().numpy())
            all_targets["volume"].append(batch_y["volume"].squeeze().cpu().numpy())
            all_targets["speed"].append(batch_y["speed"].squeeze().cpu().numpy())

    avg_losses = {k: v / max(n_batches, 1) for k, v in total_losses.items()}

    # Compute accuracy for congestion classification
    congestion_preds = np.concatenate(all_preds["congestion"])
    congestion_targets = np.concatenate(all_targets["congestion"])
    accuracy = (congestion_preds == congestion_targets).mean()

    # Compute MAE for volume
    volume_preds = np.concatenate(all_preds["volume"])
    volume_targets = np.concatenate(all_targets["volume"])
    volume_mae = np.abs(volume_preds - volume_targets).mean()

    avg_losses["congestion_accuracy"] = accuracy
    avg_losses["volume_mae"] = volume_mae

    return avg_losses


def train(
    csv_path: str = "traffic_simulation.csv",
    model_type: str = "lstm",
    epochs: int = 100,
    batch_size: int = 64,
    seq_len: int = 16,
    hidden_size: int = 128,
    learning_rate: float = 0.001,
    patience: int = 15,
    checkpoint_dir: str = "ai_engine/checkpoints",
    quick_test: bool = False,
):
    """Full training pipeline."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[TRAIN] Device: {device}")
    print(f"[TRAIN] Model: {model_type}, Epochs: {epochs}, Batch: {batch_size}, Seq: {seq_len}")

    # Prepare data
    print("[TRAIN] Preparing data...")
    datasets, norm_params = prepare_data(csv_path, seq_len=seq_len)

    if datasets["train"] is None:
        print("[TRAIN] ERROR: No training data!")
        return

    train_loader = DataLoader(datasets["train"], batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(datasets["val"], batch_size=batch_size, shuffle=False) if datasets["val"] else None
    test_loader = DataLoader(datasets["test"], batch_size=batch_size, shuffle=False) if datasets["test"] else None

    print(f"[TRAIN] Train: {len(datasets['train'])} samples, "
          f"Val: {len(datasets['val']) if datasets['val'] else 0}, "
          f"Test: {len(datasets['test']) if datasets['test'] else 0}")

    # Create model
    input_size = len(FEATURE_COLUMNS)
    if model_type == "transformer":
        model = TrafficTransformer(input_size=input_size, d_model=hidden_size).to(device)
    else:
        model = TrafficLSTM(input_size=input_size, hidden_size=hidden_size).to(device)

    print(f"[TRAIN] Parameters: {count_parameters(model):,}")

    # Loss, optimizer, scheduler
    criterion = MultiTaskLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=5, factor=0.5)

    # Training loop
    best_val_loss = float("inf")
    patience_counter = 0
    history = {"train": [], "val": []}
    checkpoint_path = Path(checkpoint_dir)
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    if quick_test:
        epochs = min(epochs, 10)
        print(f"[TRAIN] Quick test mode: {epochs} epochs")

    start_time = time.time()

    for epoch in range(1, epochs + 1):
        train_losses = train_epoch(model, train_loader, optimizer, criterion, device)
        history["train"].append(train_losses)

        log = f"  Epoch {epoch:3d}/{epochs} | Train Loss: {train_losses['total']:.4f}"

        if val_loader:
            val_losses = evaluate(model, val_loader, criterion, device)
            history["val"].append(val_losses)
            scheduler.step(val_losses["total"])

            log += f" | Val Loss: {val_losses['total']:.4f}"
            log += f" | Acc: {val_losses.get('congestion_accuracy', 0):.3f}"
            log += f" | MAE: {val_losses.get('volume_mae', 0):.1f}"

            # Early stopping
            if val_losses["total"] < best_val_loss:
                best_val_loss = val_losses["total"]
                patience_counter = 0
                # Save best model
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_loss": best_val_loss,
                    "model_type": model_type,
                    "input_size": input_size,
                    "hidden_size": hidden_size,
                    "norm_params": norm_params,
                }, checkpoint_path / "best_model.pt")
                log += " [BEST]"
            else:
                patience_counter += 1
                if patience_counter >= patience:
                    print(log)
                    print(f"[TRAIN] Early stopping at epoch {epoch}")
                    break
        else:
            # No validation, save every 10 epochs
            if epoch % 10 == 0:
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "model_type": model_type,
                    "input_size": input_size,
                    "hidden_size": hidden_size,
                    "norm_params": norm_params,
                }, checkpoint_path / "best_model.pt")

        if epoch % 5 == 0 or epoch == 1:
            print(log)

    elapsed = time.time() - start_time
    print(f"\n[TRAIN] Training complete in {elapsed:.1f}s")

    # Test evaluation
    if test_loader:
        print("\n[TRAIN] --- Test Results ---")
        test_losses = evaluate(model, test_loader, criterion, device)
        for k, v in test_losses.items():
            print(f"  {k}: {v:.4f}")

    # Save training history
    with open(checkpoint_path / "training_history.json", "w") as f:
        # Convert numpy types for JSON
        def convert(o):
            if isinstance(o, (np.floating, float)):
                return float(o)
            if isinstance(o, (np.integer, int)):
                return int(o)
            return o

        json_history = {
            "train": [{k: convert(v) for k, v in epoch_losses.items()} for epoch_losses in history["train"]],
            "val": [{k: convert(v) for k, v in epoch_losses.items()} for epoch_losses in history["val"]],
        }
        json.dump(json_history, f, indent=2)

    # Save normalization params
    with open(checkpoint_path / "norm_params.json", "w") as f:
        json.dump(norm_params, f, indent=2)

    print(f"[TRAIN] Checkpoint saved to {checkpoint_path}")
    return model, history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Traffic Prediction Model")
    parser.add_argument("--csv", default="traffic_simulation.csv")
    parser.add_argument("--model", default="lstm", choices=["lstm", "transformer"])
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--seq-len", type=int, default=16)
    parser.add_argument("--hidden-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--patience", type=int, default=15)
    parser.add_argument("--quick-test", action="store_true")
    args = parser.parse_args()

    train(
        csv_path=args.csv,
        model_type=args.model,
        epochs=args.epochs,
        batch_size=args.batch_size,
        seq_len=args.seq_len,
        hidden_size=args.hidden_size,
        learning_rate=args.lr,
        patience=args.patience,
        quick_test=args.quick_test,
    )
