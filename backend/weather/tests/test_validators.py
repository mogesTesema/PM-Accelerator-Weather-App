"""
Tests for weather.validators — validate_date_range edge cases.
"""

import pytest
from datetime import date, timedelta
from django.utils import timezone
from rest_framework import serializers

from weather.validators import validate_date_range


class TestValidateDateRange:
    """Tests for the validate_date_range function."""

    def test_valid_range(self):
        """No exception for a valid, short range."""
        today = timezone.now().date()
        validate_date_range(today, today + timedelta(days=3))

    def test_same_day(self):
        """start == end should be valid."""
        today = timezone.now().date()
        validate_date_range(today, today)

    def test_start_after_end(self):
        today = timezone.now().date()
        with pytest.raises(serializers.ValidationError):
            validate_date_range(today + timedelta(days=3), today)

    def test_exceeds_365_days(self):
        today = timezone.now().date()
        with pytest.raises(serializers.ValidationError):
            validate_date_range(today - timedelta(days=200), today + timedelta(days=200))

    def test_exceeds_5_day_future(self):
        today = timezone.now().date()
        with pytest.raises(serializers.ValidationError):
            validate_date_range(today, today + timedelta(days=6))

    def test_boundary_exactly_5_days_future(self):
        """date_end == today + 5 should pass (edge case)."""
        today = timezone.now().date()
        validate_date_range(today, today + timedelta(days=5))
