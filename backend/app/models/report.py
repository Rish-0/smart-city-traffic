"""Report model for generated traffic/analytics reports."""

# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    format = Column(String(10), nullable=False, default="pdf")
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="generating")
    generated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
