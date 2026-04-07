"""
Tests for weather.models — Location and WeatherRecord.
"""

import pytest

from weather.models import Location, WeatherRecord
from weather.tests.conftest import LocationFactory, WeatherRecordFactory


@pytest.mark.django_db
class TestLocationModel:
    """Tests for the Location model."""

    def test_str_representation(self):
        loc = LocationFactory(name=" Miami, Florida", latitude=9.02, longitude=38.75)
        assert str(loc) == " Miami, Florida (9.02, 38.75)"

    def test_default_location_type(self):
        LocationFactory(location_type="")
        # Empty string is stored; default via factory is "city"
        # Test the model-level default using direct creation
        loc2 = Location.objects.create(name="X", latitude=0, longitude=0)
        assert loc2.location_type == "other"

    def test_default_resolved_by(self):
        loc = Location.objects.create(name="X", latitude=0, longitude=0)
        assert loc.resolved_by == "user_input"

    def test_ordering(self):
        LocationFactory(name="First")
        LocationFactory(name="Second")
        locations = list(Location.objects.all())
        # -created_at means newest first
        assert locations[0].name == "Second"
        assert locations[1].name == "First"


@pytest.mark.django_db
class TestWeatherRecordModel:
    """Tests for the WeatherRecord model."""

    def test_str_representation(self):
        record = WeatherRecordFactory(temperature=15.0)
        expected = f"{record.location.name} — {record.date} — 15.0°C"
        assert str(record) == expected

    def test_fk_cascade_delete(self):
        record = WeatherRecordFactory()
        loc_id = record.location.id
        Location.objects.filter(id=loc_id).delete()
        assert WeatherRecord.objects.filter(id=record.id).exists() is False

    def test_nullable_fields(self):
        loc = LocationFactory()
        record = WeatherRecord.objects.create(
            location=loc,
            date="2026-04-04",
            temperature=20.0,
            # All optional fields omitted
        )
        assert record.feels_like is None
        assert record.humidity is None
        assert record.wind_speed is None
