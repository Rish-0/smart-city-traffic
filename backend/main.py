"""Smart City Traffic Optimisation System — FastAPI Application Entry Point."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc

from app.core.config import settings
from app.core.database import create_tables, SessionLocal
from app.services.seed import seed_all
from app.services.data_loader import load_all_data
from app.routers import auth, traffic, ai, analytics, emergency, incidents, notifications
from app.services.tomtom import tomtom_service

# Import all models so create_tables picks them up
from app.models.ai_action_log import AIActionLog  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

AUTO_OPTIMIZE_INTERVAL = 300  # 5 minutes


async def _auto_optimize_loop():
    """Background task: periodically scan all intersections and auto-apply AI optimisations."""
    from app.models.traffic_data import TrafficData
    from app.models.signal import Signal
    from app.models.notification import Notification
    from app.models.ai_action_log import AIActionLog as ActionLog
    from app.services.ai_engine import ai_engine, TrafficInput
    from sqlalchemy import func

    while True:
        await asyncio.sleep(AUTO_OPTIMIZE_INTERVAL)
        logger.info("Auto-optimization loop running...")
        db = SessionLocal()
        try:
            signals = db.query(Signal).all()
            now_hour = datetime.now().hour
            applied, skipped = 0, 0

            for sig in signals:
                try:
                    latest = db.query(TrafficData).filter(
                        TrafficData.intersection_id == sig.intersection_id,
                        TrafficData.source == "tomtom_live"
                    ).order_by(desc(TrafficData.timestamp)).first()
                    
                    if not latest:
                        latest = db.query(TrafficData).filter(
                            TrafficData.intersection_id == sig.intersection_id,
                            TrafficData.source == "simulation"
                        ).order_by(desc(TrafficData.timestamp)).first()

                    volume = latest.traffic_volume if latest else 3000
                    weather = latest.weather_main if latest and latest.weather_main else "Clear"
                    queue = latest.queue_length if latest and latest.queue_length else 20
                    ev = latest.emergency_vehicles if latest and latest.emergency_vehicles else 0

                    hist = db.query(func.avg(TrafficData.traffic_volume)).filter(
                        TrafficData.hour == now_hour, TrafficData.source == "metro"
                    ).scalar()

                    inp = TrafficInput(
                        traffic_volume=volume, weather=weather, hour=now_hour,
                        emergency_vehicles=ev,
                        is_rush_hour=(7 <= now_hour <= 10) or (16 <= now_hour <= 20),
                        zone=sig.zone or "Commercial",
                        current_green=sig.green_duration, current_red=sig.red_duration,
                        queue_length=queue, historical_avg_volume=hist,
                    )
                    rec = ai_engine.optimize(inp)

                    # Only auto-apply for High or Critical congestion
                    if rec.congestion_level in ("High", "Critical") or ev > 0:
                        prev_g, prev_r = sig.green_duration, sig.red_duration
                        if rec.suggested_green != prev_g or rec.suggested_red != prev_r:
                            sig.green_duration = rec.suggested_green
                            sig.red_duration = rec.suggested_red
                            sig.updated_at = datetime.utcnow()

                            db.add(ActionLog(
                                intersection_id=sig.intersection_id,
                                action_type=rec.action,
                                previous_green=prev_g, previous_red=prev_r,
                                new_green=rec.suggested_green, new_red=rec.suggested_red,
                                congestion_level=rec.congestion_level,
                                confidence_score=rec.confidence_score,
                                expected_improvement=rec.expected_improvement,
                                reasoning=rec.reasoning,
                                traffic_volume=volume, weather=weather,
                                status="applied", triggered_by="auto",
                            ))
                            applied += 1
                        else:
                            skipped += 1
                    else:
                        skipped += 1

                except Exception as e:
                    logger.warning(f"Auto-optimize error for {sig.intersection_id}: {e}")

            db.commit()
            if applied > 0:
                db.add(Notification(
                    type="ai_action",
                    title="Auto-Optimization Complete",
                    message=f"Background scan applied {applied} signal changes, skipped {skipped}.",
                    severity="info",
                ))
                db.commit()
            logger.info(f"Auto-optimization done: applied={applied}, skipped={skipped}")

        except Exception as e:
            logger.error(f"Auto-optimization loop error: {e}")
        finally:
            db.close()

TOMTOM_POLL_INTERVAL = 900  # 15 minutes to stay under 2500 API calls/day (25 * 4 * 24 = 2400)

async def _tomtom_traffic_loop():
    """Background task: periodically fetch live traffic from TomTom and save to DB."""
    from app.models.traffic_data import TrafficData
    from app.models.signal import Signal

    # If key is missing/default, don't run
    if not settings.TOMTOM_API_KEY or settings.TOMTOM_API_KEY == "your_tomtom_api_key_here":
        logger.warning("TomTom API key not set. Skipping live traffic background loop.")
        return

    while True:
        logger.info("Fetching live traffic from TomTom API...")
        db = SessionLocal()
        try:
            signals = db.query(Signal).all()
            now = datetime.now()
            
            for sig in signals:
                if not sig.latitude or not sig.longitude:
                    continue
                    
                flow_data = await tomtom_service.get_traffic_flow(float(sig.latitude), float(sig.longitude))
                if flow_data:
                    metrics = tomtom_service.estimate_metrics(flow_data)
                    
                    td = TrafficData(
                        timestamp=now,
                        intersection_id=sig.intersection_id,
                        zone=sig.zone,
                        traffic_volume=metrics["volume"],
                        avg_speed=metrics["speed"],
                        congestion_level=metrics["congestion"],
                        weather_main="Clear", # TomTom flow doesn't give weather directly
                        hour=now.hour,
                        day=now.day,
                        weekday=now.weekday(),
                        weekday_name=now.strftime("%A"),
                        month=now.month,
                        month_name=now.strftime("%B"),
                        year=now.year,
                        season="Summer", # simplified
                        is_weekend=1 if now.weekday() >= 5 else 0,
                        is_rush_hour=1 if (7 <= now.hour <= 10) or (16 <= now.hour <= 20) else 0,
                        source="tomtom_live"
                    )
                    db.add(td)
            
            db.commit()
            logger.info("Live traffic data ingested successfully.")
        except Exception as e:
            logger.error(f"TomTom polling error: {e}")
        finally:
            db.close()
            
        await asyncio.sleep(TOMTOM_POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables, seed data, load datasets, start background loop."""
    logger.info("Starting Smart City Traffic Optimisation System...")
    create_tables()
    logger.info("Database tables created.")

    db = SessionLocal()
    try:
        seed_all(db)
        logger.info("Seed data loaded.")
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        result = load_all_data(db, base_dir)
        logger.info(f"Data loading result: {result}")
    except Exception as e:
        logger.error(f"Startup data loading error: {e}")
    finally:
        db.close()

    # Start background auto-optimization loop
    auto_task = asyncio.create_task(_auto_optimize_loop())
    logger.info("Background auto-optimization loop started (every 5 minutes).")
    
    # Start TomTom Live Traffic loop
    tomtom_task = asyncio.create_task(_tomtom_traffic_loop())

    logger.info("System ready.")
    yield

    # Cleanup
    auto_task.cancel()
    tomtom_task.cancel()
    try:
        await auto_task
        await tomtom_task
    except asyncio.CancelledError:
        pass
    logger.info("Shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    description="AI-powered traffic signal optimisation, real-time monitoring, and analytics platform.",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(traffic.router)
app.include_router(ai.router)
app.include_router(analytics.router)
app.include_router(emergency.router)
app.include_router(incidents.router)
app.include_router(notifications.router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}
