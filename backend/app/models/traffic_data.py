"""Traffic data model — stores both historical Metro and simulation data."""

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.core.database import Base


class TrafficData(Base):
    __tablename__ = "traffic_data"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, nullable=False)
    intersection_id = Column(String(20), index=True, nullable=True)
    zone = Column(String(50), nullable=True)
    traffic_volume = Column(Integer, nullable=False)
    cars = Column(Integer, nullable=True)
    motorcycles = Column(Integer, nullable=True)
    buses = Column(Integer, nullable=True)
    trucks = Column(Integer, nullable=True)
    emergency_vehicles = Column(Integer, nullable=True, default=0)
    queue_length = Column(Integer, nullable=True)
    avg_wait_time = Column(Float, nullable=True)
    avg_speed = Column(Float, nullable=True)
    congestion_level = Column(String(20), nullable=True)
    green_signal = Column(Integer, nullable=True)
    red_signal = Column(Integer, nullable=True)
    ai_recommendation = Column(String(100), nullable=True)
    temp_celsius = Column(Float, nullable=True)
    rain_1h = Column(Float, nullable=True, default=0)
    snow_1h = Column(Float, nullable=True, default=0)
    clouds_all = Column(Integer, nullable=True)
    weather_main = Column(String(50), nullable=True)
    weather_description = Column(String(200), nullable=True)
    holiday = Column(String(100), nullable=True)
    hour = Column(Integer, nullable=True)
    day = Column(Integer, nullable=True)
    weekday = Column(Integer, nullable=True)
    weekday_name = Column(String(20), nullable=True)
    month = Column(Integer, nullable=True)
    month_name = Column(String(20), nullable=True)
    year = Column(Integer, nullable=True)
    season = Column(String(20), nullable=True)
    is_weekend = Column(Integer, nullable=True, default=0)
    is_rush_hour = Column(Integer, nullable=True, default=0)
    source = Column(String(20), nullable=False, default="metro")
    created_at = Column(DateTime, server_default=func.now())
