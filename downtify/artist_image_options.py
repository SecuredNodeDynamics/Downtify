"""Collect artist image candidates from online metadata sources."""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, TypedDict

import requests
from loguru import logger

from . import artist_image_sources
from .artist_art import _wikimedia_artist_image_url
from .metadata_repair import artist_search_names
from . import musicbrainz as musicbrainz_module
from .musicbrainz import USER_AGENT, _ratio, _throttle_musicbrainz

_SPOTIFY_ARTIST_URL_RE = re.compile(
    r'(?:https?://)?(?:open\.)?spotify\.com/artist/([A-Za-z0-9]+)'
)

ArtistImageOption = TypedDict(
    'ArtistImageOption',
    {
        'id': str,
        'source': str,
        'label': str,
        'subtitle': str,
        'image_url': str,
        'jellyfin_artist_id': str,
    },
)


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
    if artist_image_sources._spotify_search_blocked():
        return []
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
            timeout=10,
        )
        if response.status_code in {401, 403, 429}:
            artist_image_sources._mark_spotify_search_rate_limited(response)
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


def _spotify_id_from_musicbrainz_artist(mbid: str) -> str:
    mbid = str(mbid or '').strip()
    if not mbid:
        return ''
    try:
        _throttle_musicbrainz()
        response = requests.get(
            f'https://musicbrainz.org/ws/2/artist/{mbid}',
            params={'inc': 'url-rels', 'fmt': 'json'},
            headers={'User-Agent': USER_AGENT},
            timeout=12,
        )
        if response.status_code != 200:
            return ''
        for relation in response.json().get('relations') or []:
            if not isinstance(relation, dict):
                continue
            target = relation.get('url')
            if not isinstance(target, dict):
                continue
            resource = str(target.get('resource') or '')
            match = _SPOTIFY_ARTIST_URL_RE.search(resource)
            if match:
                return match.group(1)
    except Exception:
        logger.opt(exception=True).debug(
            'MusicBrainz Spotify artist URL lookup failed for {!r}',
            mbid,
        )
    return ''


def _append_spotify_artist_match(
    results: list[dict[str, Any]],
    seen_ids: set[str],
    *,
    spotify_id: str,
    name: str,
    artist_name: str,
    image_url: str = '',
) -> None:
    spotify_id = str(spotify_id or '').strip()
    name = str(name or '').strip()
    if not spotify_id or not name or spotify_id in seen_ids:
        return
    seen_ids.add(spotify_id)
    results.append(
        {
            'spotify_id': spotify_id,
            'name': name,
            'url': f'https://open.spotify.com/artist/{spotify_id}',
            'image_url': image_url,
            'match_score': round(
                artist_image_sources._name_ratio(name, artist_name),
                3,
            ),
        }
    )


