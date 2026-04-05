"""
Unit tests for weather.services — geocoding, openweather, exports, youtube, google_maps.

All HTTP calls are mocked. No real API calls are made.
"""

import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from weather.services import exports, geocoding, google_maps, openweather, youtube

# ─── geocoding ─────────────────────────────────────────────

class TestIsZipCode:

    def test_us_zip(self):
        assert geocoding._is_probable_zip_code("90210") is True

    def test_us_zip_plus_four(self):
        assert geocoding._is_probable_zip_code("90210-1234") is True

    def test_uk_postal(self):
        assert geocoding._is_probable_zip_code("SW1A 1AA") is True

    def test_canada_postal(self):
        assert geocoding._is_probable_zip_code("K1A 0B1") is True

    def test_city_name_not_zip(self):
        assert geocoding._is_probable_zip_code("London") is False

    def test_empty_string(self):
        assert geocoding._is_probable_zip_code("") is False


class TestClassifyType:

    def test_city(self):
        assert geocoding._classify_type({"class": "place", "type": "city"}) == "city"

    def test_postcode(self):
        assert geocoding._classify_type({"type": "postcode"}) == "zip"

    def test_landmark(self):
        assert geocoding._classify_type({"class": "tourism", "type": "attraction"}) == "landmark"

    def test_other(self):
        assert geocoding._classify_type({"class": "highway", "type": "residential"}) == "other"


class TestResolveLocation:

    @pytest.mark.asyncio
    @patch("weather.services.geocoding.httpx.AsyncClient")
    @patch("weather.services.geocoding.settings.LOCATIONIQ_API_KEY", "fake-key")
    async def test_success(self, mock_client_class):
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "lat": "51.5074",
                "lon": "-0.1278",
                "display_name": "London, UK",
                "type": "city",
                "class": "place",
                "address": {"country": "United Kingdom"},
            }
        ]
        mock_client.get.return_value = mock_response

        result = await geocoding.resolve_location("London")
        assert result is not None
        assert result["lat"] == 51.5074
        assert result["lon"] == -0.1278
        assert result["name"] == "London, UK"

    @pytest.mark.asyncio
    @patch("weather.services.geocoding.httpx.AsyncClient")
    @patch("weather.services.geocoding.settings.LOCATIONIQ_API_KEY", "fake-key")
    async def test_zip_uses_postalcode_param(self, mock_client_class):
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "lat": "34.0901",
                "lon": "-118.4065",
                "display_name": "Beverly Hills, CA",
                "type": "postcode",
                "class": "place",
                "address": {"country": "US"},
            }
        ]
        mock_client.get.return_value = mock_response

        await geocoding.resolve_location("90210")
        
        # Verify postalcode param was used
        call_kwargs = mock_client.get.call_args
        assert "postalcode" in call_kwargs.kwargs.get("params", call_kwargs[1].get("params", {}))

    @pytest.mark.asyncio
    @patch("weather.services.geocoding.settings")
    async def test_no_api_key(self, mock_settings):
        mock_settings.LOCATIONIQ_API_KEY = ""
        result = await geocoding.resolve_location("London")
        assert result is None


# ─── openweather ───────────────────────────────────────────

class TestParseWeather:

    def test_with_dt_timestamp(self):
        data = {
            "dt": 1712188800,  # 2024-04-04 00:00:00 UTC
            "main": {"temp": 15.0, "feels_like": 13.0, "humidity": 55},
            "wind": {"speed": 3.0},
            "weather": [{"description": "clear sky", "icon": "01d"}],
        }
        result = openweather._parse_weather(data)
        assert result is not None
        assert result["temperature"] == 15.0
        assert isinstance(result["date"], date)

    def test_with_dt_txt(self):
        data = {
            "dt_txt": "2026-04-04 12:00:00",
            "main": {"temp": 20.0, "feels_like": 19.0, "humidity": 60},
            "wind": {"speed": 2.5},
            "weather": [{"description": "scattered clouds", "icon": "03d"}],
        }
        result = openweather._parse_weather(data)
        assert result is not None
        assert result["date"] == date(2026, 4, 4)

    def test_empty_data(self):
        result = openweather._parse_weather({})
        # Should not crash; returns dict with None values
        assert result is not None


