"""
Weather app views — CRUD, forecast, enrichment, export, and agent query endpoints.
"""

from datetime import date

from asgiref.sync import async_to_sync
from django.http import HttpResponse, StreamingHttpResponse
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)
from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Location, WeatherRecord
from .serializers import (
    LocationSerializer,
    WeatherCreateSerializer,
    WeatherRecordSerializer,
)
from .services import exports, geocoding, google_maps, openweather, youtube


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
@extend_schema(
    summary="Create Weather Record",
    description="Accepts a location query and date range. Resolves the location natively or via fuzzy matching, fetches real-time weather from OpenWeatherMap, stores the record in the database, and returns the result.",
    request=WeatherCreateSerializer,
    responses={201: WeatherRecordSerializer},
    examples=[
        OpenApiExample(
            "Valid Request",
            value={
                "location_query": "London",
                "date_start": "2026-04-01",
                "date_end": "2026-04-05",
            },
            request_only=True,
        )
    ],
)
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
    geo = async_to_sync(geocoding.resolve_location)(query)
    if not geo:
        # Try fuzzy search as fallback
        geo = async_to_sync(geocoding.fuzzy_search)(query)

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
    weather_data = async_to_sync(openweather.get_current_weather)(
        location.latitude, location.longitude
    )
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
    )

    return Response(
        WeatherRecordSerializer(record).data,
        status=status.HTTP_201_CREATED,
    )


# ──────────────────────────────────────────────
# 5-Day Forecast
# ──────────────────────────────────────────────
@extend_schema(
    summary="Get 5-Day Forecast",
    description="Retrieve a 5-day / 3-hour forecast either by a full `location_query`, existing `location_id` in the database, or raw `lat` & `lon` coordinates.",
    parameters=[
        OpenApiParameter(
            name="location_query",
            description="City name, zip code, landmark, or coordinates",
            required=False,
            type=OpenApiTypes.STR,
        ),
        OpenApiParameter(
            name="location_id",
            description="ID of a stored Location",
            required=False,
            type=OpenApiTypes.INT,
        ),
        OpenApiParameter(
            name="lat", description="Latitude", required=False, type=OpenApiTypes.FLOAT
        ),
        OpenApiParameter(
            name="lon", description="Longitude", required=False, type=OpenApiTypes.FLOAT
        ),
    ],
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["GET"])
def forecast_view(request):
    """
    GET /api/weather/forecast/?location_query=... | location_id=... | lat=...&lon=...
    """
    location_query = request.query_params.get("location_query")
    location_id = request.query_params.get("location_id")
    lat = request.query_params.get("lat")
    lon = request.query_params.get("lon")

    if location_query:
        geo = async_to_sync(geocoding.resolve_location)(location_query)
        if not geo:
            geo = async_to_sync(geocoding.fuzzy_search)(location_query)

        if not geo:
            return Response(
                {
                    "error": True,
                    "detail": f"Could not resolve location: '{location_query}'",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        lat, lon = geo["lat"], geo["lon"]
    elif location_id:
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
            {
                "error": True,
                "detail": "Provide location_query, location_id, or lat & lon.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = async_to_sync(openweather.get_forecast)(lat, lon)
    if data is None:
        return Response(
            {"error": True, "detail": "Failed to fetch forecast from API."},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response({"count": len(data), "forecast": data})


# ──────────────────────────────────────────────
# Enrichment (YouTube + Google Maps)
# ──────────────────────────────────────────────
@extend_schema(
    summary="Get Location Enrichment",
    description="Retrieve YouTube travel/weather videos and Google/Stadia Maps data for a stored location.",
    parameters=[
        OpenApiParameter(
            name="location_id",
            description="ID of a stored Location",
            required=True,
            type=OpenApiTypes.INT,
        ),
    ],
    responses={200: OpenApiTypes.OBJECT},
)
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
@extend_schema(
    summary="Export Weather Data",
    description="Export weather records in various formats (json, csv, pdf, xml, md). Optionally filter by location_id.",
    parameters=[
        OpenApiParameter(
            name="export_format",
            description="Format to export (json, csv, pdf, xml, md)",
            required=False,
            type=OpenApiTypes.STR,
        ),
        OpenApiParameter(
            name="location_id",
            description="Optional Location ID to filter by",
            required=False,
            type=OpenApiTypes.INT,
        ),
    ],
    responses={200: OpenApiTypes.BINARY},
)
@api_view(["GET"])
def export_view(request):
    """
    GET /api/weather/export/?export_format=json|csv|pdf|xml|md[&location_id=...]
    Download weather data in the requested format.
    """
    fmt = request.query_params.get("export_format", "json").lower()
    location_id = request.query_params.get("location_id")

    queryset = WeatherRecord.objects.select_related("location").all()
    if location_id:
        queryset = queryset.filter(location_id=location_id)

    # Use chunked iteration to prevent loading heavy memory models all at once
    queryset = queryset.iterator(chunk_size=1000)

    if fmt == "csv":
        generator = exports.stream_records_to_dicts(queryset)
        response = StreamingHttpResponse(
            exports.stream_csv(generator), content_type="text/csv"
        )
        response["Content-Disposition"] = 'attachment; filename="weather_data.csv"'
        return response

    elif fmt == "json":
        generator = exports.stream_records_to_dicts(queryset)
        response = StreamingHttpResponse(
            exports.stream_json(generator), content_type="application/json"
        )
        response["Content-Disposition"] = 'attachment; filename="weather_data.json"'
        return response

    # For formats that don't natively stream, convert the lazy iterator to a list
    records = exports.records_to_dicts(queryset)

    if fmt == "pdf":
        content = exports.export_pdf(records)
        response = HttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="weather_data.pdf"'
        return response

    elif fmt == "xml":
        content = exports.export_xml(records)
        response = HttpResponse(content, content_type="application/xml")
        response["Content-Disposition"] = 'attachment; filename="weather_data.xml"'
        return response

    elif fmt == "md":
        content = exports.export_md(records)
        response = HttpResponse(content, content_type="text/markdown")
        response["Content-Disposition"] = 'attachment; filename="weather_data.md"'
        return response


# ──────────────────────────────────────────────
# Agent Query
# ──────────────────────────────────────────────
@extend_schema(
    summary="AI Agent Query",
    description="Send a natural language message to the AI orchestrator to autonomously retrieve weather, forecasts, or YouTube videos.",
    request={
        "application/json": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
        }
    },
    examples=[
        OpenApiExample(
            "Valid Request",
            value={"message": "What is the weather in Addis Ababa right now?"},
            request_only=True,
        )
    ],
    responses={200: OpenApiTypes.OBJECT},
)
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
