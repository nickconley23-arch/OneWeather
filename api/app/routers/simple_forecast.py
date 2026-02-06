"""
Simple forecast endpoint that actually works
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging

from app.services.simple_weather import simple_weather, SimpleForecastPoint

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{latitude}/{longitude}")
async def get_simple_forecast(latitude: float, longitude: float, hours: int = 24):
    """
    Get simple weather forecast that actually works
    """
    try:
        # Validate coordinates
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="Invalid coordinates")
        
        logger.info(f"Getting forecast for {latitude}, {longitude}")
        
        # Get forecast
        points = await simple_weather.get_forecast(latitude, longitude)
        
        # Limit to requested hours
        points = points[:hours]
        
        # Convert to response format
        forecast_points = []
        for point in points:
            forecast_points.append({
                "timestamp": point.timestamp.isoformat(),
                "temperature_c": point.temperature_c,
                "precipitation_mm": point.precipitation_mm,
                "wind_speed_mps": point.wind_speed_mps,
                "humidity_percent": point.humidity_percent,
                "source": point.source
            })
        
        response = {
            "latitude": latitude,
            "longitude": longitude,
            "forecast_hours": len(forecast_points),
            "generated_at": datetime.utcnow().isoformat(),
            "points": forecast_points,
            "sources_used": ["openmeteo"],
            "blending_method": "direct",
            "status": "success"
        }
        
        logger.info(f"Returning {len(forecast_points)} forecast points")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in simple forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ardmore/demo")
async def get_ardmore_forecast():
    """Get forecast for Ardmore, PA (demo location)"""
    return await get_simple_forecast(40.0048, -75.2923, hours=12)