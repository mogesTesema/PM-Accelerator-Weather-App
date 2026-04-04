from django.contrib import admin

from .models import Location, WeatherRecord


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "latitude", "longitude", "country", "location_type", "created_at"]
    list_filter = ["location_type", "resolved_by"]
    search_fields = ["name", "country"]


@admin.register(WeatherRecord)
class WeatherRecordAdmin(admin.ModelAdmin):
    list_display = ["location", "date", "temperature", "humidity", "wind_speed", "created_at"]
    list_filter = ["date", "location"]
    search_fields = ["location__name"]
    date_hierarchy = "date"
