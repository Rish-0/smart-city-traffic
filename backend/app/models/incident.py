"""Incident model for accident/road closure tracking."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, func
from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=False)
    intersection_id = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    severity = Column(String(20), nullable=False, default="medium")
    status = Column(String(30), nullable=False, default="reported")
    priority = Column(Integer, nullable=False, default=3)
    reported_by = Column(Integer, nullable=True)
    assigned_to = Column(Integer, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
