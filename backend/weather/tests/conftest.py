"""
Factory-boy factories for the weather app models.
Used by all weather test modules.
"""

import factory
from datetime import date as _date

from weather.models import Location, WeatherRecord


class LocationFactory(factory.django.DjangoModelFactory):
    """Factory for creating Location instances."""

    class Meta:
        model = Location

    name = factory.Sequence(lambda n: f"Test City {n}")
    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")
    country = "US"
    location_type = "city"
    resolved_by = "locationiq"


class WeatherRecordFactory(factory.django.DjangoModelFactory):
    """Factory for creating WeatherRecord instances."""

    class Meta:
        model = WeatherRecord

    location = factory.SubFactory(LocationFactory)
    date = factory.LazyFunction(lambda: _date.today())
    date_range_start = factory.LazyFunction(lambda: _date.today())
    date_range_end = factory.LazyFunction(lambda: _date.today())
    temperature = 22.5
    feels_like = 21.0
    humidity = 65
    wind_speed = 3.5
    description = "clear sky"
    icon = "01d"
    raw_response = {"source": "test"}

