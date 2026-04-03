"""
Google Maps service — embed URLs and static map URLs for a location.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def get_map_data(lat: float, lon: float, location_name: str = "") -> dict:
    """
    Generate Google Maps URLs for a given location.
    Returns {"embed_url": ..., "static_map_url": ..., "directions_url": ...}.
    """
    api_key = settings.GOOGLE_MAPS_API_KEY

    result = {
        "embed_url": "",
        "static_map_url": "",
        "directions_url": f"https://www.google.com/maps?q={lat},{lon}",
    }

    if not api_key:
        logger.warning("GOOGLE_MAPS_API_KEY not set — returning basic URLs only.")
        return result

    # Embed URL (for iframe)
    query = location_name if location_name else f"{lat},{lon}"
    result["embed_url"] = (
        f"https://www.google.com/maps/embed/v1/place"
        f"?key={api_key}"
        f"&q={query}"
    )

    # Static map image URL
    result["static_map_url"] = (
        f"https://maps.googleapis.com/maps/api/staticmap"
        f"?center={lat},{lon}"
        f"&zoom=12"
        f"&size=600x400"
        f"&maptype=roadmap"
        f"&markers=color:red|{lat},{lon}"
        f"&key={api_key}"
    )

    return result
