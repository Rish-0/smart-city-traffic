"""Signal model — traffic signal configuration per intersection."""

from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True, index=True)
    intersection_id = Column(String(20), unique=True, index=True, nullable=False)
    zone = Column(String(50), nullable=True)
    green_duration = Column(Integer, nullable=False, default=45)
    red_duration = Column(Integer, nullable=False, default=45)
    yellow_duration = Column(Integer, nullable=False, default=5)
    mode = Column(String(30), nullable=False, default="automatic")
    status = Column(String(20), nullable=False, default="active")
    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, server_default=func.now())
