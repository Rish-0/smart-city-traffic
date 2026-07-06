"""Analytics API routes — comprehensive traffic analytics and chart data."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.traffic_data import TrafficData
from app.models.user import User
import statistics

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("/summary")
async def get_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = db.query(TrafficData).count()
    mc = db.query(TrafficData).filter(TrafficData.source == "metro").count()
    sc = db.query(TrafficData).filter(TrafficData.source == "simulation").count()
    ss = db.query(func.avg(TrafficData.traffic_volume).label("av"), func.max(TrafficData.traffic_volume).label("mx"),
        func.min(TrafficData.traffic_volume).label("mn"), func.avg(TrafficData.avg_speed).label("asp"),
        func.avg(TrafficData.avg_wait_time).label("aw")).filter(TrafficData.source == "simulation").first()
    cd = db.query(TrafficData.congestion_level, func.count().label("c")).filter(
        TrafficData.source == "simulation").group_by(TrafficData.congestion_level).all()
    pk = db.query(TrafficData.hour, func.avg(TrafficData.traffic_volume).label("av")).filter(
        TrafficData.source == "metro").group_by(TrafficData.hour).order_by(desc("av")).first()
    return {"total_records": total, "metro_records": mc, "simulation_records": sc,
        "avg_volume": round(ss.av or 0), "max_volume": ss.mx or 0, "min_volume": ss.mn or 0,
        "avg_speed": round(ss.asp or 0, 1), "avg_wait_time": round(ss.aw or 0, 1),
        "peak_hour": pk.hour if pk else 8, "peak_hour_volume": round(pk.av) if pk else 0,
        "congestion_distribution": {r.congestion_level: r.c for r in cd}}

@router.get("/hourly")
async def get_hourly(source: str = Query("metro"), zone: Optional[str] = None,
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = db.query(TrafficData.hour, func.avg(TrafficData.traffic_volume).label("av"),
        func.count().label("dp")).filter(TrafficData.source == source)
    if zone: q = q.filter(TrafficData.zone == zone)
    results = q.group_by(TrafficData.hour).order_by(TrafficData.hour).all()
    return {"data": [{"hour": r.hour, "label": f"{r.hour:02d}:00", "avg_volume": round(r.av), "data_points": r.dp} for r in results]}

@router.get("/weekday")
async def get_weekday(source: str = Query("metro"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = db.query(TrafficData.weekday, TrafficData.weekday_name, func.avg(TrafficData.traffic_volume).label("av")).filter(
        TrafficData.source == source, TrafficData.weekday.isnot(None)).group_by(TrafficData.weekday, TrafficData.weekday_name).order_by(TrafficData.weekday).all()
    return {"data": [{"weekday": r.weekday, "name": r.weekday_name, "avg_volume": round(r.av)} for r in results]}

@router.get("/monthly")
async def get_monthly(source: str = Query("metro"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = db.query(TrafficData.month, TrafficData.month_name, func.avg(TrafficData.traffic_volume).label("av")).filter(
        TrafficData.source == source, TrafficData.month.isnot(None)).group_by(TrafficData.month, TrafficData.month_name).order_by(TrafficData.month).all()
    return {"data": [{"month": r.month, "name": r.month_name, "avg_volume": round(r.av)} for r in results]}

@router.get("/weather-impact")
async def get_weather_impact(source: str = Query("metro"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = db.query(TrafficData.weather_main, func.avg(TrafficData.traffic_volume).label("av"),
        func.count().label("occ")).filter(TrafficData.source == source, TrafficData.weather_main.isnot(None)).group_by(
        TrafficData.weather_main).order_by(desc("av")).all()
    return {"data": [{"weather": r.weather_main, "avg_volume": round(r.av), "occurrences": r.occ} for r in results]}

@router.get("/holiday")
async def get_holiday(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ha = db.query(func.avg(TrafficData.traffic_volume)).filter(TrafficData.source == "metro", TrafficData.holiday.isnot(None)).scalar() or 0
    ra = db.query(func.avg(TrafficData.traffic_volume)).filter(TrafficData.source == "metro", TrafficData.holiday.is_(None)).scalar() or 0
    holidays = db.query(TrafficData.holiday, func.avg(TrafficData.traffic_volume).label("av"),
        func.count().label("dp")).filter(TrafficData.source == "metro", TrafficData.holiday.isnot(None)).group_by(
        TrafficData.holiday).order_by(desc("av")).all()
    return {"holiday_avg": round(ha), "regular_avg": round(ra),
        "difference_pct": round((ra - ha) / max(ra, 1) * 100, 1),
        "holidays": [{"name": h.holiday, "avg_volume": round(h.av), "data_points": h.dp} for h in holidays]}

@router.get("/distribution")
async def get_distribution(source: str = Query("metro"), bins: int = Query(20, ge=5, le=50),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    volumes = db.query(TrafficData.traffic_volume).filter(TrafficData.source == source).all()
    if not volumes: return {"bins": [], "stats": {}}
    vals = [v[0] for v in volumes]
    mn, mx = min(vals), max(vals); bw = (mx - mn) / bins
    hist = [{"bin": f"{int(mn + i * bw)}-{int(mn + (i+1) * bw)}", "low": int(mn + i * bw),
             "high": int(mn + (i+1) * bw), "count": sum(1 for v in vals if mn + i * bw <= v < mn + (i+1) * bw)} for i in range(bins)]
    return {"bins": hist, "stats": {"mean": round(statistics.mean(vals)), "median": round(statistics.median(vals)),
        "std_dev": round(statistics.stdev(vals)), "min": mn, "max": mx, "total": len(vals)}}

@router.get("/peak-hours")
async def get_peak_hours(source: str = Query("metro"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = db.query(TrafficData.hour, func.avg(TrafficData.traffic_volume).label("av"),
        func.max(TrafficData.traffic_volume).label("mx"), func.min(TrafficData.traffic_volume).label("mn")).filter(
        TrafficData.source == source).group_by(TrafficData.hour).order_by(TrafficData.hour).all()
    data = [{"hour": r.hour, "label": f"{r.hour:02d}:00", "avg_volume": round(r.av), "max_volume": r.mx,
             "min_volume": r.mn, "is_peak": 7 <= r.hour <= 10 or 16 <= r.hour <= 20} for r in results]
    sorted_d = sorted(data, key=lambda x: x["avg_volume"], reverse=True)
    return {"data": data, "peak_hours": sorted_d[:3]}

@router.get("/scatter")
async def get_scatter(source: str = Query("simulation"), x_field: str = Query("traffic_volume"),
    y_field: str = Query("avg_speed"), limit: int = Query(500, le=2000),
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = db.query(TrafficData).filter(TrafficData.source == source).limit(limit).all()
    points = [{"x": getattr(d, x_field, None), "y": getattr(d, y_field, None), "label": d.intersection_id or "",
               "congestion": d.congestion_level, "zone": d.zone} for d in data if getattr(d, x_field, None) is not None and getattr(d, y_field, None) is not None]
    return {"data": points, "x_field": x_field, "y_field": y_field}

@router.get("/signal-comparison")
async def get_signal_comparison(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = db.query(TrafficData.zone, TrafficData.congestion_level,
        func.avg(TrafficData.green_signal).label("ag"), func.avg(TrafficData.red_signal).label("ar"),
        func.avg(TrafficData.avg_wait_time).label("aw")).filter(TrafficData.source == "simulation",
        TrafficData.zone.isnot(None)).group_by(TrafficData.zone, TrafficData.congestion_level).all()
    return {"data": [{"zone": r.zone, "congestion_level": r.congestion_level, "avg_green": round(r.ag, 1) if r.ag else 0,
        "avg_red": round(r.ar, 1) if r.ar else 0, "avg_wait": round(r.aw, 1) if r.aw else 0} for r in results]}
