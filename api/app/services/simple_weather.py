"""
Simple weather source for immediate demo
"""

import httpx
import logging
from datetime import datetime, timezone
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SimpleForecastPoint:
    """Simplified forecast point"""
    timestamp: datetime
    temperature_c: float
    precipitation_mm: float
    wind_speed_mps: float
    humidity_percent: float
    source: str


class SimpleWeatherAPI:
    """Simple weather API that actually works"""
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    async def get_forecast(self, latitude: float, longitude: float) -> List[SimpleForecastPoint]:
        """Get simple forecast from Open-Meteo"""
        try:
            url = f"{self.base_url}?latitude={latitude}&longitude={longitude}"
            url += "&hourly=temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m"
            url += "&forecast_days=2"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                points = []
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])
                temps = hourly.get("temperature_2m", [])
                precip = hourly.get("precipitation", [])
                humidity = hourly.get("relative_humidity_2m", [])
                wind = hourly.get("wind_speed_10m", [])
                
                for i in range(min(24, len(times))):  # Just 24 hours
                    try:
                        time_str = times[i]
                        # Parse ISO timestamp
                        if time_str.endswith('Z'):
                            time_str = time_str[:-1] + '+00:00'
                        timestamp = datetime.fromisoformat(time_str)
                        
                        point = SimpleForecastPoint(
                            timestamp=timestamp,
                            temperature_c=temps[i] if i < len(temps) else 15.0,
                            precipitation_mm=precip[i] if i < len(precip) else 0.0,
                            wind_speed_mps=wind[i] if i < len(wind) else 3.0,
                            humidity_percent=humidity[i] if i < len(humidity) else 60.0,
                            source="openmeteo"
                        )
                        points.append(point)
                    except (ValueError, IndexError):
                        continue
                
                logger.info(f"Got {len(points)} forecast points")
                return points
                
        except Exception as e:
            logger.error(f"Error getting forecast: {e}")
            # Return some fallback data
            return self.get_fallback_forecast()
    
    def get_fallback_forecast(self) -> List[SimpleForecastPoint]:
        """Fallback forecast if API fails"""
        points = []
        now = datetime.now(timezone.utc)
        
        for i in range(24):
            timestamp = datetime.fromtimestamp(now.timestamp() + i * 3600, tz=timezone.utc)
            # Simple temperature curve
            hour = timestamp.hour
            temp = 15 + 5 * (1 - abs(hour - 14) / 7)  # Peaks at 2 PM
            
            point = SimpleForecastPoint(
                timestamp=timestamp,
                temperature_c=temp,
                precipitation_mm=0.0,
                wind_speed_mps=3.0,
                humidity_percent=60.0,
                source="fallback"
            )
            points.append(point)
        
        return points


# Global instance
simple_weather = SimpleWeatherAPI()