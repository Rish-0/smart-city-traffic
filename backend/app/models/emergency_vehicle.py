"""Emergency Vehicle model for tracking active emergency units."""

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.core.database import Base


class EmergencyVehicle(Base):
    __tablename__ = "emergency_vehicles"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(30), nullable=False)
    call_sign = Column(String(30), unique=True, nullable=False)
    status = Column(String(30), nullable=False, default="available")
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    destination_name = Column(String(200), nullable=True)
    nearest_junction = Column(String(20), nullable=True)
    eta_minutes = Column(Integer, nullable=True)
    priority_active = Column(Integer, default=0)
    dispatcher_notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
