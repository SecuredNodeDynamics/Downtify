"""Collect artist image candidates from online metadata sources."""

from __future__ import annotations

from typing import Any, TypedDict

from loguru import logger

from . import artist_art, artist_image_sources
from .musicbrainz import USER_AGENT, _ratio

import requests


class ArtistImageOption(TypedDict):
    id: str
    source: str
    label: str
    subtitle: str
    image_url: str
    jellyfin_artist_id: str


def _append_option(
    options: list[ArtistImageOption],
    seen_urls: set[str],
    *,
    option_id: str,
    source: str,
    label: str,
    subtitle: str,
    image_url: str,
    jellyfin_artist_id: str = '',
) -> None:
    url = str(image_url or '').strip()
    if not url and not jellyfin_artist_id:
        return
    dedupe_key = url.casefold() if url else f'jellyfin:{jellyfin_artist_id}'
    if dedupe_key in seen_urls:
        return
    seen_urls.add(dedupe_key)
    options.append(
        {
            'id': option_id,
            'source': source,
            'label': label,
            'subtitle': subtitle,
            'image_url': url,
            'jellyfin_artist_id': jellyfin_artist_id,
        }
    )


def _spotify_artist_items(artist_name: str, *, limit: int = 5) -> list[dict[str, Any]]:
    token = artist_image_sources._spotify_access_token()
    if not token:
        return []
    try:
        response = requests.get(
            'https://api.spotify.com/v1/search',
            headers={
                'Authorization': f'Bearer {token}',
                'User-Agent': artist_image_sources._SPOTIFY_UA,
            },
            params={
                'q': artist_name,
                'type': 'artist',
                'limit': limit,
            },
            timeout=15,
        )
        if response.status_code in {401, 403}:
            artist_image_sources._SPOTIFY_TOKEN.clear()
            return []
        response.raise_for_status()
        return [
            item
            for item in response.json().get('artists', {}).get('items') or []
            if isinstance(item, dict)
        ]
    except Exception:
        logger.opt(exception=True).debug(
            'Spotify artist search failed for {!r}',
            artist_name,
        )
        return []


def _best_spotify_image_url(item: dict[str, Any]) -> str:
    images = [
        image
        for image in item.get('images') or []
        if isinstance(image, dict) and str(image.get('url') or '').strip()
    ]
    if not images:
        return ''
    best = max(images, key=lambda image: int(image.get('width') or 0))
    return str(best.get('url') or '').strip()


def list_spotify_artist_image_options(
    artist_name: str,
    *,
    limit: int = 5,
    minimum_score: float = 0.75,
) -> list[ArtistImageOption]:
    options: list[ArtistImageOption] = []
    seen: set[str] = set()
    for item in _spotify_artist_items(artist_name, limit=limit):
        label = str(item.get('name') or '').strip()
        if not label:
            continue
        score = artist_image_sources._name_ratio(label, artist_name)
        if score < minimum_score:
            continue
        image_url = _best_spotify_image_url(item)
        if not image_url:
            continue
        artist_id = str(item.get('id') or '').strip() or label
        _append_option(
            options,
            seen,
            option_id=f'spotify:{artist_id}',
            source='Spotify',
            label=label,
            subtitle=f'{int(score * 100)}% name match',
            image_url=image_url,
        )
    return options


