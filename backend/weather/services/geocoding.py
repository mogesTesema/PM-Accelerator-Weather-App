"""
Geocoding service — resolves user input to (lat, lon) via LocationIQ
and Pinecone for fuzzy/landmark matching.
"""

import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

LOCATIONIQ_BASE_URL = "https://us1.locationiq.com/v1"

def _is_probable_zip_code(query: str) -> bool:
    """Return True if query looks like a postal/zip code."""
    query = query.strip()
    # US Zip code (5 digits or 5-4)
    if re.match(r"^\d{5}(?:-\d{4})?$", query):
        return True
    # UK Postal Code (approximate e.g. SW1A 1AA)
    if re.match(r"^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$", query, re.IGNORECASE):
        return True
    # Canada Postal Code (e.g. K1A 0B1)
    if re.match(r"^[A-Z]\d[A-Z] ?\d[A-Z]\d$", query, re.IGNORECASE):
        return True
    return False


def resolve_location(query: str) -> dict | None:
    """
    Resolve a location query string to coordinates via LocationIQ.
    Returns {"name": ..., "lat": ..., "lon": ..., "country": ..., "type": ...}
    or None if not found.
    """
    api_key = settings.LOCATIONIQ_API_KEY
    if not api_key:
        logger.warning("LOCATIONIQ_API_KEY not set.")
        return None

    try:
        # Determine if we should do a precise postalcode search or a generic search
        params = {
            "key": api_key,
            "format": "json",
            "limit": 1,
        }

        if _is_probable_zip_code(query):
            params["postalcode"] = query.strip()
        else:
            params["q"] = query

        response = requests.get(
            f"{LOCATIONIQ_BASE_URL}/search",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        result = data[0]
        return {
            "name": result.get("display_name", query),
            "lat": float(result["lat"]),
            "lon": float(result["lon"]),
            "country": _extract_country(result),
            "type": _classify_type(result),
        }
    except requests.RequestException as e:
        logger.error("LocationIQ request failed: %s", e)
        return None


def fuzzy_search(query: str) -> dict | None:
    """
    Use Pinecone vector similarity search to resolve ambiguous
    or landmark-based location queries.
    Returns {"name": ..., "lat": ..., "lon": ...} or None.
    """
    api_key = settings.PINECONE_API_KEY
    if not api_key:
        logger.info("PINECONE_API_KEY not set — skipping fuzzy search.")
        return None

    try:
        from pinecone import Pinecone

        pc = Pinecone(api_key=api_key)

        # Check if index exists; if not, skip
        indexes = pc.list_indexes()
        if not indexes or not any(idx.name == "locations" for idx in indexes):
            logger.info("Pinecone 'locations' index not found — skipping fuzzy search.")
            return None

        index = pc.Index("locations")
        # For a real implementation, we'd embed the query first.
        # For now, we do a metadata-based search as a placeholder.
        results = index.query(
            vector=[0.0] * 1536,  # placeholder embedding
            top_k=1,
            include_metadata=True,
            filter={"name": {"$eq": query}},
        )

        if results and results.matches:
            match = results.matches[0]
            metadata = match.metadata
            return {
                "name": metadata.get("name", query),
                "lat": metadata.get("lat"),
                "lon": metadata.get("lon"),
            }
        return None
    except Exception as e:
        logger.error("Pinecone fuzzy search failed: %s", e)
        return None


def _extract_country(result: dict) -> str:
    """Extract country from LocationIQ result address breakdown."""
    address = result.get("address", {})
    if isinstance(address, dict):
        return address.get("country", "")
    return ""


def _classify_type(result: dict) -> str:
    """Classify the location type from LocationIQ result."""
    loc_type = result.get("type", "").lower()
    loc_class = result.get("class", "").lower()

    if loc_class in ("place", "boundary") and loc_type in ("city", "town", "village"):
        return "city"
    if loc_type in ("postcode",):
        return "zip"
    if loc_class in ("tourism", "historic"):
        return "landmark"
    return "other"
