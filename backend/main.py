"""Smart City Traffic Optimisation System — FastAPI Application Entry Point."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import create_tables, SessionLocal
from app.services.seed import seed_all
from app.services.data_loader import load_all_data
from app.routers import auth, traffic, ai, analytics, emergency, incidents, notifications

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables, seed data, load datasets."""
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

    logger.info("System ready.")
    yield
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
