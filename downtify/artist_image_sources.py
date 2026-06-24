"""Online artist image lookups by name (Spotify, Apple Music, Discogs)."""

from __future__ import annotations

import re
import time
from difflib import SequenceMatcher
from typing import Any, Callable

import requests
from loguru import logger
from ytmusicapi import YTMusic

from .artist_art import _download_image
from .musicbrainz import USER_AGENT

ArtistImageFetcher = Callable[[str, dict[str, str]], tuple[bytes | None, str]]

_SPOTIFY_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
)
_ITUNES_SEARCH_URL = 'https://itunes.apple.com/search'
_DISCOGS_SEARCH_URL = 'https://api.discogs.com/database/search'
_DEEZER_SEARCH_URL = 'https://api.deezer.com/search/artist'
_DEEZER_ARTIST_URL = 'https://api.deezer.com/artist/{artist_id}'
_APPLE_OG_IMAGE_RE = re.compile(
    r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
    re.I,
)
_MZSTATIC_SIZE_RE = re.compile(r'/\d+x\d+(?:bb|sr)?\.(?:jpg|jpeg|png|webp)\b', re.I)
_EMBED_BOOTSTRAP_ARTIST_ID = '4NJhFmfw43RLBLjQvxDuRS'

_SPOTIFY_TOKEN: dict[str, Any] = {}
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
    minimum: float = 0.72,
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


def _spotify_embed_access_token() -> str:
    embed_cache = _SPOTIFY_TOKEN.get('embed')
    if isinstance(embed_cache, dict):
        token = str(embed_cache.get('token') or '').strip()
        expires_at = float(embed_cache.get('expires_at') or 0)
        if token and expires_at > time.time() + 30:
            return token

    try:
        from . import spotify as spotify_module

        payload = spotify_module._fetch_embed_json(
            'artist', _EMBED_BOOTSTRAP_ARTIST_ID
        )
        token = spotify_module._token_from_embed_payload(payload)
        if not token:
            return ''
        session = (
            payload.get('props', {})
            .get('pageProps', {})
            .get('state', {})
            .get('settings', {})
            .get('session', {})
        )
        expires_ms = int(session.get('accessTokenExpirationTimestampMs') or 0)
        expires_at = (
            expires_ms / 1000 if expires_ms > 0 else time.time() + 3600
        )
        _SPOTIFY_TOKEN['embed'] = {
            'token': token,
            'expires_at': expires_at,
        }
        return token
    except Exception:
        logger.opt(exception=True).debug(
            'Spotify embed access token bootstrap failed'
        )
        return ''


def _spotify_transport_access_token() -> str:
    transport_blocked_until = float(
        _SPOTIFY_TOKEN.get('transport_blocked_until') or 0
    )
    if transport_blocked_until > time.time():
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
            _SPOTIFY_TOKEN['transport_blocked_until'] = time.time() + 3600
            logger.info(
                'Spotify transport token unavailable (HTTP {})',
                response.status_code,
            )
            return ''
        response.raise_for_status()
        payload = response.json()
    except Exception:
        logger.opt(exception=True).debug(
            'Spotify transport access token request failed'
        )
        _SPOTIFY_TOKEN['transport_blocked_until'] = time.time() + 300
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


def _spotify_search_blocked() -> bool:
    return float(_SPOTIFY_TOKEN.get('search_blocked_until') or 0) > time.time()


def _mark_spotify_search_rate_limited(
    response: requests.Response | None = None,
) -> None:
    retry_after = 60.0
    if response is not None:
        try:
            retry_after = max(
                60.0, float(response.headers.get('Retry-After', 60))
            )
        except (TypeError, ValueError):
            retry_after = 60.0
    _SPOTIFY_TOKEN['search_blocked_until'] = time.time() + retry_after
    logger.info(
        'Spotify artist search rate-limited; pausing search for {:.0f}s',
        retry_after,
    )


def _spotify_access_token() -> str:
    token = _spotify_transport_access_token()
    if token:
        return token
    return _spotify_embed_access_token()


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


def _is_deezer_placeholder_picture(url: str) -> bool:
    lowered = str(url or '').casefold()
    return (
        '/artist//1000x1000' in lowered
        or '000000-80-0-0' in lowered
        or lowered.endswith('artist//1000x1000-000000-80-0-0.jpg')
    )


def _best_deezer_picture(item: dict[str, Any]) -> str:
    for key in ('picture_xl', 'picture_big', 'picture_medium', 'picture'):
        url = str(item.get(key) or '').strip()
        if url and not _is_deezer_placeholder_picture(url):
            return url
    return ''


