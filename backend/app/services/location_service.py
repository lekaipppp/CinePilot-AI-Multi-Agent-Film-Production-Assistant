"""
LocationService – wraps Google Maps, Places, and OpenWeather APIs.
Agents call this service to gather real-world data for location scouting.
"""

from typing import Any, Dict, List, Optional

import httpx

from app.config.settings import settings


class LocationService:
    """Fetches location and weather data from external APIs."""

    PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    WEATHER_URL = f"{settings.OPENWEATHER_BASE_URL}/weather"
    FORECAST_URL = f"{settings.OPENWEATHER_BASE_URL}/forecast"

    # ------------------------------------------------------------------
    # Google Places / Maps
    # ------------------------------------------------------------------

    async def geocode(self, address: str) -> Optional[Dict[str, Any]]:
        """Convert a human-readable address into lat/lng coordinates."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.GEOCODE_URL,
                params={"address": address, "key": settings.GOOGLE_MAPS_API_KEY},
            )
            data = response.json()
            if data.get("status") == "OK" and data.get("results"):
                return data["results"][0]["geometry"]["location"]
        return None

    async def search_filming_locations(
        self,
        query: str,
        lat: float,
        lng: float,
        radius: int = 5000,
    ) -> List[Dict[str, Any]]:
        """Search for nearby places suitable as filming locations."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.PLACES_NEARBY_URL,
                params={
                    "location": f"{lat},{lng}",
                    "radius": radius,
                    "keyword": query,
                    "key": settings.GOOGLE_PLACES_API_KEY,
                },
            )
        return response.json().get("results", [])

    # ------------------------------------------------------------------
    # OpenWeather
    # ------------------------------------------------------------------

    async def get_current_weather(self, lat: float, lng: float) -> Dict[str, Any]:
        """Fetch current weather conditions at a coordinate."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.WEATHER_URL,
                params={
                    "lat": lat,
                    "lon": lng,
                    "appid": settings.OPENWEATHER_API_KEY,
                    "units": "metric",
                },
            )
        return response.json()

    async def get_forecast(self, lat: float, lng: float, days: int = 5) -> Dict[str, Any]:
        """Fetch a multi-day weather forecast at a coordinate."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.FORECAST_URL,
                params={
                    "lat": lat,
                    "lon": lng,
                    "cnt": days * 8,  # 8 readings/day (3-hour intervals)
                    "appid": settings.OPENWEATHER_API_KEY,
                    "units": "metric",
                },
            )
        return response.json()
