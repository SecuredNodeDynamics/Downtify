"""Online artist image lookups by name (Spotify, Apple Music, Discogs)."""

from __future__ import annotations

import re
import time
from difflib import SequenceMatcher
from typing import Any, Callable

import requests
from loguru import logger

from .artist_art import _download_image
from .musicbrainz import USER_AGENT

ArtistImageFetcher = Callable[[str, dict[str, str]], tuple[bytes | None, str]]

_SPOTIFY_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)
_ITUNES_SEARCH_URL = 'https://itunes.apple.com/search'
_DISCOGS_SEARCH_URL = 'https://api.discogs.com/database/search'
_APPLE_OG_IMAGE_RE = re.compile(
    r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
    re.I,
)
_MZSTATIC_SIZE_RE = re.compile(r'/\d+x\d+(?:bb|sr)?\.(?:jpg|jpeg|png|webp)\b', re.I)

_SPOTIFY_TOKEN: dict[str, Any] = {'blocked': False}
_NAME_IMAGE_CACHE: dict[str, tuple[bytes | None, str]] = {}


def _norm(value: str) -> str:
    return ' '.join(str(value or '').casefold().split())


def _name_ratio(left: str, right: str) -> float:
    left_norm = _norm(left)
    right_norm = _norm(right)
    if not left_norm or not right_norm:
        return 0.0
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def _best_name_match(
    items: list[dict[str, Any]],
    artist_name: str,
    *,
    key: str,
    minimum: float = 0.82,
) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    best_score = 0.0
    for item in items:
        if not isinstance(item, dict):
            continue
        candidate = str(item.get(key) or '').strip()
        if not candidate:
            continue
        score = _name_ratio(candidate, artist_name)
        if score > best_score:
            best = item
            best_score = score
    if best is None or best_score < minimum:
        return None
    return best


def _upgrade_mzstatic_url(url: str, size: int = 600) -> str:
    if not url:
        return ''
    suffix = f'/{size}x{size}bb.jpg'
    if _MZSTATIC_SIZE_RE.search(url):
        return _MZSTATIC_SIZE_RE.sub(suffix, url, count=1)
    return url


def _spotify_access_token() -> str:
    if _SPOTIFY_TOKEN.get('blocked'):
        return ''

    cached = str(_SPOTIFY_TOKEN.get('token') or '').strip()
    expires_at = float(_SPOTIFY_TOKEN.get('expires_at') or 0)
    if cached and expires_at > time.time() + 30:
        return cached

    try:
        response = requests.get(
            'https://open.spotify.com/get_access_token',
            params={'reason': 'transport', 'productType': 'web_player'},
            headers={'User-Agent': _SPOTIFY_UA},
            timeout=12,
        )
        if response.status_code in {401, 403, 429}:
            _SPOTIFY_TOKEN['blocked'] = True
            logger.info(
                'Spotify artist image lookup unavailable (HTTP {})',
                response.status_code,
            )
            return ''
        response.raise_for_status()
        payload = response.json()
    except Exception:
        logger.opt(exception=True).debug(
            'Spotify access token request failed; skipping Spotify lookups'
        )
        _SPOTIFY_TOKEN['blocked'] = True
        return ''

    token = str(payload.get('accessToken') or '').strip()
    if not token:
        return ''
    _SPOTIFY_TOKEN['token'] = token
    _SPOTIFY_TOKEN['expires_at'] = time.time() + max(
        60,
        int(payload.get('accessTokenExpirationTimestampMs') or 0) / 1000
        - time.time(),
    )
    return token


def fetch_spotify_artist_image(artist_name: str) -> tuple[bytes | None, str]:
    token = _spotify_access_token()
    if not token:
        return None, ''

    response = requests.get(
        'https://api.spotify.com/v1/search',
        headers={
            'Authorization': f'Bearer {token}',
            'User-Agent': _SPOTIFY_UA,
        },
        params={
            'q': artist_name,
            'type': 'artist',
            'limit': 5,
        },
        timeout=15,
    )
    if response.status_code in {401, 403}:
        _SPOTIFY_TOKEN.clear()
        return None, ''
    response.raise_for_status()
    items = response.json().get('artists', {}).get('items') or []
    match = _best_name_match(items, artist_name, key='name')
    if not match:
        return None, ''

    images = match.get('images') or []
    sized = [
        item
        for item in images
        if isinstance(item, dict) and str(item.get('url') or '').strip()
    ]
    image_url = ''
    if sized:
        best = max(sized, key=lambda item: int(item.get('width') or 0))
        image_url = str(best.get('url') or '').strip()
    if not image_url:
        return None, ''

    data = _download_image(image_url)
    return (data, 'Spotify') if data else (None, '')


