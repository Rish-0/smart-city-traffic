"""
Baseline Traffic Controllers
Provides rule-based controllers for comparison against AI-optimised timing.
"""

import pandas as pd
import numpy as np


class FixedTimingController:
    """Fixed-cycle signal timing - same timing regardless of conditions."""

    def __init__(self, green=45, yellow=3, red=42):
        self.green = green
        self.yellow = yellow
        self.red = red
        self.name = "Fixed Timing"

    def get_timing(self, state: dict) -> dict:
        return {
            "green": self.green,
            "yellow": self.yellow,
            "red": self.red,
            "cycle_length": self.green + self.yellow + self.red,
            "controller": self.name,
        }


class TimeOfDayController:
    """Pre-programmed timing plans based on time of day."""

    def __init__(self):
        self.name = "Time-of-Day"
        self.plans = {
            "morning_peak":  {"green": 55, "yellow": 3, "red": 32, "hours": range(7, 10)},
            "midday":        {"green": 40, "yellow": 3, "red": 47, "hours": range(10, 16)},
            "evening_peak":  {"green": 60, "yellow": 3, "red": 27, "hours": range(16, 20)},
            "night":         {"green": 30, "yellow": 3, "red": 57, "hours": range(20, 24)},
            "early_morning": {"green": 25, "yellow": 3, "red": 62, "hours": range(0, 7)},
        }

    def get_timing(self, state: dict) -> dict:
        hour = state.get("hour", 12)
        for plan_name, plan in self.plans.items():
            if hour in plan["hours"]:
                return {
                    "green": plan["green"],
                    "yellow": plan["yellow"],
                    "red": plan["red"],
                    "cycle_length": plan["green"] + plan["yellow"] + plan["red"],
                    "controller": f"{self.name} ({plan_name})",
                }
        return {"green": 40, "yellow": 3, "red": 47, "cycle_length": 90, "controller": self.name}


class ActuatedController:
    """Volume-threshold-based actuated controller."""

    def __init__(self):
        self.name = "Actuated"

    def get_timing(self, state: dict) -> dict:
        volume = state.get("traffic_volume", 500)
        queue = state.get("queue_length", 0)
        has_emergency = state.get("emergency_vehicles", 0) > 0

        # Base timing from volume
        if volume > 1500:
            green = 65
        elif volume > 1000:
            green = 50
        elif volume > 600:
            green = 40
        else:
            green = 30

        # Queue adjustment
        if queue > 30:
            green = min(green + 10, 75)
        elif queue > 15:
            green = min(green + 5, 70)

        # Emergency override
        if has_emergency:
            green = min(green + 15, 80)

        red = max(90 - green - 3, 10)

        return {
            "green": green,
            "yellow": 3,
            "red": red,
            "cycle_length": green + 3 + red,
            "controller": self.name,
        }


def run_baseline_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all baseline controllers on the simulation data and compute metrics.
    Returns a DataFrame with results from each controller.
    """
    controllers = {
        "Fixed": FixedTimingController(),
        "TimeOfDay": TimeOfDayController(),
        "Actuated": ActuatedController(),
    }

    results = []

    for _, row in df.iterrows():
        state = {
            "hour": row["Hour"],
            "traffic_volume": row["Traffic_Volume"],
            "queue_length": row["Queue_Length"],
            "emergency_vehicles": row["Emergency_Vehicles"],
            "congestion_level": row["Congestion_Level"],
        }

        for ctrl_name, ctrl in controllers.items():
            timing = ctrl.get_timing(state)

            # Estimate performance with this timing
            green_ratio = timing["green"] / timing["cycle_length"]
            effective_capacity = int(1800 * green_ratio)
            est_throughput = min(row["Traffic_Volume"], effective_capacity)

            # Wait time estimate (simplified queueing model)
            utilization = min(row["Traffic_Volume"] / max(effective_capacity, 1), 0.99)
            est_wait = (timing["red"] / 2) * (1 / (1 - utilization + 0.01))
            est_wait = round(min(est_wait, 60), 2)

            # Speed estimate
            congestion_penalty = max(0, (utilization - 0.5) * 40)
            est_speed = round(max(5, 50 - congestion_penalty), 2)

            results.append({
                "Timestamp": row["Timestamp"],
                "Intersection_ID": row["Intersection_ID"],
                "Zone": row["Zone"],
                "Controller": ctrl_name,
                "Traffic_Volume": row["Traffic_Volume"],
                "Green_sec": timing["green"],
                "Red_sec": timing["red"],
                "Cycle_sec": timing["cycle_length"],
                "Est_Throughput": est_throughput,
                "Est_Wait_Time_min": est_wait,
                "Est_Speed_kmh": est_speed,
                "Green_Ratio": round(green_ratio, 3),
            })

    return pd.DataFrame(results)


if __name__ == "__main__":
    print("[BASELINE] Loading simulation data...")
    df = pd.read_csv("traffic_simulation.csv")

    print(f"[BASELINE] Running baseline comparison on {len(df)} records...")
    comparison_df = run_baseline_comparison(df)

    # Summary
    print("\n[BASELINE] --- Results by Controller ---")
    summary = comparison_df.groupby("Controller").agg({
        "Est_Throughput": "mean",
        "Est_Wait_Time_min": "mean",
        "Est_Speed_kmh": "mean",
        "Green_Ratio": "mean",
    }).round(2)
    print(summary.to_string())

    # Save
    comparison_df.to_csv("baseline_comparison.csv", index=False)
    print(f"\n[BASELINE] Saved baseline_comparison.csv ({comparison_df.shape})")
