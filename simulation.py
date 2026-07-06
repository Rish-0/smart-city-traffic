"""
Enhanced Smart City Traffic Simulator
Simulates a 5x5 grid city with METR-LA network topology, realistic traffic
patterns, weather effects, incidents, queue propagation, and emissions.
Outputs: traffic_simulation.csv (multi-day, 25+ columns)
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from traffic_network import (
    load_metr_la_adjacency, extract_subgraph, build_city_graph,
    get_neighbors, ZONE_MAP, INTERSECTION_ZONE, GRID_POSITIONS,
    NUM_INTERSECTIONS, GRID_SIZE
)

# ────────────────────────────────────────────
# CONFIGURATION
# ────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

SIMULATION_DAYS = 7
TIMESTEPS_PER_HOUR = 4          # 15-minute intervals
START_DATE = datetime(2024, 1, 1)

WEATHER_CONDITIONS = ["Clear", "Rain", "Fog", "Snow"]
WEATHER_PROBS = [0.55, 0.25, 0.12, 0.08]

INCIDENT_TYPES = ["None", "Minor Accident", "Major Accident", "Road Work", "Special Event"]
INCIDENT_PROBS = [0.85, 0.08, 0.03, 0.02, 0.02]

VEHICLE_TYPES = ["Cars", "Motorcycles", "Buses", "Trucks", "Emergency_Vehicles"]

# Emission factors (g CO2 per km per vehicle, rough estimates)
EMISSION_FACTORS = {
    "Cars": 120,
    "Motorcycles": 70,
    "Buses": 800,
    "Trucks": 600,
    "Emergency_Vehicles": 250,
}

# Average trip distance through intersection (km)
AVG_TRIP_DISTANCE = 0.5

# ────────────────────────────────────────────
# TRAFFIC PATTERN PROFILES
# ────────────────────────────────────────────
def get_traffic_multiplier(hour: int, day_of_week: int, zone: str) -> float:
    """
    Realistic time-of-day and day-of-week traffic multiplier.
    Weekends (5,6) have different patterns.
    """
    is_weekend = day_of_week >= 5

    # Base time-of-day profile
    if 7 <= hour <= 9:
        base_mult = 1.8 if not is_weekend else 1.0
    elif 10 <= hour <= 11:
        base_mult = 1.3 if not is_weekend else 1.2
    elif 12 <= hour <= 13:
        base_mult = 1.4  # Lunch rush
    elif 14 <= hour <= 15:
        base_mult = 1.2
    elif 16 <= hour <= 19:
        base_mult = 2.0 if not is_weekend else 1.3
    elif 20 <= hour <= 22:
        base_mult = 0.9
    elif 6 <= hour <= 6:
        base_mult = 0.7
    else:
        base_mult = 0.3  # Night (23-5)

    # Zone-specific adjustments
    zone_factors = {
        "Commercial":  {"peak_boost": 1.3, "off_boost": 0.7},
        "Residential": {"peak_boost": 0.9, "off_boost": 1.2},
        "School":      {"peak_boost": 1.2 if not is_weekend else 0.5, "off_boost": 0.8},
        "Industrial":  {"peak_boost": 1.1, "off_boost": 0.6},
        "Hospital":    {"peak_boost": 1.0, "off_boost": 1.0},  # consistent
    }

    zf = zone_factors.get(zone, {"peak_boost": 1.0, "off_boost": 1.0})
    if base_mult > 1.0:
        return base_mult * zf["peak_boost"]
    else:
        return base_mult * zf["off_boost"]


def get_base_volume(zone: str) -> int:
    """Base traffic volume per 15-minute interval for each zone type."""
    base_ranges = {
        "Commercial":  (800, 1200),
        "Residential": (400, 750),
        "School":      (500, 900),
        "Industrial":  (600, 1000),
        "Hospital":    (450, 800),
    }
    low, high = base_ranges.get(zone, (500, 800))
    return random.randint(low, high)


def get_vehicle_distribution(zone: str, total_volume: int) -> dict:
    """Distribute total volume across vehicle types based on zone."""
    distributions = {
        "Commercial":  {"Cars": 0.65, "Motorcycles": 0.12, "Buses": 0.08, "Trucks": 0.13, "Emergency_Vehicles": 0.02},
        "Residential": {"Cars": 0.70, "Motorcycles": 0.15, "Buses": 0.06, "Trucks": 0.05, "Emergency_Vehicles": 0.04},
        "School":      {"Cars": 0.55, "Motorcycles": 0.10, "Buses": 0.20, "Trucks": 0.05, "Emergency_Vehicles": 0.10},
        "Industrial":  {"Cars": 0.45, "Motorcycles": 0.08, "Buses": 0.07, "Trucks": 0.35, "Emergency_Vehicles": 0.05},
        "Hospital":    {"Cars": 0.55, "Motorcycles": 0.10, "Buses": 0.05, "Trucks": 0.05, "Emergency_Vehicles": 0.25},
    }
    dist = distributions.get(zone, distributions["Commercial"])
    vehicles = {}
    for vtype, ratio in dist.items():
        noise = random.uniform(-0.03, 0.03)
        vehicles[vtype] = max(0, int(total_volume * (ratio + noise)))
    return vehicles


# ────────────────────────────────────────────
# WEATHER & INCIDENT EFFECTS
# ────────────────────────────────────────────
def get_weather(prev_weather: str = None) -> str:
    """Weather with persistence (tends to stay the same within a day)."""
    if prev_weather and random.random() < 0.7:
        return prev_weather
    return np.random.choice(WEATHER_CONDITIONS, p=WEATHER_PROBS)


def weather_effects(weather: str) -> dict:
    """Return speed reduction and wait time increase due to weather."""
    effects = {
        "Clear": {"speed_reduction": 0, "wait_increase": 0, "accident_mult": 1.0},
        "Rain":  {"speed_reduction": 8, "wait_increase": 3, "accident_mult": 1.5},
        "Fog":   {"speed_reduction": 5, "wait_increase": 1.5, "accident_mult": 1.3},
        "Snow":  {"speed_reduction": 15, "wait_increase": 6, "accident_mult": 2.0},
    }
    return effects.get(weather, effects["Clear"])


def generate_incident(weather: str) -> str:
    """Generate random incidents, more likely in bad weather."""
    w_effects = weather_effects(weather)
    adjusted_probs = np.array(INCIDENT_PROBS, dtype=float)
    # Increase accident probability in bad weather
    adjusted_probs[1] *= w_effects["accident_mult"]
    adjusted_probs[2] *= w_effects["accident_mult"]
    adjusted_probs[0] = max(0, 1.0 - sum(adjusted_probs[1:]))
    adjusted_probs /= adjusted_probs.sum()
    return np.random.choice(INCIDENT_TYPES, p=adjusted_probs)


def incident_effects(incident: str) -> dict:
    """Return the effects of an incident on traffic."""
    effects = {
        "None":           {"capacity_reduction": 0.0, "speed_reduction": 0, "wait_increase": 0},
        "Minor Accident": {"capacity_reduction": 0.2, "speed_reduction": 10, "wait_increase": 5},
        "Major Accident": {"capacity_reduction": 0.5, "speed_reduction": 25, "wait_increase": 15},
        "Road Work":      {"capacity_reduction": 0.3, "speed_reduction": 15, "wait_increase": 8},
        "Special Event":  {"capacity_reduction": 0.1, "speed_reduction": 5, "wait_increase": 3},
    }
    return effects.get(incident, effects["None"])


# ────────────────────────────────────────────
# CONGESTION & SIGNAL TIMING
# ────────────────────────────────────────────
def compute_congestion_level(volume: int, capacity: int = 1800) -> str:
    """Compute congestion level based on volume-to-capacity ratio."""
    ratio = volume / max(capacity, 1)
    if ratio < 0.4:
        return "Low"
    elif ratio < 0.7:
        return "Moderate"
    elif ratio < 0.9:
        return "High"
    else:
        return "Critical"


def baseline_signal_timing(congestion: str, has_emergency: bool) -> dict:
    """Rule-based baseline signal timing."""
    timings = {
        "Low":      {"green": 30, "yellow": 3, "red": 57},
        "Moderate": {"green": 45, "yellow": 3, "red": 42},
        "High":     {"green": 55, "yellow": 3, "red": 32},
        "Critical": {"green": 65, "yellow": 3, "red": 22},
    }
    timing = timings.get(congestion, timings["Moderate"]).copy()
    if has_emergency:
        timing["green"] = min(timing["green"] + 15, 80)
        timing["red"] = max(timing["red"] - 15, 10)
    return timing


def compute_emissions(vehicles: dict, avg_speed: float) -> float:
    """
    Estimate CO2 emissions (grams) for the intersection during this interval.
    Lower speeds = higher emissions (stop-and-go).
    """
    speed_factor = max(0.5, 2.0 - (avg_speed / 50.0))  # Higher factor at low speeds
    total_co2 = 0.0
    for vtype, count in vehicles.items():
        factor = EMISSION_FACTORS.get(vtype, 120)
        total_co2 += count * factor * AVG_TRIP_DISTANCE * speed_factor
    return round(total_co2, 2)


# ────────────────────────────────────────────
# MAIN SIMULATION
# ────────────────────────────────────────────
def run_simulation(days: int = SIMULATION_DAYS, seed: int = 42) -> pd.DataFrame:
    """Run the full traffic simulation and return a DataFrame."""
    random.seed(seed)
    np.random.seed(seed)

    # Build city network
    try:
        _, _, adj_full = load_metr_la_adjacency()
        sub_adj, _ = extract_subgraph(adj_full, NUM_INTERSECTIONS)
        graph = build_city_graph(sub_adj)
        print(f"[SIM] Loaded METR-LA topology: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    except Exception as e:
        print(f"[SIM] METR-LA load failed ({e}), using grid topology")
        graph = build_city_graph()

    intersections = [f"J{i}" for i in range(1, NUM_INTERSECTIONS + 1)]
    total_timesteps = days * 24 * TIMESTEPS_PER_HOUR
    records = []

    # State tracking for queue propagation
    prev_queues = {j: 0 for j in intersections}

    print(f"[SIM] Starting simulation: {days} days, {total_timesteps} timesteps, {NUM_INTERSECTIONS} intersections")

    day_weather = None

    for t in range(total_timesteps):
        # Compute time
        minutes_elapsed = t * (60 // TIMESTEPS_PER_HOUR)
        timestamp = START_DATE + timedelta(minutes=minutes_elapsed)
        hour = timestamp.hour
        day_of_week = timestamp.weekday()
        day_num = t // (24 * TIMESTEPS_PER_HOUR) + 1

        # Weather (changes slowly, mostly per-day)
        if t % (24 * TIMESTEPS_PER_HOUR) == 0:
            day_weather = get_weather()
        weather = get_weather(day_weather)

        for junction in intersections:
            zone = INTERSECTION_ZONE[junction]
            neighbors = get_neighbors(graph, junction)

            # --- Traffic Volume ---
            base = get_base_volume(zone)
            multiplier = get_traffic_multiplier(hour, day_of_week, zone)
            volume = int(base * multiplier)

            # Queue spillover from neighbors
            if neighbors:
                neighbor_queue_avg = np.mean([prev_queues.get(n, 0) for n in neighbors])
                spillover = int(neighbor_queue_avg * 0.15)
                volume += spillover

            # --- Incident ---
            incident = generate_incident(weather)
            inc_fx = incident_effects(incident)

            # --- Vehicle Distribution ---
            vehicles = get_vehicle_distribution(zone, volume)
            emergency_count = vehicles.get("Emergency_Vehicles", 0)
            has_emergency = emergency_count > 0

            # --- Compute Metrics ---
            effective_capacity = int(1800 * (1.0 - inc_fx["capacity_reduction"]))
            congestion = compute_congestion_level(volume, effective_capacity)

            # Queue length
            if volume > effective_capacity:
                queue_growth = int((volume - effective_capacity) / TIMESTEPS_PER_HOUR)
            else:
                queue_growth = -int(prev_queues[junction] * 0.3)  # Queue dissipation
            queue_length = max(0, prev_queues[junction] + queue_growth)
            queue_length = min(queue_length, 100)  # Cap at 100

            # Average speed
            w_fx = weather_effects(weather)
            free_flow_speed = 50.0  # km/h
            congestion_speed_reduction = {"Low": 0, "Moderate": 10, "High": 20, "Critical": 30}
            avg_speed = max(5.0, round(
                free_flow_speed
                - congestion_speed_reduction.get(congestion, 0)
                - w_fx["speed_reduction"]
                - inc_fx["speed_reduction"]
                + random.uniform(-3, 3),
                2
            ))

            # Wait time (minutes)
            base_wait = queue_length * random.uniform(0.3, 0.6)
            wait_time = round(
                base_wait + w_fx["wait_increase"] + inc_fx["wait_increase"],
                2
            )
            wait_time = max(0, wait_time)

            # Throughput (vehicles per 15 min that actually pass)
            throughput = min(volume, effective_capacity)
            throughput = max(0, throughput - int(queue_length * 0.5))

            # Signal timing (baseline)
            timing = baseline_signal_timing(congestion, has_emergency)

            # Emissions
            emissions_co2 = compute_emissions(vehicles, avg_speed)

            # Delay (difference between actual and free-flow travel time)
            free_flow_time = (AVG_TRIP_DISTANCE / free_flow_speed) * 60  # minutes
            actual_time = (AVG_TRIP_DISTANCE / max(avg_speed, 5)) * 60
            delay = round(max(0, actual_time - free_flow_time + wait_time * 0.5), 2)

            # Volume-to-Capacity ratio
            vc_ratio = round(volume / max(effective_capacity, 1), 3)

            # Level of Service (LOS)
            if delay < 1:
                los = "A"
            elif delay < 2:
                los = "B"
            elif delay < 3.5:
                los = "C"
            elif delay < 5.5:
                los = "D"
            elif delay < 8:
                los = "E"
            else:
                los = "F"

            # AI Recommendation (baseline placeholder)
            if has_emergency:
                recommendation = "Emergency Priority Override"
            elif congestion == "Critical":
                recommendation = "Extend Green + Reroute Traffic"
            elif congestion == "High":
                recommendation = "Increase Green Time"
            elif congestion == "Moderate":
                recommendation = "Maintain Current Timing"
            else:
                recommendation = "Reduce Green Time"

            records.append({
                "Timestamp": timestamp,
                "Day": day_num,
                "Hour": hour,
                "Day_of_Week": timestamp.strftime("%A"),
                "Intersection_ID": junction,
                "Zone": zone,
                "Grid_Row": GRID_POSITIONS[junction][0],
                "Grid_Col": GRID_POSITIONS[junction][1],
                "Weather": weather,
                "Incident": incident,
                "Traffic_Volume": volume,
                "Cars": vehicles["Cars"],
                "Motorcycles": vehicles["Motorcycles"],
                "Buses": vehicles["Buses"],
                "Trucks": vehicles["Trucks"],
                "Emergency_Vehicles": emergency_count,
                "Queue_Length": queue_length,
                "Average_Wait_Time_min": wait_time,
                "Average_Speed_kmh": avg_speed,
                "Throughput": throughput,
                "Congestion_Level": congestion,
                "V_C_Ratio": vc_ratio,
                "Level_of_Service": los,
                "Green_Signal_sec": timing["green"],
                "Yellow_Signal_sec": timing["yellow"],
                "Red_Signal_sec": timing["red"],
                "Cycle_Length_sec": timing["green"] + timing["yellow"] + timing["red"],
                "Delay_min": delay,
                "CO2_Emissions_g": emissions_co2,
                "Baseline_Recommendation": recommendation,
                "Num_Neighbors": len(neighbors),
            })

            # Update queue state
            prev_queues[junction] = queue_length

    df = pd.DataFrame(records)
    print(f"[SIM] Simulation complete: {df.shape[0]} records, {df.shape[1]} columns")
    return df


# ────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────
if __name__ == "__main__":
    df = run_simulation()

    # Save CSV
    csv_path = "traffic_simulation.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n[SIM] Saved to {csv_path}")
    print(f"[SIM] Shape: {df.shape}")
    print(f"[SIM] Columns: {list(df.columns)}")
    print(f"\n[SIM] Sample data:")
    print(df.head(3).to_string())

    # Summary statistics
    print(f"\n[SIM] --- Summary ---")
    print(f"  Date range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
    print(f"  Congestion distribution:")
    print(df["Congestion_Level"].value_counts().to_string())
    print(f"\n  Avg wait time by zone:")
    print(df.groupby("Zone")["Average_Wait_Time_min"].mean().round(2).to_string())
    print(f"\n  Avg speed by congestion level:")
    print(df.groupby("Congestion_Level")["Average_Speed_kmh"].mean().round(2).to_string())
    print(f"\n  Total CO2 emissions: {df['CO2_Emissions_g'].sum():,.0f} g")
    print(f"\n[SIM] Done!")