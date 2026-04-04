from rest_framework import serializers

from .models import Location, WeatherRecord


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "name",
            "latitude",
            "longitude",
            "country",
            "location_type",
            "resolved_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WeatherRecordSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source="location",
        write_only=True,
    )

    class Meta:
        model = WeatherRecord
        fields = [
            "id",
            "location",
            "location_id",
            "date",
            "date_range_start",
            "date_range_end",
            "temperature",
            "feels_like",
            "humidity",
            "wind_speed",
            "description",
            "icon",
            "raw_response",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class WeatherCreateSerializer(serializers.Serializer):
    """
    Accepts a location query + date range, resolves the location,
    fetches weather data, and creates records.
    """

    location_query = serializers.CharField(
        max_length=255,
        help_text="City name, zip code, landmark, or coordinates",
    )
    date_start = serializers.DateField(
        help_text="Start date for weather data (YYYY-MM-DD)",
    )
    date_end = serializers.DateField(
        help_text="End date for weather data (YYYY-MM-DD)",
    )

    def validate(self, data):
        from .validators import validate_date_range

        validate_date_range(data["date_start"], data["date_end"])
        return data
