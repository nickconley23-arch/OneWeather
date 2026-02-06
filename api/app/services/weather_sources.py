"""
Weather Data Source Integrations
Free tier APIs for Phase 1
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class ForecastPoint:
    """Standardized forecast data point"""
    timestamp: datetime
    temperature_c: Optional[float]
    precipitation_mm: Optional[float]
    precipitation_probability: Optional[float]
    wind_speed_mps: Optional[float]
    wind_direction_deg: Optional[float]
    humidity_percent: Optional[float]
    cloud_cover_percent: Optional[float]
    pressure_hpa: Optional[float]
    source: str
    latitude: float
    longitude: float


class WeatherSource:
    """Base class for all weather data sources"""
    
    def __init__(self, name: str, cache_ttl: int = 300):
        self.name = name
        self.cache_ttl = cache_ttl
        self.last_fetch = None
        self.cache = None
    
    async def get_forecast(self, latitude: float, longitude: float) -> List[ForecastPoint]:
        """Get forecast for a specific location"""
        raise NotImplementedError
    
    def _standardize_response(self, raw_data: Dict, latitude: float, longitude: float) -> List[ForecastPoint]:
        """Convert source-specific format to standardized ForecastPoint"""
        raise NotImplementedError


class OpenMeteoSource(WeatherSource):
    """Open-Meteo API (free, multiple models)"""
    
    def __init__(self):
        super().__init__("openmeteo", cache_ttl=300)
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.models = ["gfs", "ecmwf", "gem"]  # GFS, ECMWF, Canadian model
    
    async def get_forecast(self, latitude: float, longitude: float) -> List[ForecastPoint]:
        """Get forecast from Open-Meteo"""
        forecasts = []
        
        # Try each model
        for model in self.models:
            try:
                url = f"{self.base_url}?latitude={latitude}&longitude={longitude}"
                url += f"&hourly=temperature_2m,precipitation,rain,showers,snowfall,pressure_msl"
                url += f",cloud_cover,wind_speed_10m,wind_direction_10m,relative_humidity_2m"
                url += f"&models={model}&forecast_days=3"
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Extract forecast points
                    points = self._parse_openmeteo_response(data, model, latitude, longitude)
                    forecasts.extend(points)
                    
                    logger.info(f"Open-Meteo {model}: Got {len(points)} forecast points")
                    
            except Exception as e:
                logger.warning(f"Open-Meteo {model} failed: {e}")
                continue
        
        return forecasts
    
    def _parse_openmeteo_response(self, data: Dict, model: str, 
                                 latitude: float, longitude: float) -> List[ForecastPoint]:
        """Parse Open-Meteo API response"""
        points = []
        
        if "hourly" not in data:
            return points
        
        hourly = data["hourly"]
        time_list = hourly.get("time", [])
        
        # Extract all available variables
        temp_list = hourly.get("temperature_2m", [])
        precip_list = hourly.get("precipitation", [])
        rain_list = hourly.get("rain", [])
        snow_list = hourly.get("snowfall", [])
        pressure_list = hourly.get("pressure_msl", [])
        cloud_list = hourly.get("cloud_cover", [])
        wind_speed_list = hourly.get("wind_speed_10m", [])
        wind_dir_list = hourly.get("wind_direction_10m", [])
        humidity_list = hourly.get("relative_humidity_2m", [])
        
        # Combine rain and snow for total precipitation
        def get_precipitation(i):
            rain = rain_list[i] if i < len(rain_list) else 0
            snow = snow_list[i] if i < len(snow_list) else 0
            precip = precip_list[i] if i < len(precip_list) else 0
            return max(rain + snow, precip)  # Use max of total or precipitation
        
        for i, time_str in enumerate(time_list):
            try:
                timestamp = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                
                point = ForecastPoint(
                    timestamp=timestamp,
                    temperature_c=temp_list[i] if i < len(temp_list) else None,
                    precipitation_mm=get_precipitation(i),
                    precipitation_probability=None,  # Open-Meteo doesn't provide probability
                    wind_speed_mps=wind_speed_list[i] if i < len(wind_speed_list) else None,
                    wind_direction_deg=wind_dir_list[i] if i < len(wind_dir_list) else None,
                    humidity_percent=humidity_list[i] if i < len(humidity_list) else None,
                    cloud_cover_percent=cloud_list[i] if i < len(cloud_list) else None,
                    pressure_hpa=pressure_list[i] if i < len(pressure_list) else None,
                    source=f"openmeteo_{model}",
                    latitude=latitude,
                    longitude=longitude
                )
                points.append(point)
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing Open-Meteo point {i}: {e}")
                continue
        
        return points


class NOAAWeatherGovSource(WeatherSource):
    """NOAA Weather.gov API (free, US only)"""
    
    def __init__(self):
        super().__init__("noaa_weathergov", cache_ttl=600)
        self.base_url = "https://api.weather.gov"
        self.user_agent = "OneWeather/1.0 (https://github.com/nickconley23-arch/OneWeather)"
    
    async def get_forecast(self, latitude: float, longitude: float) -> List[ForecastPoint]:
        """Get forecast from NOAA Weather.gov"""
        try:
            # First, get grid point
            points_url = f"{self.base_url}/points/{latitude},{longitude}"
            
            async with httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": self.user_agent}
            ) as client:
                # Get grid point
                points_response = await client.get(points_url)
                points_response.raise_for_status()
                points_data = points_response.json()
                
                # Get forecast from grid point
                forecast_url = points_data["properties"]["forecastHourly"]
                forecast_response = await client.get(forecast_url)
                forecast_response.raise_for_status()
                forecast_data = forecast_response.json()
                
                # Parse forecast
                points = self._parse_weathergov_response(forecast_data, latitude, longitude)
                logger.info(f"Weather.gov: Got {len(points)} forecast points")
                return points
                
        except Exception as e:
            logger.warning(f"Weather.gov failed: {e}")
            return []
    
    def _parse_weathergov_response(self, data: Dict, 
                                  latitude: float, longitude: float) -> List[ForecastPoint]:
        """Parse Weather.gov API response"""
        points = []
        
        if "properties" not in data or "periods" not in data["properties"]:
            return points
        
        periods = data["properties"]["periods"]
        
        for period in periods:
            try:
                timestamp = datetime.fromisoformat(period["startTime"].replace("Z", "+00:00"))
                
                # Parse temperature (convert F to C if needed)
                temp_f = period.get("temperature")
                temperature_c = (temp_f - 32) * 5/9 if temp_f is not None else None
                
                # Parse wind speed (convert mph to m/s if needed)
                wind_speed_str = period.get("windSpeed", "")
                wind_speed_mps = self._parse_wind_speed(wind_speed_str)
                
                # Parse precipitation probability
                precip_prob = period.get("probabilityOfPrecipitation", {}).get("value")
                precipitation_probability = float(precip_prob) / 100 if precip_prob is not None else None
                
                point = ForecastPoint(
                    timestamp=timestamp,
                    temperature_c=temperature_c,
                    precipitation_mm=None,  # Weather.gov doesn't provide amount
                    precipitation_probability=precipitation_probability,
                    wind_speed_mps=wind_speed_mps,
                    wind_direction_deg=None,  # Would need to parse wind direction string
                    humidity_percent=None,  # Not in hourly forecast
                    cloud_cover_percent=None,  # Not in hourly forecast
                    pressure_hpa=None,  # Not in hourly forecast
                    source="noaa_weathergov",
                    latitude=latitude,
                    longitude=longitude
                )
                points.append(point)
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing Weather.gov period: {e}")
                continue
        
        return points
    
    def _parse_wind_speed(self, wind_speed_str: str) -> Optional[float]:
        """Parse wind speed string like '10 mph' or '5 to 10 mph'"""
        try:
            # Extract first number
            import re
            match = re.search(r'(\d+(?:\.\d+)?)', wind_speed_str)
            if match:
                mph = float(match.group(1))
                # Convert mph to m/s
                return mph * 0.44704
        except:
            pass
        return None


class WeatherAPISource(WeatherSource):
    """WeatherAPI.com Free Tier (1M calls/month)"""
    
    def __init__(self):
        super().__init__("weatherapi", cache_ttl=300)
        self.base_url = "http://api.weatherapi.com/v1"
        # Note: Requires free API key from weatherapi.com
    
    async def get_forecast(self, latitude: float, longitude: float) -> List[ForecastPoint]:
        """Get forecast from WeatherAPI.com"""
        # Placeholder - needs API key
        # Free tier: 1M calls/month, 3-day forecast
        logger.info("WeatherAPI.com requires free API key registration")
        return []


class OpenWeatherMapSource(WeatherSource):
    """OpenWeatherMap Free Tier (1K calls/day)"""
    
    def __init__(self):
        super().__init__("openweathermap", cache_ttl=300)
        self.base_url = "https://api.openweathermap.org/data/2.5"
        # Note: Requires free API key from openweathermap.org
    
    async def get_forecast(self, latitude: float, longitude: float) -> List[ForecastPoint]:
        """Get forecast from OpenWeatherMap"""
        # Placeholder - needs API key
        # Free tier: 1,000 calls/day, current weather + 5-day forecast
        logger.info("OpenWeatherMap requires free API key registration")
        return []


class MeteomaticsFreeSource(WeatherSource):
    """Meteomatics Free Tier API"""
    
    def __init__(self):
        super().__init__("meteomatics_free", cache_ttl=300)
        self.base_url = "https://api.meteomatics.com"
        # Note: Requires registration for free API key
    
    async def get_forecast(self, latitude: float, longitude: float) -> List[ForecastPoint]:
        """Get forecast from Meteomatics (placeholder - needs API key)"""
        logger.info("Meteomatics requires API key registration")
        return []


class WeatherSourceManager:
    """Manager for all weather data sources"""
    
    def __init__(self):
        self.sources = {
            "openmeteo": OpenMeteoSource(),
            "noaa_weathergov": NOAAWeatherGovSource(),
            # "weatherapi": WeatherAPISource(),  # Needs free API key
            # "openweathermap": OpenWeatherMapSource(),  # Needs free API key
            # "meteomatics": MeteomaticsFreeSource(),  # Needs API key
        }
        
        # Track which sources are actually working (have API keys)
        self.active_sources = ["openmeteo", "noaa_weathergov"]
    
    async def get_all_forecasts(self, latitude: float, longitude: float) -> Dict[str, List[ForecastPoint]]:
        """Get forecasts from all available sources"""
        results = {}
        
        # Run all sources concurrently
        tasks = []
        for name, source in self.sources.items():
            task = asyncio.create_task(
                self._safe_get_forecast(source, latitude, longitude, name)
            )
            tasks.append((name, task))
        
        # Collect results
        for name, task in tasks:
            try:
                results[name] = await task
            except Exception as e:
                logger.error(f"Source {name} failed: {e}")
                results[name] = []
        
        return results
    
    async def _safe_get_forecast(self, source: WeatherSource, 
                                latitude: float, longitude: float, 
                                name: str) -> List[ForecastPoint]:
        """Safely get forecast with timeout"""
        try:
            return await asyncio.wait_for(
                source.get_forecast(latitude, longitude),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Source {name} timed out")
            return []
        except Exception as e:
            logger.warning(f"Source {name} error: {e}")
            return []
    
    def blend_forecasts(self, forecasts: Dict[str, List[ForecastPoint]]) -> List[ForecastPoint]:
        """Simple average blending of all forecasts"""
        if not forecasts:
            return []
        
        # Group by timestamp
        from collections import defaultdict
        timestamp_groups = defaultdict(list)
        
        # Collect all points by timestamp
        for source_name, points in forecasts.items():
            for point in points:
                key = point.timestamp.isoformat()
                timestamp_groups[key].append((source_name, point))
        
        # Average each timestamp
        blended_points = []
        for timestamp_str, source_points in timestamp_groups.items():
            if len(source_points) < 1:
                continue
            
            # Use first point as template
            _, first_point = source_points[0]
            timestamp = first_point.timestamp
            latitude = first_point.latitude
            longitude = first_point.longitude
            
            # Calculate averages
            temp_sum = count = 0
            precip_sum = precip_count = 0
            precip_prob_sum = precip_prob_count = 0
            wind_speed_sum = wind_speed_count = 0
            humidity_sum = humidity_count = 0
            cloud_sum = cloud_count = 0
            pressure_sum = pressure_count = 0
            
            for source_name, point in source_points:
                if point.temperature_c is not None:
                    temp_sum += point.temperature_c
                    count += 1
                if point.precipitation_mm is not None:
                    precip_sum += point.precipitation_mm
                    precip_count += 1
                if point.precipitation_probability is not None:
                    precip_prob_sum += point.precipitation_probability
                    precip_prob_count += 1
                if point.wind_speed_mps is not None:
                    wind_speed_sum += point.wind_speed_mps
                    wind_speed_count += 1
                if point.humidity_percent is not None:
                    humidity_sum += point.humidity_percent
                    humidity_count += 1
                if point.cloud_cover_percent is not None:
                    cloud_sum += point.cloud_cover_percent
                    cloud_count += 1
                if point.pressure_hpa is not None:
                    pressure_sum += point.pressure_hpa
                    pressure_count += 1
            
            # Create blended point
            blended_point = ForecastPoint(
                timestamp=timestamp,
                temperature_c=temp_sum / count if count > 0 else None,
                precipitation_mm=precip_sum / precip_count if precip_count > 0 else None,
                precipitation_probability=precip_prob_sum / precip_prob_count if precip_prob_count > 0 else None,
                wind_speed_mps=wind_speed_sum / wind_speed_count if wind_speed_count > 0 else None,
                wind_direction_deg=first_point.wind_direction_deg,  # Can't average direction
                humidity_percent=humidity_sum / humidity_count if humidity_count > 0 else None,
                cloud_cover_percent=cloud_sum / cloud_count if cloud_count > 0 else None,
                pressure_hpa=pressure_sum / pressure_count if pressure_count > 0 else None,
                source="blended",
                latitude=latitude,
                longitude=longitude
            )
            
            blended_points.append(blended_point)
        
        # Sort by timestamp
        blended_points.sort(key=lambda x: x.timestamp)
        
        logger.info(f"Blended {len(blended_points)} forecast points from {len(forecasts)} sources")
        return blended_points


# Global instance
weather_manager = WeatherSourceManager()