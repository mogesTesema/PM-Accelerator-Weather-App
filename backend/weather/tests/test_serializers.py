"""
Tests for weather.serializers — LocationSerializer, WeatherRecordSerializer,
WeatherCreateSerializer.
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone

from weather.serializers import (
    LocationSerializer,
    WeatherRecordSerializer,
    WeatherCreateSerializer,
)
from weather.tests.conftest import LocationFactory, WeatherRecordFactory


@pytest.mark.django_db
class TestLocationSerializer:
    """Tests for LocationSerializer."""

    def test_serializer_fields(self):
        loc = LocationFactory()
        data = LocationSerializer(loc).data
        expected_fields = {
            "id", "name", "latitude", "longitude",
            "country", "location_type", "resolved_by",
            "created_at", "updated_at",
        }
        assert set(data.keys()) == expected_fields

    def test_read_only_fields(self):
        """id, created_at, updated_at should be ignored on input."""
        input_data = {
            "id": 999,
            "name": "Test",
            "latitude": 1.0,
            "longitude": 2.0,
            "created_at": "2020-01-01T00:00:00Z",
        }
        serializer = LocationSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors
        # id should not be in validated_data
        assert "id" not in serializer.validated_data
        assert "created_at" not in serializer.validated_data


@pytest.mark.django_db
class TestWeatherRecordSerializer:
    """Tests for WeatherRecordSerializer."""

    def test_nested_location_on_read(self):
        record = WeatherRecordFactory()
        data = WeatherRecordSerializer(record).data
        assert isinstance(data["location"], dict)
        assert "name" in data["location"]
        assert "latitude" in data["location"]

    def test_location_id_on_write(self):
        loc = LocationFactory()
        input_data = {
            "location_id": loc.id,
            "date": "2026-04-04",
            "temperature": 25.0,
        }
        serializer = WeatherRecordSerializer(data=input_data)
        assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
class TestWeatherCreateSerializer:
    """Tests for WeatherCreateSerializer (validation logic)."""

    def test_valid_data(self):
        today = timezone.now().date()
        data = {
            "location_query": "London",
            "date_start": today.isoformat(),
            "date_end": (today + timedelta(days=3)).isoformat(),
        }
        serializer = WeatherCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_invalid_start_after_end(self):
        today = timezone.now().date()
        data = {
            "location_query": "London",
            "date_start": (today + timedelta(days=3)).isoformat(),
            "date_end": today.isoformat(),
        }
        serializer = WeatherCreateSerializer(data=data)
        assert not serializer.is_valid()

    def test_invalid_future_exceeds_5_days(self):
        today = timezone.now().date()
        data = {
            "location_query": "London",
            "date_start": today.isoformat(),
            "date_end": (today + timedelta(days=10)).isoformat(),
        }
        serializer = WeatherCreateSerializer(data=data)
        assert not serializer.is_valid()