def _musicbrainz_spotify_artist_matches(
    artist_name: str,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for item in _musicbrainz_search_artists(artist_name, limit=limit):
        label = str(item.get('name') or '').strip()
        mbid = str(item.get('id') or '').strip()
        if not label or not mbid:
            continue
        spotify_id = _spotify_id_from_musicbrainz_artist(mbid)
        _append_spotify_artist_match(
            results,
            seen_ids,
            spotify_id=spotify_id,
            name=label,
            artist_name=artist_name,
        )
    if not results:
        mbid = musicbrainz_module.lookup_artist_id(artist_name) or ''
        if mbid:
            spotify_id = _spotify_id_from_musicbrainz_artist(mbid)
            _append_spotify_artist_match(
                results,
                seen_ids,
                spotify_id=spotify_id,
                name=artist_name,
                artist_name=artist_name,
            )
    results.sort(key=lambda item: item['match_score'], reverse=True)
    return results


def list_spotify_artist_matches(
    artist_name: str,
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    seen_ids: set[str] = set()
    results: list[dict[str, Any]] = []
    for item in _musicbrainz_spotify_artist_matches(artist_name, limit=limit):
        spotify_id = str(item.get('spotify_id') or '').strip()
        if not spotify_id or spotify_id in seen_ids:
            continue
        seen_ids.add(spotify_id)
        results.append(item)
    if len(results) < limit and not artist_image_sources._spotify_search_blocked():
        search_names = artist_search_names(artist_name) or [artist_name]
        for search_name in search_names:
            for item in _spotify_artist_items(search_name, limit=limit):
                _append_spotify_artist_match(
                    results,
                    seen_ids,
                    spotify_id=str(item.get('id') or '').strip(),
                    name=str(item.get('name') or '').strip(),
                    artist_name=artist_name,
                    image_url=_best_spotify_image_url(item),
                )
            if len(results) >= limit:
                break
            if artist_image_sources._spotify_search_blocked():
                break
    results.sort(key=lambda item: item['match_score'], reverse=True)
    return results[:limit]


def list_spotify_artist_image_options(
    artist_name: str,
    *,
    limit: int = 5,
    minimum_score: float = 0.72,
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


def list_apple_music_artist_image_options(
    artist_name: str,
    *,
    minimum_score: float = 0.72,
) -> list[ArtistImageOption]:
    options: list[ArtistImageOption] = []
    seen: set[str] = set()
    response = requests.get(
        artist_image_sources._ITUNES_SEARCH_URL,
        params={
            'term': artist_name,
            'entity': 'musicArtist',
            'limit': 5,
        },
        headers={'User-Agent': USER_AGENT},
        timeout=10,
    )
    response.raise_for_status()
    match = artist_image_sources._best_name_match(
        response.json().get('results') or [],
        artist_name,
        key='artistName',
        minimum=minimum_score,
    )
    if not match:
        return options
    label = str(match.get('artistName') or artist_name).strip()
    artist_url = str(match.get('artistLinkUrl') or '').strip()
    if not artist_url:
        return options
    page = requests.get(
        artist_url,
        headers={'User-Agent': artist_image_sources._SPOTIFY_UA},
        timeout=10,
    )
    page.raise_for_status()
    image_match = artist_image_sources._APPLE_OG_IMAGE_RE.search(page.text)
    if not image_match:
        return options
    image_url = artist_image_sources._upgrade_mzstatic_url(
        image_match.group(1).strip()
    )
    if not image_url:
        return options
    _append_option(
        options,
        seen,
        option_id=f'apple-music:{label.casefold()}',
        source='Apple Music',
        label=label,
        subtitle='Apple Music artist page',
        image_url=image_url,
    )
    return options


def list_discogs_artist_image_options(
    artist_name: str,
    *,
    discogs_token: str = '',
    limit: int = 3,
    minimum_score: float = 0.72,
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
            timeout=10,
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
        thumb = str(item.get('thumb') or '').strip()
        if thumb:
            _append_option(
                options,
                seen,
                option_id=f'discogs:{artist_id}:thumb',
                source='Discogs',
                label=label,
                subtitle=f'{int(score * 100)}% name match',
                image_url=thumb,
            )
            continue
        try:
            detail = requests.get(
                f'https://api.discogs.com/artists/{artist_id}',
                headers=artist_image_sources._discogs_headers(discogs_token),
                timeout=10,
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


def list_deezer_artist_image_options(
    artist_name: str,
    *,
    limit: int = 3,
    minimum_score: float = 0.72,
) -> list[ArtistImageOption]:
    options: list[ArtistImageOption] = []
    seen: set[str] = set()
    for item in artist_image_sources._deezer_artist_items(
        artist_name,
        limit=limit,
    ):
        label = str(item.get('name') or '').strip()
        if not label:
            continue
        score = artist_image_sources._name_ratio(label, artist_name)
        if score < minimum_score:
            continue
        image_url = artist_image_sources._best_deezer_picture(item)
        if not image_url:
            continue
        artist_id = str(item.get('id') or '').strip() or label
        _append_option(
            options,
            seen,
            option_id=f'deezer:{artist_id}',
            source='Deezer',
            label=label,
            subtitle=f'{int(score * 100)}% name match',
            image_url=image_url,
        )
    return options


def list_youtube_music_artist_image_options(
    artist_name: str,
    *,
    limit: int = 3,
    minimum_score: float = 0.72,
) -> list[ArtistImageOption]:
    options: list[ArtistImageOption] = []
    seen: set[str] = set()
    for item in artist_image_sources._youtube_music_artist_items(
        artist_name,
        limit=limit,
    ):
        label = str(item.get('artist') or '').strip()
        if not label:
            continue
        score = artist_image_sources._name_ratio(label, artist_name)
        if score < minimum_score:
            continue
        image_url = artist_image_sources._best_youtube_music_image_url(item)
        if not image_url:
            continue
        browse_id = str(item.get('browseId') or '').strip() or label
        _append_option(
            options,
            seen,
            option_id=f'youtube-music:{browse_id}',
            source='YouTube Music',
            label=label,
            subtitle=f'{int(score * 100)}% name match',
            image_url=image_url,
        )
    return options


def _musicbrainz_search_artists(
    artist_name: str,
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    for attempt in range(2):
        try:
            _throttle_musicbrainz()
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
            musicbrainz_module._LAST_REQUEST_AT = time.monotonic()
            if response.status_code == 503 and attempt == 0:
                time.sleep(2.0)
                continue
            response.raise_for_status()
            return [
                item
                for item in response.json().get('artists') or []
                if isinstance(item, dict)
            ]
        except Exception:
            if attempt == 0:
                continue
            logger.opt(exception=True).debug(
                'MusicBrainz artist search failed for {!r}',
                artist_name,
            )
    return []


def list_musicbrainz_artist_image_options(
    artist_name: str,
    *,
    limit: int = 3,
    minimum_score: float = 0.72,
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
        image_url = _wikimedia_artist_image_url(mbid) or ''
        if not image_url:
            continue
        _append_option(
            options,
            seen,
            option_id=f'musicbrainz:{mbid}',
            source='MusicBrainz',
            label=label,
            subtitle=f'{int(score * 100)}% name match',
            image_url=image_url,
        )
    return options


def _merge_source_options(
    options: list[ArtistImageOption],
    seen: set[str],
    source_options: list[ArtistImageOption],
) -> None:
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


def _collect_for_search_name(
    artist_name: str,
    *,
    discogs_token: str = '',
    per_source_limit: int = 3,
) -> list[ArtistImageOption]:
    tasks = {
        'youtube': lambda: list_youtube_music_artist_image_options(
            artist_name,
            limit=per_source_limit,
        ),
        'deezer': lambda: list_deezer_artist_image_options(
            artist_name,
            limit=per_source_limit,
        ),
        'spotify': lambda: list_spotify_artist_image_options(
            artist_name,
            limit=per_source_limit,
        ),
        'apple': lambda: list_apple_music_artist_image_options(artist_name),
        'discogs': lambda: list_discogs_artist_image_options(
            artist_name,
            discogs_token=discogs_token,
            limit=per_source_limit,
        ),
        'musicbrainz': lambda: list_musicbrainz_artist_image_options(
            artist_name,
            limit=per_source_limit,
        ),
    }
    collected: list[ArtistImageOption] = []
    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {
            executor.submit(fetch): label for label, fetch in tasks.items()
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                collected.extend(future.result())
            except Exception:
                logger.opt(exception=True).debug(
                    'Artist image source {} failed for {!r}',
                    label,
                    artist_name,
                )
    return collected


def collect_artist_image_options(
    artist_name: str,
    *,
    discogs_token: str = '',
    jellyfin_artist_id: str = '',
    jellyfin_label: str = '',
    per_source_limit: int = 3,
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

    for search_name in artist_search_names(artist_name):
        _merge_source_options(
            options,
            seen,
            _collect_for_search_name(
                search_name,
                discogs_token=discogs_token,
                per_source_limit=per_source_limit,
            ),
        )

    return options
