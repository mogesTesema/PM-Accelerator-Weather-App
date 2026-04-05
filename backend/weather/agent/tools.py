"""
Tool functions for the weather agent.
The agent calls these to interact with services and the database.
"""

from asgiref.sync import async_to_sync

from weather.models import WeatherRecord
from weather.services import geocoding, openweather, youtube


def get_weather(location_query: str) -> dict:
    """
    Get current weather for a location.

    Args:
        location_query: A city name, zip code, landmark, or coordinates.

    Returns:
        Weather data dict or error message.
    """
    geo = async_to_sync(geocoding.resolve_location)(location_query)
    if not geo:
        geo = async_to_sync(geocoding.fuzzy_search)(location_query)
    if not geo:
        return {"error": f"Could not resolve location: '{location_query}'"}

    weather = async_to_sync(openweather.get_current_weather)(geo["lat"], geo["lon"])
    if not weather:
        return {"error": "Failed to fetch weather data."}

    return {
        "location": geo["name"],
        "latitude": geo["lat"],
        "longitude": geo["lon"],
        **weather,
    }


def get_forecast(location_query: str) -> dict:
    """
    Get 5-day forecast for a location.

    Args:
        location_query: A city name, zip code, landmark, or coordinates.

    Returns:
        Forecast data or error message.
    """
    geo = async_to_sync(geocoding.resolve_location)(location_query)
    if not geo:
        return {"error": f"Could not resolve location: '{location_query}'"}

    forecast = async_to_sync(openweather.get_forecast)(geo["lat"], geo["lon"])
    if not forecast:
        return {"error": "Failed to fetch forecast data."}

    return {
        "location": geo["name"],
        "forecast_count": len(forecast),
        "forecast": forecast,
    }


def search_location(query: str) -> dict:
    """
    Resolve a location query to coordinates and details.

    Args:
        query: A city name, zip code, landmark, or coordinates.

    Returns:
        Location details or error message.
    """
    geo = async_to_sync(geocoding.resolve_location)(query)
    if not geo:
        geo = async_to_sync(geocoding.fuzzy_search)(query)
    if not geo:
        return {"error": f"Could not resolve location: '{query}'"}

    return geo


def get_videos(location_name: str) -> dict:
    """
    Find YouTube travel videos for a location.

    Args:
        location_name: Name of the location to search for.

    Returns:
        List of video results.
    """
    videos = async_to_sync(youtube.search_videos)(location_name)
    return {"location": location_name, "video_count": len(videos), "videos": videos}


def query_history(location_name: str = "", limit: int = 10) -> dict:
    """
    Query previously stored weather records from the database.

    Args:
        location_name: Optional filter by location name.
        limit: Maximum number of records to return (default 10).

    Returns:
        List of stored weather records.
    """
    qs = WeatherRecord.objects.select_related("location").order_by("-created_at")

    if location_name:
        qs = qs.filter(location__name__icontains=location_name)

    records = []
    for wr in qs[:limit]:
        records.append(
            {
                "location": wr.location.name,
                "date": wr.date.isoformat(),
                "temperature": wr.temperature,
                "humidity": wr.humidity,
                "wind_speed": wr.wind_speed,
                "description": wr.description,
            }
        )

    return {"count": len(records), "records": records}
