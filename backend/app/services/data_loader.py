"""Data loader service — loads, cleans, and processes both CSV datasets into the database."""

import pandas as pd
from sqlalchemy.orm import Session
from app.models.traffic_data import TrafficData
import os, logging

logger = logging.getLogger(__name__)

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

def get_season(m: int) -> str:
    if m in [12, 1, 2]: return "Winter"
    if m in [3, 4, 5]: return "Spring"
    if m in [6, 7, 8]: return "Summer"
    return "Autumn"

def is_rush(h: int) -> int:
    return 1 if (7 <= h <= 10) or (16 <= h <= 20) else 0

def load_metro_dataset(db: Session, path: str) -> int:
    if not os.path.exists(path):
        logger.error(f"Metro dataset not found: {path}"); return 0
    df = pd.read_csv(path)
    df["date_time"] = pd.to_datetime(df["date_time"], format="mixed", dayfirst=False)
    df = df.drop_duplicates(subset=["date_time"], keep="first")
    df["temp_celsius"] = (df["temp"] - 273.15).round(1)
    df["holiday"] = df["holiday"].replace("None", None)
    df["hour"] = df["date_time"].dt.hour
    df["day"] = df["date_time"].dt.day
    df["weekday"] = df["date_time"].dt.weekday
    df["weekday_name"] = df["weekday"].map(lambda x: WEEKDAY_NAMES[x])
    df["month"] = df["date_time"].dt.month
    df["month_name"] = df["month"].map(lambda x: MONTH_NAMES[x - 1])
    df["year"] = df["date_time"].dt.year
    df["season"] = df["month"].map(get_season)
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    df["is_rush_hour"] = df["hour"].map(is_rush)
    p33, p66 = df["traffic_volume"].quantile(0.33), df["traffic_volume"].quantile(0.66)
    df["congestion_level"] = df["traffic_volume"].map(lambda v: "Low" if v < p33 else ("Moderate" if v < p66 else "High"))

    count = 0
    for i in range(0, len(df), 1000):
        batch = df.iloc[i:i + 1000]
        records = []
        for _, r in batch.iterrows():
            records.append(TrafficData(
                timestamp=r["date_time"], traffic_volume=int(r["traffic_volume"]),
                temp_celsius=r["temp_celsius"], rain_1h=float(r["rain_1h"]),
                snow_1h=float(r["snow_1h"]), clouds_all=int(r["clouds_all"]),
                weather_main=r["weather_main"], weather_description=r["weather_description"],
                holiday=r["holiday"] if pd.notna(r["holiday"]) else None,
                hour=int(r["hour"]), day=int(r["day"]), weekday=int(r["weekday"]),
                weekday_name=r["weekday_name"], month=int(r["month"]),
                month_name=r["month_name"], year=int(r["year"]), season=r["season"],
                is_weekend=int(r["is_weekend"]), is_rush_hour=int(r["is_rush_hour"]),
                congestion_level=r["congestion_level"], source="metro",
            ))
        db.add_all(records); db.commit(); count += len(records)
    logger.info(f"Loaded {count} Metro records"); return count

def load_simulation_dataset(db: Session, path: str) -> int:
    if not os.path.exists(path):
        logger.error(f"Simulation dataset not found: {path}"); return 0
    df = pd.read_csv(path)
    # Normalize column names — handle both simulation.py and legacy naming
    col_renames = {
        "Average_Wait_Time(min)": "Average_Wait_Time_min",
        "Average_Speed(km/h)": "Average_Speed_kmh",
        "Green_Signal(sec)": "Green_Signal_sec",
        "Red_Signal(sec)": "Red_Signal_sec",
        "AI_Recommendation": "Baseline_Recommendation",
    }
    df.rename(columns={k: v for k, v in col_renames.items() if k in df.columns}, inplace=True)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df["hour"] = df["Timestamp"].dt.hour
    df["day"] = df["Timestamp"].dt.day
    df["weekday"] = df["Timestamp"].dt.weekday
    df["weekday_name"] = df["weekday"].map(lambda x: WEEKDAY_NAMES[x])
    df["month"] = df["Timestamp"].dt.month
    df["month_name"] = df["month"].map(lambda x: MONTH_NAMES[x - 1])
    df["year"] = df["Timestamp"].dt.year
    df["season"] = df["month"].map(get_season)
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    df["is_rush_hour"] = df["hour"].map(is_rush)

    count = 0
    for i in range(0, len(df), 200):
        batch = df.iloc[i:i + 200]
        records = []
        for _, r in batch.iterrows():
            records.append(TrafficData(
                timestamp=r["Timestamp"], intersection_id=r["Intersection_ID"],
                zone=r["Zone"], traffic_volume=int(r["Traffic_Volume"]),
                cars=int(r["Cars"]), motorcycles=int(r["Motorcycles"]),
                buses=int(r["Buses"]), trucks=int(r["Trucks"]),
                emergency_vehicles=int(r["Emergency_Vehicles"]),
                queue_length=int(r["Queue_Length"]),
                avg_wait_time=float(r["Average_Wait_Time_min"]),
                avg_speed=float(r["Average_Speed_kmh"]),
                congestion_level=r["Congestion_Level"],
                green_signal=int(r["Green_Signal_sec"]),
                red_signal=int(r["Red_Signal_sec"]),
                ai_recommendation=r.get("Baseline_Recommendation", "Maintain Current Timing"),
                weather_main=r["Weather"],
                hour=int(r["hour"]), day=int(r["day"]), weekday=int(r["weekday"]),
                weekday_name=r["weekday_name"], month=int(r["month"]),
                month_name=r["month_name"], year=int(r["year"]), season=r["season"],
                is_weekend=int(r["is_weekend"]), is_rush_hour=int(r["is_rush_hour"]),
                source="simulation",
            ))
        db.add_all(records); db.commit(); count += len(records)
    logger.info(f"Loaded {count} Simulation records"); return count

def load_all_data(db: Session, base_dir: str) -> dict:
    existing = db.query(TrafficData).count()
    if existing > 0:
        logger.info(f"Data already loaded ({existing} records). Skipping.")
        return {"metro": 0, "simulation": 0, "status": "skipped", "existing": existing}
    metro_path = os.path.join(base_dir, "Dataset", "Metro_Interstate_Traffic_Volume.csv")
    sim_path = os.path.join(base_dir, "traffic_simulation.csv")
    mc = load_metro_dataset(db, metro_path)
    sc = load_simulation_dataset(db, sim_path)
    return {"metro": mc, "simulation": sc, "status": "loaded", "total": mc + sc}
