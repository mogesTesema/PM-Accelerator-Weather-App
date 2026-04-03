"""
OpenWeatherMap API client — current weather and 5-day forecast.
"""

import logging
from datetime import datetime, timezone

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.openweathermap.org/data/2.5"


def get_current_weather(lat: float, lon: float) -> dict | None:
    """
    Fetch current weather for given coordinates.
    Returns parsed dict or None on failure.
    """
    api_key = settings.OPEN_WEATHER_API_KEY
    if not api_key:
        logger.warning("OPEN_WEATHER_API_KEY not set.")
        return None

    try:
        response = requests.get(
            f"{BASE_URL}/weather",
            params={
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        return _parse_weather(data)
    except requests.RequestException as e:
        logger.error("OpenWeatherMap current weather request failed: %s", e)
        return None


def get_forecast(lat: float, lon: float) -> list[dict] | None:
    """
    Fetch 5-day / 3-hour forecast for given coordinates.
    Returns list of parsed weather dicts (one per 3-hour slot) or None.
    """
    api_key = settings.OPEN_WEATHER_API_KEY
    if not api_key:
        logger.warning("OPEN_WEATHER_API_KEY not set.")
        return None

    try:
        response = requests.get(
            f"{BASE_URL}/forecast",
            params={
                "lat": lat,
                "lon": lon,
                "appid": api_key,
                "units": "metric",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        forecasts = []
        for item in data.get("list", []):
            parsed = _parse_weather(item)
            if parsed:
                forecasts.append(parsed)

        return forecasts
    except requests.RequestException as e:
        logger.error("OpenWeatherMap forecast request failed: %s", e)
        return None


def _parse_weather(data: dict) -> dict | None:
    """Parse a single weather data point from the API response."""
    try:
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather_list = data.get("weather", [{}])
        weather_info = weather_list[0] if weather_list else {}

        # Handle both current (dt) and forecast (dt_txt) timestamps
        dt = data.get("dt")
        dt_txt = data.get("dt_txt")
        if dt_txt:
            parsed_date = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S").date()
        elif dt:
            parsed_date = datetime.fromtimestamp(dt, tz=timezone.utc).date()
        else:
            parsed_date = datetime.now(tz=timezone.utc).date()

        return {
            "date": parsed_date,
            "temperature": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "description": weather_info.get("description", ""),
            "icon": weather_info.get("icon", ""),
            "raw_response": data,
        }
    except (KeyError, IndexError, ValueError) as e:
        logger.error("Failed to parse weather data: %s", e)
        return None
