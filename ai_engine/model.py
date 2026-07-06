"""
LSTM-based Traffic Prediction Model
Predicts future traffic volume, congestion level, and optimal signal timing
based on historical multi-intersection state sequences.
"""

import torch
import torch.nn as nn
import numpy as np


class TrafficLSTM(nn.Module):
    """
    Multi-output LSTM for traffic prediction.
    
    Inputs:  (batch, seq_len, num_features)
    Outputs: volume prediction, congestion class, optimal green time
    """

    def __init__(
        self,
        input_size: int = 12,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        num_congestion_classes: int = 4,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM backbone
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )

        # Batch normalization
        self.bn = nn.BatchNorm1d(hidden_size)

        # Prediction heads
        self.volume_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

        self.congestion_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_congestion_classes),
        )

        self.speed_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

        self.green_time_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
            nn.Sigmoid(),  # Output 0-1, scale to 20-80 sec
        )

        self.wait_time_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
            nn.ReLU(),  # Wait time is non-negative
        )

    def forward(self, x):
        """
        Args:
            x: (batch, seq_len, input_size) tensor
        Returns:
            dict of predictions
        """
        # LSTM forward pass
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Use the last hidden state
        last_hidden = lstm_out[:, -1, :]  # (batch, hidden_size)
        last_hidden = self.bn(last_hidden)

        # Multi-head predictions
        volume_pred = self.volume_head(last_hidden).squeeze(-1)
        congestion_logits = self.congestion_head(last_hidden)
        speed_pred = self.speed_head(last_hidden).squeeze(-1)
        green_time_raw = self.green_time_head(last_hidden).squeeze(-1)
        green_time_pred = green_time_raw * 60 + 20  # Scale to 20-80 sec
        wait_time_pred = self.wait_time_head(last_hidden).squeeze(-1)

        return {
            "volume": volume_pred,
            "congestion_logits": congestion_logits,
            "speed": speed_pred,
            "green_time": green_time_pred,
            "wait_time": wait_time_pred,
        }


class TrafficTransformer(nn.Module):
    """
    Transformer-based alternative for traffic prediction.
    Better at capturing long-range temporal dependencies.
    """

    def __init__(
        self,
        input_size: int = 12,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 2,
        dropout: float = 0.1,
        num_congestion_classes: int = 4,
    ):
        super().__init__()
        self.input_proj = nn.Linear(input_size, d_model)
        self.pos_encoding = nn.Parameter(torch.randn(1, 100, d_model) * 0.1)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dropout=dropout,
            dim_feedforward=d_model * 4, batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.bn = nn.BatchNorm1d(d_model)

        # Same prediction heads as LSTM
        self.volume_head = nn.Sequential(nn.Linear(d_model, 64), nn.ReLU(), nn.Linear(64, 1))
        self.congestion_head = nn.Sequential(nn.Linear(d_model, 64), nn.ReLU(), nn.Linear(64, num_congestion_classes))
        self.speed_head = nn.Sequential(nn.Linear(d_model, 64), nn.ReLU(), nn.Linear(64, 1))
        self.green_time_head = nn.Sequential(nn.Linear(d_model, 64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid())
        self.wait_time_head = nn.Sequential(nn.Linear(d_model, 64), nn.ReLU(), nn.Linear(64, 1), nn.ReLU())

    def forward(self, x):
        batch, seq_len, _ = x.shape
        x = self.input_proj(x)
        x = x + self.pos_encoding[:, :seq_len, :]
        x = self.transformer(x)
        last = self.bn(x[:, -1, :])

        return {
            "volume": self.volume_head(last).squeeze(-1),
            "congestion_logits": self.congestion_head(last),
            "speed": self.speed_head(last).squeeze(-1),
            "green_time": self.green_time_head(last).squeeze(-1) * 60 + 20,
            "wait_time": self.wait_time_head(last).squeeze(-1),
        }


def count_parameters(model: nn.Module) -> int:
    """Count trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Quick test
    batch_size, seq_len, input_size = 32, 16, 12

    print("=== Traffic LSTM ===")
    model = TrafficLSTM(input_size=input_size)
    x = torch.randn(batch_size, seq_len, input_size)
    out = model(x)
    print(f"Parameters: {count_parameters(model):,}")
    for k, v in out.items():
        print(f"  {k}: {v.shape}")

    print("\n=== Traffic Transformer ===")
    model_t = TrafficTransformer(input_size=input_size)
    out_t = model_t(x)
    print(f"Parameters: {count_parameters(model_t):,}")
    for k, v in out_t.items():
        print(f"  {k}: {v.shape}")
