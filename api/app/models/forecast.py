"""
Database models for weather forecasts
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class ForecastModelRun(Base):
    """Model run metadata (GFS, HRRR, NAM cycles)"""
    
    __tablename__ = "forecast_model_runs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False)  # gfs, hrrr, nam
    cycle_time = Column(DateTime, nullable=False)  # Model initialization time
    forecast_hour = Column(Integer, nullable=False)  # Hours from cycle time
    resolution = Column(String(20))  # 0p25, 3km, 12km
    data_path = Column(String(500))  # Path to raw data file
    file_size = Column(Integer)  # Size in bytes
    checksum = Column(String(64))  # SHA256 checksum
    variables = Column(JSON)  # List of variables in this run
    status = Column(String(20), default="ingested")  # ingested, processed, failed
    ingested_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)
    
    __table_args__ = (
        # Unique constraint: same source can't have duplicate cycle+hour
        {"schema": "weather"},
    )


class ProcessedForecast(Base):
    """Processed forecasts in H3 grid format"""
    
    __tablename__ = "processed_forecasts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_run_id = Column(UUID(as_uuid=True), nullable=False)  # Foreign key to ForecastModelRun
    h3_index = Column(String(20), nullable=False)  # H3 cell index (resolution 6)
    forecast_time = Column(DateTime, nullable=False)  # Valid forecast time
    variable = Column(String(50), nullable=False)  # temperature, precipitation, etc.
    value = Column(Float, nullable=False)  # Forecast value
    unit = Column(String(20))  # Celsius, mm, m/s, etc.
    confidence = Column(Float)  # Confidence score (0-1)
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        # Index for spatial and temporal queries
        {"schema": "weather"},
    )


class Observation(Base):
    """Weather observations (METAR/ASOS stations)"""
    
    __tablename__ = "observations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_id = Column(String(10), nullable=False)  # Station identifier
    observation_time = Column(DateTime, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation = Column(Float)  # Meters above sea level
    temperature_c = Column(Float)  # Celsius
    dewpoint_c = Column(Float)  # Celsius
    pressure_hpa = Column(Float)  # Hectopascals
    wind_speed_mps = Column(Float)  Meters per second
    wind_direction_deg = Column(Float)  # Degrees
    precipitation_mm = Column(Float)  # Millimeters
    visibility_m = Column(Float)  # Meters
    cloud_cover_oktas = Column(Integer)  # Oktas (0-8)
    raw_text = Column(String(500))  # Original METAR text
    quality_flag = Column(String(20))  # good, suspect, bad
    ingested_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        {"schema": "weather"},
    )


class EvaluationMetric(Base):
    """Forecast evaluation metrics"""
    
    __tablename__ = "evaluation_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_run_id = Column(UUID(as_uuid=True), nullable=False)
    h3_index = Column(String(20), nullable=False)
    forecast_hour = Column(Integer, nullable=False)
    variable = Column(String(50), nullable=False)
    mae = Column(Float)  # Mean Absolute Error
    rmse = Column(Float)  # Root Mean Square Error
    bias = Column(Float)  # Forecast bias
    correlation = Column(Float)  # Correlation coefficient
    skill_score = Column(Float)  # Skill score relative to baseline
    sample_size = Column(Integer)  # Number of observations used
    evaluation_period_start = Column(DateTime)
    evaluation_period_end = Column(DateTime)
    calculated_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        {"schema": "weather"},
    )


class BlendedForecast(Base):
    """Final blended forecasts for API consumption"""
    
    __tablename__ = "blended_forecasts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    h3_index = Column(String(20), nullable=False)
    forecast_time = Column(DateTime, nullable=False)
    variable = Column(String(50), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    confidence = Column(Float)
    sources = Column(JSON)  # List of sources used in blending
    source_weights = Column(JSON)  # Weight given to each source
    model_version = Column(String(50))  # Blending model version
    generated_at = Column(DateTime, server_default=func.now())
    valid_until = Column(DateTime)
    
    __table_args__ = (
        # Index for API queries
        {"schema": "weather"},
    )