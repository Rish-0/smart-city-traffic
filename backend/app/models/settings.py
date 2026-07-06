"""System settings model — key-value configuration store."""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="general")
    description = Column(String(300), nullable=True)
    updated_by = Column(Integer, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
