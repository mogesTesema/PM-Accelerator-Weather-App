from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers


def validate_date_range(date_start, date_end):
    """Validate that date_start <= date_end and range is reasonable."""
    if date_start > date_end:
        raise serializers.ValidationError(
            {"date_range": "date_start must be on or before date_end."}
        )

    max_range = timedelta(days=365)
    if (date_end - date_start) > max_range:
        raise serializers.ValidationError(
            {"date_range": "Date range cannot exceed 365 days."}
        )

    max_future = timezone.now().date() + timedelta(days=5)
    if date_end > max_future:
        raise serializers.ValidationError(
            {"date_range": "date_end cannot be more than 5 days in the future."}
        )
