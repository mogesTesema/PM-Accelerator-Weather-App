"""
Tests for core.exceptions — custom DRF exception handler.
"""

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestCustomExceptionHandler:
    def test_404_returns_error_envelope(self):
        """A 404 from DRF should be wrapped in {error, detail, status_code}."""
        client = APIClient()
        resp = client.get("/api/weather/locations/99999/")
        assert resp.status_code == 404
        assert resp.data["error"] is True
        assert resp.data["status_code"] == 404

    def test_405_returns_error_envelope(self):
        """A method not allowed should be wrapped."""
        client = APIClient()
        # PATCH on list endpoint is not allowed
        resp = client.patch("/api/weather/locations/", {}, format="json")
        assert resp.status_code == 405
        assert resp.data["error"] is True
        assert resp.data["status_code"] == 405
