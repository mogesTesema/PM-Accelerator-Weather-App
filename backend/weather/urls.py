from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"locations", views.LocationViewSet, basename="location")
router.register(r"records", views.WeatherRecordViewSet, basename="weather-record")

urlpatterns = [
    # CRUD via router
    path("weather/", include(router.urls)),
    # Custom endpoints
    path("weather/create/", views.create_weather, name="weather-create"),
    path("weather/forecast/", views.forecast_view, name="weather-forecast"),
    path("weather/enrichment/", views.enrichment_view, name="weather-enrichment"),
    path("weather/export/", views.export_view, name="weather-export"),
    path("weather/agent/query/", views.agent_query_view, name="agent-query"),
]
