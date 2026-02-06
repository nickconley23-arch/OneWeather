"""
Forecast API endpoints
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from app.services.weather_sources import weather_manager, ForecastPoint
from app.schemas.forecast import ForecastResponse, ForecastPointResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{latitude}/{longitude}", response_model=ForecastResponse)
async def get_forecast(
    latitude: float = Path(..., ge=-90, le=90, description="Latitude"),
    longitude: float = Path(..., ge=-180, le=180, description="Longitude"),
    hours: Optional[int] = Query(24, ge=1, le=168, description="Hours of forecast to return"),
    include_sources: Optional[bool] = Query(False, description="Include individual source forecasts"),
):
    """
    Get blended weather forecast for a location
    
    Returns a forecast blended from multiple weather sources using simple averaging.
    """
    try:
        # Validate CONUS (for Phase 1)
        if not (24 <= latitude <= 50 and -125 <= longitude <= -66):
            raise HTTPException(
                status_code=400,
                detail="Phase 1 only supports CONUS (24°N-50°N, 125°W-66°W)"
            )
        
        logger.info(f"Getting forecast for {latitude}, {longitude}")
        
        # Get forecasts from all sources
        source_forecasts = await weather_manager.get_all_forecasts(latitude, longitude)
        
        # Blend forecasts
        blended_forecast = weather_manager.blend_forecasts(source_forecasts)
        
        # Use all forecast points for now (time filtering disabled)
        filtered_forecast = blended_forecast[:hours] if hours < len(blended_forecast) else blended_forecast
        
        # Convert to response format
        forecast_points = [
            ForecastPointResponse(
                timestamp=point.timestamp,
                temperature_c=point.temperature_c,
                precipitation_mm=point.precipitation_mm,
                precipitation_probability=point.precipitation_probability,
                wind_speed_mps=point.wind_speed_mps,
                wind_direction_deg=point.wind_direction_deg,
                humidity_percent=point.humidity_percent,
                cloud_cover_percent=point.cloud_cover_percent,
                pressure_hpa=point.pressure_hpa,
                source=point.source
            )
            for point in filtered_forecast
        ]
        
        # Prepare source details if requested
        source_details = None
        if include_sources:
            source_details = {}
            for source_name, points in source_forecasts.items():
                if points:
                    source_details[source_name] = {
                        "count": len(points),
                        "first_timestamp": points[0].timestamp.isoformat() if points else None,
                        "last_timestamp": points[-1].timestamp.isoformat() if points else None,
                    }
        
        response = ForecastResponse(
            latitude=latitude,
            longitude=longitude,
            forecast_hours=hours,
            generated_at=datetime.utcnow(),
            points=forecast_points,
            sources_used=list(source_forecasts.keys()),
            source_details=source_details,
            blending_method="simple_average"
        )
        
        logger.info(f"Returning {len(forecast_points)} forecast points")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources/status")
async def get_source_status():
    """
    Get status of all weather data sources
    """
    sources = []
    
    for name, source in weather_manager.sources.items():
        sources.append({
            "name": name,
            "display_name": source.name,
            "cache_ttl": source.cache_ttl,
            "last_fetch": source.last_fetch.isoformat() if source.last_fetch else None,
            "cache_size": len(source.cache) if source.cache else 0
        })
    
    return {
        "sources": sources,
        "total_sources": len(sources),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/demo/nyc")
async def get_demo_forecast():
    """
    Get forecast for a demo location (New York City)
    """
    # NYC coordinates
    latitude = 40.7128
    longitude = -74.0060
    
    return await get_forecast(latitude, longitude, hours=24, include_sources=True)