def fetch_apple_music_artist_image(artist_name: str) -> tuple[bytes | None, str]:
    response = requests.get(
        _ITUNES_SEARCH_URL,
        params={
            'term': artist_name,
            'entity': 'musicArtist',
            'limit': 5,
        },
        headers={'User-Agent': USER_AGENT},
        timeout=15,
    )
    response.raise_for_status()
    match = _best_name_match(
        response.json().get('results') or [],
        artist_name,
        key='artistName',
    )
    if not match:
        return None, ''

    artist_url = str(match.get('artistLinkUrl') or '').strip()
    if not artist_url:
        return None, ''

    page = requests.get(
        artist_url,
        headers={'User-Agent': _SPOTIFY_UA},
        timeout=15,
    )
    page.raise_for_status()
    image_match = _APPLE_OG_IMAGE_RE.search(page.text)
    if not image_match:
        return None, ''

    image_url = _upgrade_mzstatic_url(image_match.group(1).strip())
    data = _download_image(image_url)
    return (data, 'Apple Music') if data else (None, '')


def _discogs_headers(token: str = '') -> dict[str, str]:
    headers = {'User-Agent': USER_AGENT}
    token = str(token or '').strip()
    if token:
        headers['Authorization'] = f'Discogs token={token}'
    return headers


def fetch_discogs_artist_image(
    artist_name: str,
    *,
    discogs_token: str = '',
) -> tuple[bytes | None, str]:
    response = requests.get(
        _DISCOGS_SEARCH_URL,
        headers=_discogs_headers(discogs_token),
        params={
            'q': artist_name,
            'type': 'artist',
            'per_page': 5,
        },
        timeout=15,
    )
    response.raise_for_status()
    match = _best_name_match(
        response.json().get('results') or [],
        artist_name,
        key='title',
    )
    if not match:
        return None, ''

    artist_id = match.get('id')
    if not artist_id:
        return None, ''

    detail = requests.get(
        f'https://api.discogs.com/artists/{artist_id}',
        headers=_discogs_headers(discogs_token),
        timeout=15,
    )
    detail.raise_for_status()
    images = detail.json().get('images') or []
    image_url = ''
    for preferred_type in ('primary', 'secondary'):
        for image in images:
            if not isinstance(image, dict):
                continue
            if str(image.get('type') or '').casefold() != preferred_type:
                continue
            image_url = str(image.get('uri') or image.get('resource_url') or '').strip()
            if image_url:
                break
        if image_url:
            break
    if not image_url and images:
        first = images[0]
        if isinstance(first, dict):
            image_url = str(first.get('uri') or first.get('resource_url') or '').strip()
    if not image_url:
        return None, ''

    data = _download_image(image_url)
    return (data, 'Discogs') if data else (None, '')


def fetch_online_artist_image(
    artist_name: str,
    *,
    discogs_token: str = '',
) -> tuple[bytes | None, str]:
    artist_name = str(artist_name or '').strip()
    if not artist_name:
        return None, ''

    cache_key = f'{_norm(artist_name)}::{discogs_token}'
    if cache_key in _NAME_IMAGE_CACHE:
        return _NAME_IMAGE_CACHE[cache_key]

    sources: list[tuple[str, Callable[[str], tuple[bytes | None, str]]]] = [
        ('Apple Music', fetch_apple_music_artist_image),
        (
            'Discogs',
            lambda name: fetch_discogs_artist_image(
                name,
                discogs_token=discogs_token,
            ),
        ),
        ('Spotify', fetch_spotify_artist_image),
    ]
    for _label, fetch in sources:
        try:
            data, source = fetch(artist_name)
        except Exception:
            logger.debug(
                'Online artist image lookup failed via {} for {!r}',
                fetch.__name__ if hasattr(fetch, '__name__') else _label,
                artist_name,
            )
            continue
        if data:
            _NAME_IMAGE_CACHE[cache_key] = (data, source)
            return data, source

    _NAME_IMAGE_CACHE[cache_key] = (None, '')
    return None, ''


def online_artist_image_fetcher(
    discogs_token: str = '',
) -> ArtistImageFetcher:
    def _fetch(artist_name: str, _artist: dict[str, str]) -> tuple[bytes | None, str]:
        return fetch_online_artist_image(
            artist_name,
            discogs_token=discogs_token,
        )

    return _fetch