def list_discogs_artist_image_options(
    artist_name: str,
    *,
    discogs_token: str = '',
    limit: int = 5,
    minimum_score: float = 0.75,
) -> list[ArtistImageOption]:
    options: list[ArtistImageOption] = []
    seen: set[str] = set()
    try:
        response = requests.get(
            artist_image_sources._DISCOGS_SEARCH_URL,
            headers=artist_image_sources._discogs_headers(discogs_token),
            params={
                'q': artist_name,
                'type': 'artist',
                'per_page': limit,
            },
            timeout=15,
        )
        response.raise_for_status()
        results = response.json().get('results') or []
    except Exception:
        logger.opt(exception=True).debug(
            'Discogs artist search failed for {!r}',
            artist_name,
        )
        return options

    for item in results:
        if not isinstance(item, dict):
            continue
        label = str(item.get('title') or '').strip()
        if not label:
            continue
        score = artist_image_sources._name_ratio(label, artist_name)
        if score < minimum_score:
            continue
        artist_id = item.get('id')
        if not artist_id:
            continue
        try:
            detail = requests.get(
                f'https://api.discogs.com/artists/{artist_id}',
                headers=artist_image_sources._discogs_headers(discogs_token),
                timeout=15,
            )
            detail.raise_for_status()
            images = detail.json().get('images') or []
        except Exception:
            continue
        image_url = ''
        for preferred_type in ('primary', 'secondary'):
            for image in images:
                if not isinstance(image, dict):
                    continue
                if str(image.get('type') or '').casefold() != preferred_type:
                    continue
                image_url = str(
                    image.get('uri') or image.get('resource_url') or ''
                ).strip()
                if image_url:
                    break
            if image_url:
                break
        if not image_url and images and isinstance(images[0], dict):
            image_url = str(
                images[0].get('uri') or images[0].get('resource_url') or ''
            ).strip()
        if not image_url:
            continue
        _append_option(
            options,
            seen,
            option_id=f'discogs:{artist_id}',
            source='Discogs',
            label=label,
            subtitle=f'{int(score * 100)}% name match',
            image_url=image_url,
        )
    return options


def _musicbrainz_search_artists(
    artist_name: str,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            'https://musicbrainz.org/ws/2/artist/',
            params={
                'query': f'artist:"{artist_name}"',
                'fmt': 'json',
                'limit': limit,
            },
            headers={'User-Agent': USER_AGENT},
            timeout=12,
        )
        response.raise_for_status()
        return [
            item
            for item in response.json().get('artists') or []
            if isinstance(item, dict)
        ]
    except Exception:
        logger.opt(exception=True).debug(
            'MusicBrainz artist search failed for {!r}',
            artist_name,
        )
        return []


def list_musicbrainz_artist_image_options(
    artist_name: str,
    *,
    limit: int = 5,
    minimum_score: float = 0.75,
) -> list[ArtistImageOption]:
    options: list[ArtistImageOption] = []
    seen: set[str] = set()
    for item in _musicbrainz_search_artists(artist_name, limit=limit):
        label = str(item.get('name') or '').strip()
        mbid = str(item.get('id') or '').strip()
        if not label or not mbid:
            continue
        score = _ratio(label, artist_name)
        if score < minimum_score:
            continue
        for image_url, source_label in artist_art.musicbrainz_artist_image_urls(
            mbid
        ):
            _append_option(
                options,
                seen,
                option_id=f'musicbrainz:{mbid}:{source_label.casefold()}',
                source=source_label,
                label=label,
                subtitle=f'{int(score * 100)}% name match',
                image_url=image_url,
            )
    return options


def collect_artist_image_options(
    artist_name: str,
    *,
    discogs_token: str = '',
    jellyfin_artist_id: str = '',
    jellyfin_label: str = '',
    per_source_limit: int = 5,
) -> list[ArtistImageOption]:
    artist_name = str(artist_name or '').strip()
    if not artist_name:
        return []

    options: list[ArtistImageOption] = []
    seen: set[str] = set()
    jellyfin_artist_id = str(jellyfin_artist_id or '').strip()
    if jellyfin_artist_id:
        _append_option(
            options,
            seen,
            option_id=f'jellyfin:{jellyfin_artist_id}',
            source='Jellyfin',
            label=jellyfin_label or artist_name,
            subtitle='Current Jellyfin library art',
            image_url='',
            jellyfin_artist_id=jellyfin_artist_id,
        )

    for source_options in (
        list_spotify_artist_image_options(
            artist_name,
            limit=per_source_limit,
        ),
        list_discogs_artist_image_options(
            artist_name,
            discogs_token=discogs_token,
            limit=per_source_limit,
        ),
        list_musicbrainz_artist_image_options(
            artist_name,
            limit=per_source_limit,
        ),
    ):
        for option in source_options:
            dedupe_key = (
                option['image_url'].casefold()
                if option['image_url']
                else f"jellyfin:{option['jellyfin_artist_id']}"
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            options.append(option)

    return options
