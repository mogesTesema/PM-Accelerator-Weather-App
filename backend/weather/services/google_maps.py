"""
Google Maps / Stadia Maps service — embed URLs and static map images.

Uses Google Maps API if GOOGLE_MAPS_API_KEY is set, otherwise falls
back to Stadia Maps (free tier) using STADIA_MAPS_API_KEY.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def get_map_data(lat: float, lon: float, location_name: str = "") -> dict:
    """
    Generate map URLs for a given location.
    Returns {"embed_url": ..., "static_map_url": ..., "directions_url": ...}.
    """
    result = {
        "embed_url": "",
        "static_map_url": "",
        "directions_url": f"https://www.google.com/maps?q={lat},{lon}",
    }

    google_key = settings.GOOGLE_MAPS_API_KEY
    stadia_key = getattr(settings, "STADIA_MAPS_API_KEY", "")

    if google_key:
        # ── Google Maps (paid) ──
        query = location_name if location_name else f"{lat},{lon}"
        result["embed_url"] = (
            f"https://www.google.com/maps/embed/v1/place?key={google_key}&q={query}"
        )
        result["static_map_url"] = (
            f"https://maps.googleapis.com/maps/api/staticmap"
            f"?center={lat},{lon}"
            f"&zoom=12"
            f"&size=600x400"
            f"&maptype=roadmap"
            f"&markers=color:red|{lat},{lon}"
            f"&key={google_key}"
        )

    elif stadia_key:
        # ── Stadia Maps (free tier) ──
        result["static_map_url"] = (
            f"https://tiles.stadiamaps.com/static/osm_bright"
            f"?center={lon},{lat}"
            f"&zoom=12"
            f"&size=600x400"
            f"&markers={lon},{lat},color:red"
            f"&api_key={stadia_key}"
        )
        # Stadia doesn't have an embed endpoint; use OpenStreetMap embed
        result["embed_url"] = (
            f"https://www.openstreetmap.org/export/embed.html"
            f"?bbox={lon - 0.05},{lat - 0.03},{lon + 0.05},{lat + 0.03}"
            f"&layer=mapnik"
            f"&marker={lat},{lon}"
        )

    else:
        logger.warning(
            "No map API key set (GOOGLE_MAPS_API_KEY or STADIA_MAPS_API_KEY) "
            "— returning basic directions URL only."
        )

    return result
