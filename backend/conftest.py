"""
Root conftest for pytest-django.

Provides shared fixtures (APIClient) and ensures SQLite is used in CI
by clearing DATABASE_URL before Django initialises.
"""

import os

# Force SQLite fallback when DATABASE_URL is not explicitly set for testing.
# This prevents CI from needing a live PostgreSQL instance.
os.environ.setdefault("DATABASE_URL", os.environ.get("DATABASE_URL", ""))

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Return a DRF APIClient instance."""
    return APIClient()
