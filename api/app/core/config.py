"""
Configuration settings for OneWeather API
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    RELOAD: bool = False
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    SECRET_KEY: str = "change-this-in-production"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/oneweather"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    STORAGE_PATH: str = "./data"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    # External Services
    NOAA_NOMADS_BASE_URL: str = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
    METAR_BASE_URL: str = "https://aviationweather.gov/api/data"
    
    # Ingestion Settings
    GFS_RESOLUTION: str = "0p25"
    GFS_FORECAST_HOURS: List[int] = [0, 1, 3, 6, 12, 24, 48]
    GFS_CYCLES: List[str] = ["00", "06", "12", "18"]
    DATA_RETENTION_DAYS: int = 14
    
    # Monitoring
    PROMETHEUS_METRICS_PORT: int = 8001
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()