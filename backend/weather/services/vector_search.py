"""
Pinecone vector-based fuzzy location search.

Uses Pinecone Inference API (llama-text-embed-v2) to embed queries
and perform semantic similarity search against a pre-seeded index
of world cities, capitals, and landmarks.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────
EMBED_MODEL = "llama-text-embed-v2"
SIMILARITY_THRESHOLD = 0.3
TOP_K = 3


def _get_client():
    """
    Return a (Pinecone client, Index) tuple, or (None, None)
    if Pinecone is not configured.
    """
    api_key = settings.PINECONE_API_KEY
    if not api_key:
        logger.info("PINECONE_API_KEY not set — vector search disabled.")
        return None, None

    try:
        from pinecone import Pinecone

        pc = Pinecone(api_key=api_key)

        # Direct host connection — avoids a list_indexes API call
        host = settings.PINECONE_HOST
        if host:
            index = pc.Index(
                name=settings.PINECONE_INDEX_NAME,
                host=host,
            )
        else:
            index = pc.Index(settings.PINECONE_INDEX_NAME)

        return pc, index
    except Exception as e:
        logger.error("Failed to initialize Pinecone client: %s", e)
        return None, None


def _embed_query(pc, text: str) -> list[float] | None:
    """
    Generate a 1024-dim embedding for a search query using
    Pinecone's Inference API (free tier: 5M tokens/month).
    """
    try:
        response = pc.inference.embed(
            model=EMBED_MODEL,
            inputs=[text],
            parameters={
                "input_type": "query",
                "truncate": "END",
            },
        )
        if response and len(response) > 0:
            return response[0].values
        return None
    except Exception as e:
        logger.error("Pinecone embedding failed: %s", e)
        return None


def fuzzy_location_search(query: str) -> dict | None:
    """
    Perform semantic similarity search for a location query.

    Embeds the query, searches the Pinecone index for the closest
    location vectors, and returns the best match above the
    similarity threshold.

    Args:
        query: Natural language location query (e.g. "Big Apple",
               "The Great Pyramids", "Eiffel Tower").

    Returns:
        Dict with keys {name, lat, lon, country, type} or None.
    """
    pc, index = _get_client()
    if pc is None or index is None:
        return None

    # 1. Embed the query
    vector = _embed_query(pc, query)
    if vector is None:
        return None

    # 2. Search the index
    try:
        results = index.query(
            vector=vector,
            top_k=TOP_K,
            include_metadata=True,
        )
    except Exception as e:
        logger.error("Pinecone query failed: %s", e)
        return None

    # 3. Check results against similarity threshold
    if not results or not results.matches:
        logger.info("Pinecone returned no matches for query: '%s'", query)
        return None

    best = results.matches[0]
    score = best.score

    logger.info(
        "Pinecone best match for '%s': '%s' (score=%.4f)",
        query,
        best.metadata.get("name", "?"),
        score,
    )

    if score < SIMILARITY_THRESHOLD:
        logger.info(
            "Score %.4f below threshold %.2f — rejecting match.",
            score,
            SIMILARITY_THRESHOLD,
        )
        return None

    metadata = best.metadata
    return {
        "name": metadata.get("name", query),
        "lat": metadata.get("lat"),
        "lon": metadata.get("lon"),
        "country": metadata.get("country", ""),
        "type": metadata.get("type", "other"),
    }