# ─── exports ───────────────────────────────────────────────

SAMPLE_RECORDS = [
    {
        "location": "London",
        "latitude": 51.5,
        "longitude": -0.12,
        "date": "2026-04-04",
        "temperature": 15.0,
        "feels_like": 13.0,
        "humidity": 55,
        "wind_speed": 3.0,
        "description": "clear sky",
    }
]


class TestExports:

    def test_export_json(self):
        result = exports.export_json(SAMPLE_RECORDS)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["location"] == "London"

    def test_export_csv(self):
        result = exports.export_csv(SAMPLE_RECORDS)
        lines = result.strip().split("\n")
        assert len(lines) == 2  # header + 1 row
        assert "location" in lines[0]

    def test_export_xml(self):
        result = exports.export_xml(SAMPLE_RECORDS)
        assert "<WeatherRecords>" in result
        assert "<WeatherRecord>" in result
        assert "<location>London</location>" in result

    def test_export_md(self):
        result = exports.export_md(SAMPLE_RECORDS)
        assert "# Weather Data Export" in result
        assert "| location" in result
        assert "London" in result

    def test_export_pdf(self):
        result = exports.export_pdf(SAMPLE_RECORDS)
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_export_json_empty(self):
        result = exports.export_json([])
        assert json.loads(result) == []

    def test_export_csv_empty(self):
        result = exports.export_csv([])
        assert result == ""

    def test_export_md_empty(self):
        result = exports.export_md([])
        assert "No records found" in result

    def test_export_pdf_empty(self):
        result = exports.export_pdf([])
        assert isinstance(result, bytes)


# ─── youtube ───────────────────────────────────────────────

class TestYouTubeService:

    @patch("weather.services.youtube.settings")
    def test_no_api_key(self, mock_settings):
        mock_settings.YOUTUBE_API_KEY = ""
        result = youtube.search_videos("London")
        assert result == []

    @patch("weather.services.youtube.requests.get")
    @patch("weather.services.youtube.settings.YOUTUBE_API_KEY", "fake-key")
    def test_success(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "items": [
                    {
                        "id": {"videoId": "abc123"},
                        "snippet": {
                            "title": "London Trip",
                            "thumbnails": {"high": {"url": "http://thumb.jpg"}},
                            "channelTitle": "Travel Channel",
                        },
                    }
                ]
            },
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = youtube.search_videos("London")
        assert len(result) == 1
        assert result[0]["video_id"] == "abc123"
        assert result[0]["title"] == "London Trip"


# ─── google_maps ───────────────────────────────────────────

class TestGoogleMapsService:

    @patch("weather.services.google_maps.settings")
    def test_no_keys(self, mock_settings):
        mock_settings.GOOGLE_MAPS_API_KEY = ""
        mock_settings.STADIA_MAPS_API_KEY = ""
        type(mock_settings).STADIA_MAPS_API_KEY = ""
        result = google_maps.get_map_data(51.5, -0.12, "London")
        assert result["directions_url"] != ""
        assert result["embed_url"] == ""
        assert result["static_map_url"] == ""

    @patch("weather.services.google_maps.settings")
    def test_stadia_fallback(self, mock_settings):
        mock_settings.GOOGLE_MAPS_API_KEY = ""
        mock_settings.STADIA_MAPS_API_KEY = "test-stadia-key"
        # Make getattr return the stadia key
        result = google_maps.get_map_data(51.5, -0.12, "London")
        # When GOOGLE_MAPS_API_KEY is empty (falsy), it should check STADIA
        # The mock settings should work with getattr
        assert "directions_url" in result
