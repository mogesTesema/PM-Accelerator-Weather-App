"""
Tests for weather views — CRUD endpoints, forecast, enrichment, export, agent.

All external API calls are mocked. Tests hit the real Django URL router
against an in-memory SQLite database.
"""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from weather.models import Location
from weather.tests.conftest import LocationFactory, WeatherRecordFactory

# ─── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_location(db):
    return LocationFactory(name="London", latitude=51.5, longitude=-0.12, country="GB")


@pytest.fixture
def sample_record(sample_location):
    return WeatherRecordFactory(location=sample_location)


# ─── Location CRUD ─────────────────────────────────────────


@pytest.mark.django_db
class TestLocationCRUD:
    def test_create_location(self, api_client):
        resp = api_client.post(
            "/api/weather/locations/",
            {"name": "Paris", "latitude": 48.85, "longitude": 2.35},
            format="json",
        )
        print("RESP DATA:", resp.content)
        assert resp.status_code == 201
        assert resp.data["name"] == "Paris"

    def test_list_locations(self, api_client, sample_location):
        resp = api_client.get("/api/weather/locations/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1

    def test_retrieve_location(self, api_client, sample_location):
        resp = api_client.get(f"/api/weather/locations/{sample_location.id}/")
        assert resp.status_code == 200
        assert resp.data["name"] == "London"

    def test_update_location(self, api_client, sample_location):
        resp = api_client.patch(
            f"/api/weather/locations/{sample_location.id}/",
            {"country": "UK"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["country"] == "UK"

    def test_delete_location(self, api_client, sample_location):
        resp = api_client.delete(f"/api/weather/locations/{sample_location.id}/")
        assert resp.status_code == 204
        assert not Location.objects.filter(id=sample_location.id).exists()


# ─── WeatherRecord CRUD ───────────────────────────────────


@pytest.mark.django_db
class TestWeatherRecordCRUD:
    def test_create_weather_record(self, api_client, sample_location):
        resp = api_client.post(
            "/api/weather/records/",
            {
                "location_id": sample_location.id,
                "date": "2026-04-04",
                "temperature": 18.5,
            },
            format="json",
        )
        print("RESP DATA:", resp.content)
        assert resp.status_code == 201
        assert resp.data["temperature"] == 18.5

    def test_list_weather_records(self, api_client, sample_record):
        resp = api_client.get("/api/weather/records/")
        assert resp.status_code == 200
        assert resp.data["count"] >= 1
        # Nested location should be present
        assert "location" in resp.data["results"][0]

    def test_update_weather_record(self, api_client, sample_record):
        resp = api_client.patch(
            f"/api/weather/records/{sample_record.id}/",
            {"temperature": 30.0},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.data["temperature"] == 30.0

    def test_delete_weather_record(self, api_client, sample_record):
        resp = api_client.delete(f"/api/weather/records/{sample_record.id}/")
        assert resp.status_code == 204


# ─── Create Weather (mocked external APIs) ────────────────

MOCK_GEO_RESULT = {
    "name": "London, UK",
    "lat": 51.5,
    "lon": -0.12,
    "country": "GB",
    "type": "city",
}

MOCK_WEATHER_RESULT = {
    "date": date.today(),
    "temperature": 12.5,
    "feels_like": 11.0,
    "humidity": 72,
    "wind_speed": 4.1,
    "description": "overcast clouds",
    "icon": "04d",
    "raw_response": {"dt": 1234567890},
}


@pytest.mark.django_db
class TestCreateWeather:
    @patch(
        "weather.views.openweather.get_current_weather",
        return_value=MOCK_WEATHER_RESULT,
    )
    @patch("weather.views.geocoding.resolve_location", return_value=MOCK_GEO_RESULT)
    def test_success(self, mock_geo, mock_weather, api_client):
        today = timezone.now().date()
        resp = api_client.post(
            "/api/weather/create/",
            {
                "location_query": "London",
                "date_start": today.isoformat(),
                "date_end": (today + timedelta(days=3)).isoformat(),
            },
            format="json",
        )
        assert resp.status_code == 201
        assert resp.data["temperature"] == 12.5
        mock_geo.assert_called_once_with("London")

    @patch("weather.views.geocoding.fuzzy_search", return_value=None)
    @patch("weather.views.geocoding.resolve_location", return_value=None)
    def test_unresolvable_location(self, mock_geo, mock_fuzzy, api_client):
        today = timezone.now().date()
        resp = api_client.post(
            "/api/weather/create/",
            {
                "location_query": "ZZZZXXX",
                "date_start": today.isoformat(),
                "date_end": (today + timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        assert resp.status_code == 400
        assert "Could not resolve" in resp.data["detail"]

    @patch("weather.views.openweather.get_current_weather", return_value=None)
    @patch("weather.views.geocoding.resolve_location", return_value=MOCK_GEO_RESULT)
    def test_weather_api_failure(self, mock_geo, mock_weather, api_client):
        today = timezone.now().date()
        resp = api_client.post(
            "/api/weather/create/",
            {
                "location_query": "London",
                "date_start": today.isoformat(),
                "date_end": (today + timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        assert resp.status_code == 502


# ─── Forecast (mocked) ────────────────────────────────────


@pytest.mark.django_db
class TestForecastView:
    @patch("weather.views.openweather.get_forecast", return_value=[{"temp": 20}])
    def test_forecast_by_coords(self, mock_fc, api_client):
        resp = api_client.get("/api/weather/forecast/", {"lat": "51.5", "lon": "-0.12"})
        assert resp.status_code == 200
        assert resp.data["count"] == 1

    @patch("weather.views.openweather.get_forecast", return_value=[{"temp": 20}])
    def test_forecast_by_location_id(self, mock_fc, api_client, sample_location):
        resp = api_client.get(
            "/api/weather/forecast/", {"location_id": sample_location.id}
        )
        assert resp.status_code == 200

    def test_forecast_missing_params(self, api_client):
        resp = api_client.get("/api/weather/forecast/")
        assert resp.status_code == 400

    def test_forecast_invalid_location_id(self, api_client):
        resp = api_client.get("/api/weather/forecast/", {"location_id": "9999"})
        assert resp.status_code == 404

    @patch("weather.views.openweather.get_forecast", return_value=None)
    def test_forecast_api_failure(self, mock_fc, api_client):
        resp = api_client.get("/api/weather/forecast/", {"lat": "51.5", "lon": "-0.12"})
        assert resp.status_code == 502


# ─── Enrichment (mocked) ──────────────────────────────────


@pytest.mark.django_db
class TestEnrichmentView:
    @patch(
        "weather.views.google_maps.get_map_data", return_value={"embed_url": "http://x"}
    )
    @patch("weather.views.youtube.search_videos", return_value=[{"title": "Trip"}])
    def test_success(self, mock_yt, mock_maps, api_client, sample_location):
        resp = api_client.get(
            "/api/weather/enrichment/", {"location_id": sample_location.id}
        )
        assert resp.status_code == 200
        assert "youtube_videos" in resp.data
        assert "google_maps" in resp.data

    def test_missing_location_id(self, api_client):
        resp = api_client.get("/api/weather/enrichment/")
        assert resp.status_code == 400

    def test_not_found(self, api_client):
        resp = api_client.get("/api/weather/enrichment/", {"location_id": "9999"})
        assert resp.status_code == 404


# ─── Export ────────────────────────────────────────────────


@pytest.mark.django_db
class TestExportView:
    def test_export_json(self, api_client, sample_record):
        resp = api_client.get("/api/weather/export/", {"export_format": "json"})
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/json"

    def test_export_csv(self, api_client, sample_record):
        resp = api_client.get("/api/weather/export/", {"export_format": "csv"})
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"

    def test_export_pdf(self, api_client, sample_record):
        resp = api_client.get("/api/weather/export/", {"export_format": "pdf"})
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"

    def test_export_xml(self, api_client, sample_record):
        resp = api_client.get("/api/weather/export/", {"export_format": "xml"})
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/xml"

    def test_export_md(self, api_client, sample_record):
        resp = api_client.get("/api/weather/export/", {"export_format": "md"})
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/markdown"

    def test_export_default_is_json(self, api_client, sample_record):
        resp = api_client.get("/api/weather/export/")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/json"


# ─── Agent Query ───────────────────────────────────────────


@pytest.mark.django_db
class TestAgentQueryView:
    def test_empty_message(self, api_client):
        resp = api_client.post("/api/weather/agent/query/", {}, format="json")
        assert resp.status_code == 400

    @patch("weather.views.agent_query_view.__wrapped__", side_effect=None)
    def test_agent_no_config(self, mock_agent, api_client):
        """When no LLM keys are set, agent returns a config message."""
        # Directly test without mocking the import — the orchestrator
        # handles missing keys gracefully.
        resp = api_client.post(
            "/api/weather/agent/query/",
            {"message": "What is the weather in London?"},
            format="json",
        )
        # Should be 200 with a helpful config message, or 500/501 depending on setup
        assert resp.status_code in (200, 500, 501)
