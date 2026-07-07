"""Application configuration using Pydantic Settings."""

# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart City Traffic Optimisation System"
    API_VERSION: str = "v1"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./smart_city_traffic.db"
    SECRET_KEY: str = "smart-city-traffic-super-secret-key-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    TOMTOM_API_KEY: Optional[str] = None

    REPORTS_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
