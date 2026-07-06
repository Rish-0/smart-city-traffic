"""AI Traffic Optimisation Engine — Rule-based with Strategy Pattern for easy ML replacement."""

from dataclasses import dataclass
from typing import Optional
import random

@dataclass
class TrafficInput:
    traffic_volume: int
    weather: str = "Clear"
    hour: int = 12
    emergency_vehicles: int = 0
    is_rush_hour: bool = False
    is_weekend: bool = False
    zone: str = "Commercial"
    current_green: int = 45
    current_red: int = 45
    avg_speed: float = 40.0
    queue_length: int = 20
    historical_avg_volume: Optional[float] = None

@dataclass
class TrafficRecommendation:
    congestion_level: str
    suggested_green: int
    suggested_red: int
    expected_wait_time: float
    expected_improvement: float
    confidence_score: float
    reasoning: str
    priority: str
    action: str

class AITrafficEngine:
    WEATHER_FACTORS = {"Clear": 1.0, "Clouds": 1.05, "Rain": 1.25, "Drizzle": 1.15, "Snow": 1.45,
                       "Fog": 1.20, "Mist": 1.10, "Thunderstorm": 1.50, "Haze": 1.08}
    ZONE_WEIGHTS = {"Hospital": 1.3, "School": 1.2, "Commercial": 1.1, "Industrial": 1.0, "Residential": 0.9}

    def classify_congestion(self, volume: int, weather: str = "Clear") -> str:
        adj = volume * self.WEATHER_FACTORS.get(weather, 1.0)
        if adj < 2500: return "Low"
        elif adj < 4500: return "Moderate"
        elif adj < 6500: return "High"
        return "Critical"

    def calculate_signal_timing(self, congestion: str, emergency: int, zone: str, is_rush: bool) -> tuple:
        base = {"Low": (30, 60), "Moderate": (45, 45), "High": (60, 30), "Critical": (75, 25)}
        green, red = base.get(congestion, (45, 45))
        if is_rush: green, red = min(green + 10, 90), max(red - 5, 15)
        zw = self.ZONE_WEIGHTS.get(zone, 1.0)
        if zw > 1.0: green = min(int(green * zw), 90)
        if emergency > 0: green, red = min(green + 15 * emergency, 90), max(red - 10, 15)
        return green, red

    def estimate_wait(self, volume: int, green: int, red: int, queue: int) -> float:
        cycle = green + red + 5
        cap = green * 30 / 60
        if cap == 0: return 99.9
        cycles = max(1, queue / max(cap, 1))
        wait = (red / 60) * cycles * min(volume / 3000, 3.0)
        return round(max(0.5, min(wait, 120.0)), 1)

    def calculate_improvement(self, cg: int, cr: int, sg: int, sr: int, cong: str) -> float:
        if cg == sg and cr == sr: return 0.0
        base = abs(sg - cg) * 1.5
        mult = {"Low": 0.5, "Moderate": 1.0, "High": 1.5, "Critical": 2.0}.get(cong, 1.0)
        return round(min(base * mult, 45.0), 1)

    def calculate_confidence(self, volume: int, has_hist: bool, weather: str) -> float:
        base = 0.75 + (0.10 if volume > 5000 else 0.05 if volume > 3000 else 0)
        if has_hist: base += 0.08
        unc = {"Clear": 0, "Clouds": -0.02, "Rain": -0.05, "Snow": -0.08, "Thunderstorm": -0.10}.get(weather, -0.03)
        return round(max(0.5, min(base + unc + random.uniform(-0.03, 0.03), 0.98)), 2)

    def optimize(self, inp: TrafficInput) -> TrafficRecommendation:
        cong = self.classify_congestion(inp.traffic_volume, inp.weather)
        green, red = self.calculate_signal_timing(cong, inp.emergency_vehicles, inp.zone, inp.is_rush_hour)
        wait = self.estimate_wait(inp.traffic_volume, green, red, inp.queue_length)
        imp = self.calculate_improvement(inp.current_green, inp.current_red, green, red, cong)
        conf = self.calculate_confidence(inp.traffic_volume, inp.historical_avg_volume is not None, inp.weather)

        if inp.emergency_vehicles > 0: action, priority = "emergency_priority", "critical"
        elif cong in ("Critical", "High"): action, priority = "increase_green", "high"
        elif cong == "Low": action, priority = "decrease_green", "low"
        else: action, priority = "maintain", "medium"

        parts = [f"Traffic congestion is {cong.lower()}."]
        wf = self.WEATHER_FACTORS.get(inp.weather, 1.0)
        if inp.weather not in ("Clear", "Clouds"): parts.append(f"{inp.weather} increases congestion by {int((wf-1)*100)}%.")
        if inp.is_rush_hour: parts.append("Rush hour — extended green recommended.")
        if inp.emergency_vehicles > 0: parts.append(f"{inp.emergency_vehicles} emergency vehicle(s) — priority activated.")
        if inp.zone in ("Hospital", "School"): parts.append(f"{inp.zone} zone — elevated priority.")
        if imp > 0: parts.append(f"Recommended changes could improve flow by ~{imp}%.")

        return TrafficRecommendation(
            congestion_level=cong, suggested_green=green, suggested_red=red,
            expected_wait_time=wait, expected_improvement=imp, confidence_score=conf,
            reasoning=" ".join(parts), priority=priority, action=action)

ai_engine = AITrafficEngine()
