"""Notification model for real-time alerts."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="info")
    is_read = Column(Boolean, default=False)
    user_id = Column(Integer, nullable=True)
    related_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
