"""
Forecast API schemas
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any


class ForecastPointResponse(BaseModel):
    """Individual forecast point"""
    timestamp: datetime
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    precipitation_mm: Optional[float] = Field(None, description="Precipitation in mm")
    precipitation_probability: Optional[float] = Field(None, description="Precipitation probability (0-1)")
    wind_speed_mps: Optional[float] = Field(None, description="Wind speed in meters per second")
    wind_direction_deg: Optional[float] = Field(None, description="Wind direction in degrees")
    humidity_percent: Optional[float] = Field(None, description="Relative humidity percentage")
    cloud_cover_percent: Optional[float] = Field(None, description="Cloud cover percentage")
    pressure_hpa: Optional[float] = Field(None, description="Pressure in hectopascals")
    source: str = Field(..., description="Source of this forecast point")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ForecastResponse(BaseModel):
    """Complete forecast response"""
    latitude: float
    longitude: float
    forecast_hours: int
    generated_at: datetime
    points: List[ForecastPointResponse]
    sources_used: List[str]
    source_details: Optional[Dict[str, Any]] = None
    blending_method: str = Field(..., description="Method used to blend forecasts")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SourceStatusResponse(BaseModel):
    """Weather source status"""
    name: str
    display_name: str
    cache_ttl: int
    last_fetch: Optional[str]
    cache_size: int
    status: str = "unknown"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }