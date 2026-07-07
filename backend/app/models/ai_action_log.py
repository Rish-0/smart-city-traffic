"""AI Action Log model — tracks every AI auto-applied signal optimisation."""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, func
from app.core.database import Base


class AIActionLog(Base):
    __tablename__ = "ai_action_logs"
    id = Column(Integer, primary_key=True, index=True)
    intersection_id = Column(String(20), index=True, nullable=False)
    action_type = Column(String(30), nullable=False)  # increase_green, decrease_green, emergency_priority, maintain
    previous_green = Column(Integer, nullable=False)
    previous_red = Column(Integer, nullable=False)
    new_green = Column(Integer, nullable=False)
    new_red = Column(Integer, nullable=False)
    congestion_level = Column(String(20), nullable=False)
    confidence_score = Column(Float, nullable=False)
    expected_improvement = Column(Float, nullable=False, default=0.0)
    reasoning = Column(Text, nullable=True)
    traffic_volume = Column(Integer, nullable=True)
    weather = Column(String(30), nullable=True)
    status = Column(String(20), nullable=False, default="applied")  # applied, skipped, reverted
    triggered_by = Column(String(30), nullable=False, default="manual")  # manual, auto, bulk
    applied_at = Column(DateTime, server_default=func.now())
