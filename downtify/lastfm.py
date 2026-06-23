"""Last.fm artist tag lookup for Spotify-style genres."""

from __future__ import annotations

import os
import time

import requests
from loguru import logger

from .genres import pick_genre_from_tag_names

LASTFM_API_URL = 'https://ws.audioscrobbler.com/2.0/'
DEFAULT_LASTFM_API_KEY = 'b25b959554ed76058ac220b7b2e0a026'
_LAST_REQUEST_AT = 0.0


def _api_key() -> str:
    return (
        os.getenv('LASTFM_API_KEY', '').strip()
        or os.getenv('LAST_FM_API_KEY', '').strip()
        or DEFAULT_LASTFM_API_KEY
    )


def _throttle() -> None:
    elapsed = time.monotonic() - _LAST_REQUEST_AT
    if elapsed < 0.25:
        time.sleep(0.25 - elapsed)


def _fetch_artist_tags(artist_name: str, *, timeout: int = 8) -> list[str]:
    global _LAST_REQUEST_AT

    try:
        _throttle()
        response = requests.get(
            LASTFM_API_URL,
            params={
                'method': 'artist.getTopTags',
                'artist': artist_name,
                'api_key': _api_key(),
                'format': 'json',
            },
            timeout=timeout,
        )
        _LAST_REQUEST_AT = time.monotonic()
        response.raise_for_status()
        payload = response.json()
    except Exception:
        logger.opt(exception=True).debug(
            'Last.fm artist tag lookup failed for {!r}',
            artist_name,
        )
        return []

    tags = payload.get('toptags', {}).get('tag', [])
    if isinstance(tags, dict):
        tags = [tags]
    if not isinstance(tags, list):
        return []
    return [
        str(item.get('name') or '').strip()
        for item in tags
        if isinstance(item, dict) and str(item.get('name') or '').strip()
    ]


def lookup_artist_genre(artist_name: str, *, timeout: int = 8) -> str:
    """Return a Spotify-style genre for *artist_name* from Last.fm tags."""

    tags = _fetch_artist_tags(artist_name, timeout=timeout)
    return pick_genre_from_tag_names(tags)
