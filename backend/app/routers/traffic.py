"""Traffic data API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.traffic_data import TrafficData
from app.models.signal import Signal
from app.models.user import User

router = APIRouter(prefix="/api/traffic", tags=["Traffic"])

@router.get("/current")
async def get_current_traffic(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    latest = db.query(func.max(TrafficData.timestamp)).filter(TrafficData.source == "simulation").scalar()
    if not latest: return {"intersections": [], "summary": {}}
    data = db.query(TrafficData).filter(TrafficData.source == "simulation", TrafficData.timestamp == latest).all()
    intersections = []
    tv, ts, hc = 0, 0, 0
    for d in data:
        tv += d.traffic_volume; ts += (d.avg_speed or 0)
        if d.congestion_level == "High": hc += 1
        intersections.append({"intersection_id": d.intersection_id, "zone": d.zone, "traffic_volume": d.traffic_volume,
            "congestion_level": d.congestion_level, "avg_speed": d.avg_speed, "avg_wait_time": d.avg_wait_time,
            "queue_length": d.queue_length, "weather": d.weather_main, "green_signal": d.green_signal,
            "red_signal": d.red_signal, "emergency_vehicles": d.emergency_vehicles, "ai_recommendation": d.ai_recommendation})
    n = len(intersections) or 1
    return {"intersections": intersections, "timestamp": str(latest),
            "summary": {"total_intersections": len(intersections), "total_volume": tv, "avg_volume": round(tv / n),
                         "avg_speed": round(ts / n, 1), "high_congestion_count": hc}}

@router.get("/historical")
async def get_historical_traffic(source: str = Query("metro"), zone: Optional[str] = None,
    intersection_id: Optional[str] = None, congestion_level: Optional[str] = None,
    weather: Optional[str] = None, hour_start: Optional[int] = None, hour_end: Optional[int] = None,
    limit: int = Query(500, le=5000), offset: int = 0,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(TrafficData)
    if source != "all": q = q.filter(TrafficData.source == source)
    if zone: q = q.filter(TrafficData.zone == zone)
    if intersection_id: q = q.filter(TrafficData.intersection_id == intersection_id)
    if congestion_level: q = q.filter(TrafficData.congestion_level == congestion_level)
    if weather: q = q.filter(TrafficData.weather_main == weather)
    if hour_start is not None: q = q.filter(TrafficData.hour >= hour_start)
    if hour_end is not None: q = q.filter(TrafficData.hour <= hour_end)
    total = q.count()
    data = q.order_by(desc(TrafficData.timestamp)).offset(offset).limit(limit).all()
    return {"total": total, "offset": offset, "limit": limit,
        "data": [{"id": d.id, "timestamp": str(d.timestamp), "intersection_id": d.intersection_id,
            "zone": d.zone, "traffic_volume": d.traffic_volume, "congestion_level": d.congestion_level,
            "avg_speed": d.avg_speed, "avg_wait_time": d.avg_wait_time, "weather": d.weather_main,
            "temp_celsius": d.temp_celsius, "hour": d.hour, "weekday_name": d.weekday_name,
            "month_name": d.month_name, "season": d.season, "source": d.source} for d in data]}

@router.get("/heatmap")
async def get_heatmap(source: str = Query("simulation"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = db.query(TrafficData.hour, TrafficData.weekday, TrafficData.weekday_name,
        func.avg(TrafficData.traffic_volume).label("avg_volume")).filter(TrafficData.source == source).group_by(
        TrafficData.hour, TrafficData.weekday, TrafficData.weekday_name).all()
    return {"heatmap": [{"hour": r.hour, "weekday": r.weekday, "weekday_name": r.weekday_name, "avg_volume": round(r.avg_volume)} for r in results]}

@router.get("/intersections")
async def get_intersections(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    signals = db.query(Signal).all()
    result = []
    for s in signals:
        latest = db.query(TrafficData).filter(TrafficData.intersection_id == s.intersection_id,
            TrafficData.source == "simulation").order_by(desc(TrafficData.timestamp)).first()
        result.append({"intersection_id": s.intersection_id, "zone": s.zone,
            "latitude": float(s.latitude) if s.latitude else None, "longitude": float(s.longitude) if s.longitude else None,
            "green_duration": s.green_duration, "red_duration": s.red_duration, "mode": s.mode, "status": s.status,
            "current_volume": latest.traffic_volume if latest else 0, "congestion_level": latest.congestion_level if latest else "Low",
            "avg_speed": latest.avg_speed if latest else 0})
    return {"intersections": result}
