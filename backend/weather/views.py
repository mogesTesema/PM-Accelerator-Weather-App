"""
Weather app views — CRUD, forecast, enrichment, export, and agent query endpoints.
"""

from datetime import date

from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Location, WeatherRecord
from .serializers import (
    LocationSerializer,
    WeatherRecordSerializer,
    WeatherCreateSerializer,
)
from .services import geocoding, openweather, youtube, google_maps, exports


# ──────────────────────────────────────────────
# Location CRUD
# ──────────────────────────────────────────────
class LocationViewSet(viewsets.ModelViewSet):
    """Full CRUD for locations + resolve endpoint."""

    queryset = Location.objects.all()
    serializer_class = LocationSerializer


# ──────────────────────────────────────────────
# WeatherRecord CRUD
# ──────────────────────────────────────────────
class WeatherRecordViewSet(viewsets.ModelViewSet):
    """Full CRUD for weather records."""

    queryset = WeatherRecord.objects.select_related("location").all()
    serializer_class = WeatherRecordSerializer


# ──────────────────────────────────────────────
# CREATE weather from location query + date range
# ──────────────────────────────────────────────
@api_view(["POST"])
def create_weather(request):
    """
    Accept a location query + date range, resolve the location,
    fetch weather data, store it, and return the created records.
    """
    serializer = WeatherCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    query = serializer.validated_data["location_query"]
    date_start = serializer.validated_data["date_start"]
    date_end = serializer.validated_data["date_end"]

    # 1. Resolve location
    geo = geocoding.resolve_location(query)
    if not geo:
        # Try fuzzy search as fallback
        geo = geocoding.fuzzy_search(query)

    if not geo:
        return Response(
            {"error": True, "detail": f"Could not resolve location: '{query}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 2. Get or create Location
    location, _ = Location.objects.get_or_create(
        name=geo["name"],
        latitude=geo["lat"],
        longitude=geo["lon"],
        defaults={
            "country": geo.get("country", ""),
            "location_type": geo.get("type", "other"),
            "resolved_by": "locationiq",
        },
    )

    # 3. Fetch current weather
    weather_data = openweather.get_current_weather(location.latitude, location.longitude)
    if not weather_data:
        return Response(
            {"error": True, "detail": "Failed to fetch weather data from API."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # 4. Create weather record
    record_date = weather_data["date"]
    if isinstance(record_date, str):
        record_date = date.fromisoformat(record_date)

    record = WeatherRecord.objects.create(
        location=location,
        date=record_date,
        date_range_start=date_start,
        date_range_end=date_end,
        temperature=weather_data["temperature"],
        feels_like=weather_data.get("feels_like"),
        humidity=weather_data.get("humidity"),
        wind_speed=weather_data.get("wind_speed"),
        description=weather_data.get("description", ""),
        icon=weather_data.get("icon", ""),
        raw_response=weather_data.get("raw_response", {}),
    )

    return Response(
        WeatherRecordSerializer(record).data,
        status=status.HTTP_201_CREATED,
    )


# ──────────────────────────────────────────────
# 5-Day Forecast
# ──────────────────────────────────────────────
@api_view(["GET"])
def forecast_view(request):
    """
    GET /api/weather/forecast/?lat=...&lon=...
    or GET /api/weather/forecast/?location_id=...
    """
    location_id = request.query_params.get("location_id")
    lat = request.query_params.get("lat")
    lon = request.query_params.get("lon")

    if location_id:
        try:
            loc = Location.objects.get(pk=location_id)
            lat, lon = loc.latitude, loc.longitude
        except Location.DoesNotExist:
            return Response(
                {"error": True, "detail": "Location not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
    elif lat and lon:
        try:
            lat, lon = float(lat), float(lon)
        except (TypeError, ValueError):
            return Response(
                {"error": True, "detail": "Invalid lat/lon values."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    else:
        return Response(
            {"error": True, "detail": "Provide location_id or lat & lon."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = openweather.get_forecast(lat, lon)
    if data is None:
        return Response(
            {"error": True, "detail": "Failed to fetch forecast from API."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response({"count": len(data), "forecast": data})


# ──────────────────────────────────────────────
# Enrichment (YouTube + Google Maps)
# ──────────────────────────────────────────────
@api_view(["GET"])
def enrichment_view(request):
    """
    GET /api/weather/enrichment/?location_id=...
    Returns YouTube videos and Google Maps data for a location.
    """
    location_id = request.query_params.get("location_id")
    if not location_id:
        return Response(
            {"error": True, "detail": "location_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        loc = Location.objects.get(pk=location_id)
    except Location.DoesNotExist:
        return Response(
            {"error": True, "detail": "Location not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    videos = youtube.search_videos(loc.name)
    maps = google_maps.get_map_data(loc.latitude, loc.longitude, loc.name)

    return Response(
        {
            "location": LocationSerializer(loc).data,
            "youtube_videos": videos,
            "google_maps": maps,
        }
    )


# ──────────────────────────────────────────────
# Data Export
# ──────────────────────────────────────────────
@api_view(["GET"])
def export_view(request):
    """
    GET /api/weather/export/?export_format=json|csv|pdf[&location_id=...]
    Download weather data in the requested format.
    """
    fmt = request.query_params.get("export_format", "json").lower()
    location_id = request.query_params.get("location_id")

    queryset = WeatherRecord.objects.select_related("location").all()
    if location_id:
        queryset = queryset.filter(location_id=location_id)

    records = exports.records_to_dicts(queryset)

    if fmt == "csv":
        content = exports.export_csv(records)
        response = HttpResponse(content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="weather_data.csv"'
        return response

    elif fmt == "pdf":
        content = exports.export_pdf(records)
        response = HttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="weather_data.pdf"'
        return response

    else:  # Default to JSON
        content = exports.export_json(records)
        response = HttpResponse(content, content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="weather_data.json"'
        return response


# ──────────────────────────────────────────────
# Agent Query
# ──────────────────────────────────────────────
@api_view(["POST"])
def agent_query_view(request):
    """
    POST /api/weather/agent/query/
    Accepts natural language input and returns an AI-orchestrated response.
    """
    user_message = request.data.get("message", "")
    if not user_message:
        return Response(
            {"error": True, "detail": "message field is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from .agent.orchestrator import run_agent

        result = run_agent(user_message)
        return Response({"response": result})
    except ImportError:
        return Response(
            {"error": True, "detail": "Agent module not available."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
    except Exception as e:
        return Response(
            {"error": True, "detail": f"Agent error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
