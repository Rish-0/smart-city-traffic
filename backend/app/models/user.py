"""User model with role-based access control."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="analyst")
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    department = Column(String(100), nullable=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    ROLES = ["traffic_admin", "traffic_officer", "city_admin", "emergency_services", "analyst"]
