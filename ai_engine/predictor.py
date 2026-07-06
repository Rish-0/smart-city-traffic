"""
Traffic Predictor — Real-time Prediction & Signal Optimisation Interface
Loads trained model, accepts traffic state, returns predictions + signal recommendations.
Includes emergency vehicle priority override logic.
"""

import json
import sys
import numpy as np
import torch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_engine.model import TrafficLSTM, TrafficTransformer

CONGESTION_LABELS = ["Low", "Moderate", "High", "Critical"]
LOS_LABELS = ["A", "B", "C", "D", "E", "F"]

CHECKPOINT_DIR = Path(__file__).parent / "checkpoints"


class TrafficPredictor:
    """
    Real-time traffic prediction and signal optimisation engine.
    """

    def __init__(self, checkpoint_path: str = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.norm_params = None
        self.model_loaded = False

        if checkpoint_path is None:
            checkpoint_path = CHECKPOINT_DIR / "best_model.pt"

        self._load_model(checkpoint_path)

    def _load_model(self, checkpoint_path):
        """Load trained model from checkpoint."""
        cp = Path(checkpoint_path)
        if not cp.exists():
            print(f"[PREDICTOR] No checkpoint found at {cp}, using rule-based fallback")
            return

        checkpoint = torch.load(cp, map_location=self.device, weights_only=False)
        model_type = checkpoint.get("model_type", "lstm")
        input_size = checkpoint.get("input_size", 12)
        hidden_size = checkpoint.get("hidden_size", 128)

        if model_type == "transformer":
            self.model = TrafficTransformer(input_size=input_size, d_model=hidden_size)
        else:
            self.model = TrafficLSTM(input_size=input_size, hidden_size=hidden_size)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()
        self.norm_params = checkpoint.get("norm_params", None)
        self.model_loaded = True
        print(f"[PREDICTOR] Loaded {model_type} model (epoch {checkpoint.get('epoch', '?')})")

    def normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize input features using saved normalization params."""
        if self.norm_params is None:
            return features
        mean = np.array(self.norm_params["feature_mean"])
        std = np.array(self.norm_params["feature_std"])
        return (features - mean) / std

    def predict(self, state_sequence: np.ndarray) -> dict:
        """
        Make predictions from a sequence of traffic states.

        Args:
            state_sequence: (seq_len, num_features) numpy array

        Returns:
            dict with predictions and recommendations
        """
        if not self.model_loaded:
            return self._rule_based_prediction(state_sequence[-1] if len(state_sequence.shape) > 1 else state_sequence)

        # Normalize and convert to tensor
        features_norm = self.normalize_features(state_sequence)
        x = torch.FloatTensor(features_norm).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(x)

        # Extract predictions
        volume = float(outputs["volume"][0])
        congestion_probs = torch.softmax(outputs["congestion_logits"][0], dim=0).cpu().numpy()
        congestion_idx = int(congestion_probs.argmax())
        congestion = CONGESTION_LABELS[congestion_idx]
        speed = float(outputs["speed"][0])
        green_time = float(outputs["green_time"][0])
        wait_time = float(outputs["wait_time"][0])

        # Confidence score
        confidence = float(congestion_probs[congestion_idx])

        return {
            "predicted_volume": round(max(0, volume), 0),
            "predicted_congestion": congestion,
            "congestion_probabilities": {
                label: round(float(p), 4) for label, p in zip(CONGESTION_LABELS, congestion_probs)
            },
            "predicted_speed_kmh": round(max(5, speed), 2),
            "recommended_green_sec": round(max(20, min(80, green_time)), 0),
            "predicted_wait_time_min": round(max(0, wait_time), 2),
            "confidence": round(confidence, 3),
            "model_based": True,
        }

    def _rule_based_prediction(self, current_state: np.ndarray) -> dict:
        """Fallback rule-based prediction when no model is available."""
        volume = current_state[0] if len(current_state) > 0 else 500
        queue = current_state[6] if len(current_state) > 6 else 5
        speed = current_state[8] if len(current_state) > 8 else 40

        if volume > 1500:
            congestion = "Critical"
            green = 65
        elif volume > 1000:
            congestion = "High"
            green = 55
        elif volume > 600:
            congestion = "Moderate"
            green = 45
        else:
            congestion = "Low"
            green = 30

        return {
            "predicted_volume": round(volume * 1.05, 0),
            "predicted_congestion": congestion,
            "congestion_probabilities": {c: 0.25 for c in CONGESTION_LABELS},
            "predicted_speed_kmh": round(max(5, speed), 2),
            "recommended_green_sec": green,
            "predicted_wait_time_min": round(max(0, queue * 0.4), 2),
            "confidence": 0.5,
            "model_based": False,
        }

    def optimize_signal_timing(
        self,
        prediction: dict,
        has_emergency: bool = False,
        neighbor_congestion: list = None,
    ) -> dict:
        """
        Compute optimal signal timing based on prediction.
        Applies Webster's formula adjustments and emergency priority.
        """
        base_green = prediction["recommended_green_sec"]
        congestion = prediction["predicted_congestion"]
        volume = prediction["predicted_volume"]

        # Webster's delay optimization (simplified)
        # Optimal cycle length: C_opt = (1.5 * L + 5) / (1 - Y)
        # where L = total lost time, Y = sum of critical flow ratios
        saturation_flow = 1800  # vehicles per hour of green
        Y = min(0.95, volume / saturation_flow)
        L = 8  # lost time per cycle (start-up + clearance)
        if Y < 0.95:
            C_opt = (1.5 * L + 5) / (1 - Y)
        else:
            C_opt = 120  # Max cycle length

        C_opt = max(60, min(120, C_opt))
        optimal_green = max(20, min(80, C_opt * Y))

        # Blend model recommendation with Webster's
        final_green = round(0.6 * base_green + 0.4 * optimal_green)

        # Neighbor coordination
        if neighbor_congestion:
            avg_neighbor = np.mean([
                {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}.get(c, 1)
                for c in neighbor_congestion
            ])
            if avg_neighbor > 2:
                final_green = min(final_green + 5, 80)

        # Emergency vehicle priority override
        emergency_override = False
        if has_emergency:
            emergency_override = True
            final_green = min(final_green + 20, 85)
            # Clear conflicting phases immediately

        yellow = 3
        red = max(10, int(C_opt - final_green - yellow))

        # Generate reasoning
        reasoning = self._generate_reasoning(
            prediction, final_green, congestion, has_emergency, neighbor_congestion
        )

        return {
            "green_sec": int(final_green),
            "yellow_sec": yellow,
            "red_sec": red,
            "cycle_length_sec": int(final_green + yellow + red),
            "emergency_override": emergency_override,
            "reasoning": reasoning,
            "webster_optimal_cycle": round(C_opt, 1),
            "improvement_estimate": self._estimate_improvement(prediction, final_green),
        }

    def _generate_reasoning(self, prediction, green, congestion, emergency, neighbors):
        """Generate natural language reasoning for the signal timing decision."""
        parts = []

        if emergency:
            parts.append("EMERGENCY PRIORITY: Extended green phase to allow emergency vehicle passage.")

        if congestion == "Critical":
            parts.append(f"Critical congestion detected (volume: {prediction['predicted_volume']:.0f}). "
                        f"Maximum green time ({green}s) allocated to clear queue.")
        elif congestion == "High":
            parts.append(f"High congestion predicted. Green time set to {green}s "
                        f"(above standard {45}s) to improve throughput.")
        elif congestion == "Moderate":
            parts.append(f"Moderate traffic flow. Balanced timing at {green}s green.")
        else:
            parts.append(f"Low traffic volume. Reduced green time ({green}s) to minimize "
                        f"unnecessary wait on cross-streets.")

        if neighbors:
            high_neighbors = sum(1 for n in neighbors if n in ["High", "Critical"])
            if high_neighbors > 0:
                parts.append(f"Coordination: {high_neighbors} neighboring intersections "
                            f"show high congestion; timing adjusted for corridor flow.")

        parts.append(f"Predicted wait time: {prediction['predicted_wait_time_min']:.1f} min | "
                    f"Speed: {prediction['predicted_speed_kmh']:.0f} km/h | "
                    f"Confidence: {prediction['confidence']:.0%}")

        return " ".join(parts)

    def _estimate_improvement(self, prediction, optimized_green) -> dict:
        """Estimate performance improvement over baseline."""
        # Baseline: fixed 45s green
        baseline_green = 45
        baseline_capacity = 1800 * (baseline_green / 90)
        optimized_capacity = 1800 * (optimized_green / (optimized_green + 3 + max(42, 90 - optimized_green - 3)))

        volume = max(1, prediction["predicted_volume"])

        baseline_util = min(volume / baseline_capacity, 1.0)
        optimized_util = min(volume / optimized_capacity, 1.0)

        # Wait time improvement
        baseline_wait = max(0, (45 / 2) * (1 / (1 - baseline_util + 0.01)))
        optimized_wait = max(0, ((90 - optimized_green) / 2) * (1 / (1 - optimized_util + 0.01)))

        wait_improvement = round(max(0, (baseline_wait - optimized_wait) / max(baseline_wait, 0.01) * 100), 1)
        throughput_improvement = round(max(0, (optimized_capacity - baseline_capacity) / max(baseline_capacity, 1) * 100), 1)

        return {
            "wait_time_reduction_pct": wait_improvement,
            "throughput_increase_pct": throughput_improvement,
            "baseline_wait_sec": round(baseline_wait, 1),
            "optimized_wait_sec": round(optimized_wait, 1),
        }

    def predict_sample(self) -> dict:
        """Quick test with random data."""
        sample = np.random.rand(16, 12).astype(np.float32)
        sample[:, 0] *= 2000  # volume
        sample[:, 8] *= 50    # speed
        prediction = self.predict(sample)
        timing = self.optimize_signal_timing(prediction, has_emergency=False)
        return {"prediction": prediction, "timing": timing}


# ────────────────────────────────────────────
# BATCH PREDICTION FOR SIMULATION DATA
# ────────────────────────────────────────────
def run_ai_optimization(csv_path: str = "traffic_simulation.csv", seq_len: int = 16) -> dict:
    """
    Run AI optimization on the full simulation dataset.
    Returns comparison metrics: AI vs Baseline.
    """
    import pandas as pd

    predictor = TrafficPredictor()
    df = pd.read_csv(csv_path)

    feature_cols = [
        "Traffic_Volume", "Cars", "Motorcycles", "Buses", "Trucks",
        "Emergency_Vehicles", "Queue_Length", "Average_Wait_Time_min",
        "Average_Speed_kmh", "Throughput", "V_C_Ratio", "CO2_Emissions_g",
    ]

    intersections = sorted(df["Intersection_ID"].unique())
    ai_results = []

    for junction in intersections:
        jdf = df[df["Intersection_ID"] == junction].sort_values("Timestamp").reset_index(drop=True)
        features = jdf[feature_cols].values.astype(np.float32)

        for i in range(seq_len, len(jdf)):
            seq = features[i - seq_len:i]
            row = jdf.iloc[i]

            prediction = predictor.predict(seq)
            has_emergency = row["Emergency_Vehicles"] > 0
            timing = predictor.optimize_signal_timing(prediction, has_emergency=has_emergency)

            ai_results.append({
                "Timestamp": row["Timestamp"],
                "Intersection_ID": junction,
                "Zone": row["Zone"],
                "Baseline_Volume": row["Traffic_Volume"],
                "AI_Predicted_Volume": prediction["predicted_volume"],
                "Baseline_Wait": row["Average_Wait_Time_min"],
                "AI_Wait_Time": prediction["predicted_wait_time_min"],
                "Baseline_Speed": row["Average_Speed_kmh"],
                "AI_Speed": prediction["predicted_speed_kmh"],
                "Baseline_Green": row["Green_Signal_sec"],
                "AI_Green": timing["green_sec"],
                "AI_Congestion": prediction["predicted_congestion"],
                "Baseline_Congestion": row["Congestion_Level"],
                "AI_Confidence": prediction["confidence"],
                "Wait_Improvement_pct": timing["improvement_estimate"]["wait_time_reduction_pct"],
                "Throughput_Improvement_pct": timing["improvement_estimate"]["throughput_increase_pct"],
                "AI_Reasoning": timing["reasoning"],
                "Emergency_Override": timing["emergency_override"],
            })

    ai_df = pd.DataFrame(ai_results)

    # Compute summary
    summary = {
        "total_records": len(ai_df),
        "avg_wait_reduction_pct": round(ai_df["Wait_Improvement_pct"].mean(), 1),
        "avg_throughput_increase_pct": round(ai_df["Throughput_Improvement_pct"].mean(), 1),
        "avg_baseline_wait": round(ai_df["Baseline_Wait"].mean(), 2),
        "avg_ai_wait": round(ai_df["AI_Wait_Time"].mean(), 2),
        "avg_confidence": round(ai_df["AI_Confidence"].mean(), 3),
        "emergency_overrides": int(ai_df["Emergency_Override"].sum()),
        "by_zone": ai_df.groupby("Zone").agg({
            "Wait_Improvement_pct": "mean",
            "Throughput_Improvement_pct": "mean",
            "AI_Confidence": "mean",
        }).round(2).to_dict(),
    }

    # Save
    ai_df.to_csv("ai_optimization_results.csv", index=False)
    print(f"\n[AI] Saved ai_optimization_results.csv ({ai_df.shape})")
    print(f"[AI] Average wait time reduction: {summary['avg_wait_reduction_pct']}%")
    print(f"[AI] Average throughput increase: {summary['avg_throughput_increase_pct']}%")

    return {"results_df": ai_df, "summary": summary}


if __name__ == "__main__":
    print("=== Traffic Predictor ===")
    predictor = TrafficPredictor()

    # Quick test
    result = predictor.predict_sample()
    print("\nSample prediction:")
    for k, v in result["prediction"].items():
        print(f"  {k}: {v}")
    print("\nSignal timing:")
    for k, v in result["timing"].items():
        if k != "reasoning":
            print(f"  {k}: {v}")
    print(f"  reasoning: {result['timing']['reasoning'][:150]}...")

    print("\n\n=== Running Full AI Optimization ===")
    run_ai_optimization()