def _deezer_artist_items(artist_name: str, *, limit: int = 5) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            _DEEZER_SEARCH_URL,
            params={'q': artist_name, 'limit': limit},
            headers={'User-Agent': USER_AGENT},
            timeout=12,
        )
        response.raise_for_status()
        return [
            item
            for item in response.json().get('data') or []
            if isinstance(item, dict)
        ]
    except Exception:
        logger.opt(exception=True).debug(
            'Deezer artist search failed for {!r}',
            artist_name,
        )
        return []


def fetch_deezer_artist_image(artist_name: str) -> tuple[bytes | None, str]:
    match = _best_name_match(
        _deezer_artist_items(artist_name),
        artist_name,
        key='name',
    )
    if not match:
        return None, ''

    image_url = _best_deezer_picture(match)
    if not image_url:
        artist_id = match.get('id')
        if artist_id:
            try:
                response = requests.get(
                    _DEEZER_ARTIST_URL.format(artist_id=artist_id),
                    headers={'User-Agent': USER_AGENT},
                    timeout=12,
                )
                response.raise_for_status()
                image_url = _best_deezer_picture(response.json())
            except Exception:
                image_url = ''
    if not image_url:
        return None, ''

    data = _download_image(image_url)
    return (data, 'Deezer') if data else (None, '')


def fetch_deezer_artist_image_by_id(artist_id: str) -> tuple[bytes | None, str]:
    artist_id = str(artist_id or '').strip()
    if not artist_id:
        return None, ''
    try:
        response = requests.get(
            _DEEZER_ARTIST_URL.format(artist_id=artist_id),
            headers={'User-Agent': USER_AGENT},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return None, ''
    image_url = _best_deezer_picture(payload)
    if not image_url:
        return None, ''
    data = _download_image(image_url)
    return (data, 'Deezer') if data else (None, '')


def _youtube_music_artist_items(
    artist_name: str,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    try:
        return [
            item
            for item in YTMusic().search(artist_name, filter='artists', limit=limit)
            if isinstance(item, dict)
        ]
    except Exception:
        logger.opt(exception=True).debug(
            'YouTube Music artist search failed for {!r}',
            artist_name,
        )
        return []


def _best_youtube_music_image_url(item: dict[str, Any]) -> str:
    thumbs = [
        thumb
        for thumb in item.get('thumbnails') or []
        if isinstance(thumb, dict) and str(thumb.get('url') or '').strip()
    ]
    if not thumbs:
        return ''
    best = max(thumbs, key=lambda thumb: int(thumb.get('width') or 0))
    return str(best.get('url') or '').strip()


def fetch_youtube_music_artist_image(artist_name: str) -> tuple[bytes | None, str]:
    match = _best_name_match(
        _youtube_music_artist_items(artist_name),
        artist_name,
        key='artist',
    )
    if not match:
        return None, ''

    image_url = _best_youtube_music_image_url(match)
    if not image_url:
        return None, ''

    data = _download_image(image_url)
    return (data, 'YouTube Music') if data else (None, '')


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

    thumb = str(match.get('thumb') or '').strip()
    if thumb:
        data = _download_image(thumb)
        if data:
            return data, 'Discogs'

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
        ('YouTube Music', fetch_youtube_music_artist_image),
        ('Deezer', fetch_deezer_artist_image),
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


def resolve_artist_image_by_option_id(
    option_id: str,
    artist_name: str,
    *,
    discogs_token: str = '',
) -> tuple[bytes | None, str]:
    option_id = str(option_id or '').strip()
    artist_name = str(artist_name or '').strip()
    if not option_id:
        return None, ''

    if option_id.startswith('youtube-music:'):
        return fetch_youtube_music_artist_image(artist_name)

    if option_id.startswith('deezer:'):
        deezer_id = option_id.split(':', 1)[1].split(':', 1)[0].strip()
        if deezer_id.isdigit():
            data, source = fetch_deezer_artist_image_by_id(deezer_id)
            if data:
                return data, source
        return fetch_deezer_artist_image(artist_name)

    if option_id.startswith('spotify:'):
        return fetch_spotify_artist_image(artist_name)

    if option_id.startswith('apple-music:'):
        return fetch_apple_music_artist_image(artist_name)

    if option_id.startswith('discogs:'):
        return fetch_discogs_artist_image(
            artist_name,
            discogs_token=discogs_token,
        )

    return None, ''
