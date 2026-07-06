"""
Data Export Module
Generates Tableau-optimised exports and comparison datasets.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def generate_heatmap_data(df: pd.DataFrame) -> pd.DataFrame:
    """Generate congestion heatmap: intersection x time matrix."""
    congestion_map = {"Low": 1, "Moderate": 2, "High": 3, "Critical": 4}
    df_heat = df.copy()
    df_heat["Congestion_Numeric"] = df_heat["Congestion_Level"].map(congestion_map)
    pivot = df_heat.pivot_table(
        values="Congestion_Numeric",
        index="Intersection_ID",
        columns="Timestamp",
        aggfunc="mean"
    )
    return pivot


def generate_gantt_data(df: pd.DataFrame) -> pd.DataFrame:
    """Generate signal state timeline data for Gantt chart."""
    records = []
    for _, row in df.iterrows():
        ts = pd.to_datetime(row["Timestamp"])
        green_end = ts + pd.Timedelta(seconds=row["Green_Signal_sec"])
        yellow_end = green_end + pd.Timedelta(seconds=row["Yellow_Signal_sec"])
        red_end = yellow_end + pd.Timedelta(seconds=row["Red_Signal_sec"])

        records.append({
            "Intersection_ID": row["Intersection_ID"],
            "Zone": row["Zone"],
            "Phase": "Green",
            "Start": ts,
            "End": green_end,
            "Duration_sec": row["Green_Signal_sec"],
        })
        records.append({
            "Intersection_ID": row["Intersection_ID"],
            "Zone": row["Zone"],
            "Phase": "Yellow",
            "Start": green_end,
            "End": yellow_end,
            "Duration_sec": row["Yellow_Signal_sec"],
        })
        records.append({
            "Intersection_ID": row["Intersection_ID"],
            "Zone": row["Zone"],
            "Phase": "Red",
            "Start": yellow_end,
            "End": red_end,
            "Duration_sec": row["Red_Signal_sec"],
        })
    return pd.DataFrame(records)


def generate_zone_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate metrics by zone and time period."""
    df_agg = df.copy()
    df_agg["Time_Period"] = df_agg["Hour"].apply(
        lambda h: "Night" if h < 6 else
                  "Morning Rush" if h < 10 else
                  "Midday" if h < 16 else
                  "Evening Rush" if h < 20 else
                  "Evening"
    )

    agg = df_agg.groupby(["Zone", "Time_Period", "Day"]).agg({
        "Traffic_Volume": "sum",
        "Average_Wait_Time_min": "mean",
        "Average_Speed_kmh": "mean",
        "Throughput": "sum",
        "Queue_Length": "mean",
        "CO2_Emissions_g": "sum",
        "Emergency_Vehicles": "sum",
    }).reset_index()
    agg.columns = [
        "Zone", "Time_Period", "Day",
        "Total_Volume", "Avg_Wait_Time", "Avg_Speed",
        "Total_Throughput", "Avg_Queue", "Total_CO2",
        "Emergency_Count"
    ]
    return agg.round(2)


def generate_comparison_summary(sim_df: pd.DataFrame, ai_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Generate AI vs Baseline comparison summary.
    If ai_df not provided, uses the baseline columns in sim_df.
    """
    if ai_df is not None:
        # Merge baseline and AI results
        baseline = sim_df.groupby("Zone").agg({
            "Average_Wait_Time_min": "mean",
            "Throughput": "mean",
            "Average_Speed_kmh": "mean",
            "CO2_Emissions_g": "sum",
            "Queue_Length": "mean",
        }).reset_index()
        baseline.columns = ["Zone", "Baseline_Wait", "Baseline_Throughput",
                           "Baseline_Speed", "Baseline_CO2", "Baseline_Queue"]

        ai = ai_df.groupby("Zone").agg({
            "AI_Wait_Time": "mean",
            "AI_Throughput": "mean",
            "AI_Speed": "mean",
            "AI_CO2": "sum",
            "AI_Queue": "mean",
        }).reset_index()
        ai.columns = ["Zone", "AI_Wait", "AI_Throughput",
                      "AI_Speed", "AI_CO2", "AI_Queue"]

        comparison = baseline.merge(ai, on="Zone")
    else:
        # Just baseline summary
        comparison = sim_df.groupby("Zone").agg({
            "Average_Wait_Time_min": "mean",
            "Throughput": "mean",
            "Average_Speed_kmh": "mean",
            "CO2_Emissions_g": "sum",
            "Queue_Length": "mean",
        }).reset_index()
        comparison.columns = ["Zone", "Baseline_Wait", "Baseline_Throughput",
                             "Baseline_Speed", "Baseline_CO2", "Baseline_Queue"]

    return comparison.round(2)


def export_all(df: pd.DataFrame, output_dir: str = "exports"):
    """Generate and save all Tableau-ready exports."""
    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    print(f"[EXPORT] Generating exports to {out}/")

    # 1. Zone aggregation
    zone_agg = generate_zone_aggregation(df)
    zone_agg.to_csv(out / "zone_aggregation.csv", index=False)
    print(f"  -> zone_aggregation.csv ({zone_agg.shape})")

    # 2. Hourly summary
    hourly = df.groupby(["Day", "Hour"]).agg({
        "Traffic_Volume": "sum",
        "Average_Wait_Time_min": "mean",
        "Average_Speed_kmh": "mean",
        "Throughput": "sum",
        "CO2_Emissions_g": "sum",
        "Queue_Length": "mean",
    }).reset_index().round(2)
    hourly.to_csv(out / "hourly_summary.csv", index=False)
    print(f"  -> hourly_summary.csv ({hourly.shape})")

    # 3. Intersection performance
    intersection_perf = df.groupby("Intersection_ID").agg({
        "Traffic_Volume": "mean",
        "Average_Wait_Time_min": "mean",
        "Average_Speed_kmh": "mean",
        "Throughput": "mean",
        "Queue_Length": "mean",
        "CO2_Emissions_g": "sum",
        "Congestion_Level": lambda x: x.value_counts().index[0],  # mode
        "Zone": "first",
    }).reset_index().round(2)
    intersection_perf.to_csv(out / "intersection_performance.csv", index=False)
    print(f"  -> intersection_performance.csv ({intersection_perf.shape})")

    # 4. Comparison summary
    comparison = generate_comparison_summary(df)
    comparison.to_csv(out / "comparison_summary.csv", index=False)
    print(f"  -> comparison_summary.csv ({comparison.shape})")

    # 5. Weather impact analysis
    weather_impact = df.groupby("Weather").agg({
        "Average_Wait_Time_min": "mean",
        "Average_Speed_kmh": "mean",
        "Throughput": "mean",
        "CO2_Emissions_g": "mean",
    }).reset_index().round(2)
    weather_impact.to_csv(out / "weather_impact.csv", index=False)
    print(f"  -> weather_impact.csv ({weather_impact.shape})")

    # 6. Incident analysis
    incident_impact = df.groupby("Incident").agg({
        "Average_Wait_Time_min": "mean",
        "Average_Speed_kmh": "mean",
        "Throughput": "mean",
        "Traffic_Volume": "count",
    }).reset_index().round(2)
    incident_impact.columns = ["Incident", "Avg_Wait", "Avg_Speed", "Avg_Throughput", "Count"]
    incident_impact.to_csv(out / "incident_analysis.csv", index=False)
    print(f"  -> incident_analysis.csv ({incident_impact.shape})")

    print("[EXPORT] All exports complete!")
    return out


if __name__ == "__main__":
    df = pd.read_csv("traffic_simulation.csv")
    export_all(df)
