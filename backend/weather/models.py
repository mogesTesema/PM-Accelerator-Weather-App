from django.db import models

from core.models import TimeStampedModel


class Location(TimeStampedModel):
    """A resolved geographic location."""

    class LocationType(models.TextChoices):
        CITY = "city", "City"
        ZIP = "zip", "Zip Code"
        LANDMARK = "landmark", "Landmark"
        COORDINATES = "coordinates", "GPS Coordinates"
        OTHER = "other", "Other"

    class ResolvedBy(models.TextChoices):
        USER_INPUT = "user_input", "User Input"
        LOCATIONIQ = "locationiq", "LocationIQ"
        PINECONE = "pinecone", "Pinecone (Fuzzy Match)"

    name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    country = models.CharField(max_length=100, blank=True, default="")
    location_type = models.CharField(
        max_length=20,
        choices=LocationType.choices,
        default=LocationType.OTHER,
    )
    resolved_by = models.CharField(
        max_length=20,
        choices=ResolvedBy.choices,
        default=ResolvedBy.USER_INPUT,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"


class WeatherRecord(TimeStampedModel):
    """A stored weather data record for a specific location and date."""

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name="weather_records",
    )
    date = models.DateField()
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)

    # Weather data
    temperature = models.FloatField(help_text="Temperature in Celsius")
    feels_like = models.FloatField(null=True, blank=True)
    humidity = models.IntegerField(null=True, blank=True, help_text="Percentage")
    wind_speed = models.FloatField(null=True, blank=True, help_text="m/s")
    description = models.CharField(max_length=255, blank=True, default="")
    icon = models.CharField(max_length=20, blank=True, default="")

    # (Removed raw_response JSONField to prevent DB inflation)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.location.name} — {self.date} — {self.temperature}°C"
