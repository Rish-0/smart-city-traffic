"""Audit log model for tracking user actions."""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    username = Column(String(100), nullable=True)
    action = Column(String(50), nullable=False)
    resource = Column(String(100), nullable=False)
    resource_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(300), nullable=True)
    status = Column(String(20), nullable=False, default="success")
    created_at = Column(DateTime, server_default=func.now())
