"""
YouTube Data API v3 client — search for location-related travel videos.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def search_videos(location_name: str, max_results: int = 5) -> list[dict]:
    """
    Search YouTube for travel/weather videos related to a location.
    Returns list of video dicts: {video_id, title, thumbnail, channel, url}.
    """
    api_key = settings.YOUTUBE_API_KEY
    if not api_key:
        logger.warning("YOUTUBE_API_KEY not set — returning empty results.")
        return []

    try:
        response = requests.get(
            YOUTUBE_SEARCH_URL,
            params={
                "key": api_key,
                "q": f"{location_name} travel guide weather",
                "part": "snippet",
                "type": "video",
                "maxResults": max_results,
                "order": "relevance",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        videos = []
        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId", "")
            videos.append(
                {
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "thumbnail": snippet.get("thumbnails", {})
                    .get("high", {})
                    .get("url", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                }
            )

        return videos
    except requests.RequestException as e:
        logger.error("YouTube API request failed: %s", e)
        return []
