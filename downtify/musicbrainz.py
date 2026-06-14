"""Conservative MusicBrainz metadata enrichment."""

from __future__ import annotations

import time
from difflib import SequenceMatcher
from typing import Any, Optional

import requests
from loguru import logger

MUSICBRAINZ_RECORDING_URL = 'https://musicbrainz.org/ws/2/recording/'
USER_AGENT = 'Downtify/1.0 (https://github.com/JanzenMediaGroup/Downtify)'

_CACHE: dict[str, Optional[dict[str, Any]]] = {}
_LAST_REQUEST_AT = 0.0


def _norm(value: Any) -> str:
    return ' '.join(str(value or '').casefold().split())


def _ratio(a: Any, b: Any) -> float:
    left = _norm(a)
    right = _norm(b)
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def _artists(song: dict[str, Any]) -> list[str]:
    raw = song.get('artists')
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    artist = str(song.get('artist') or '').strip()
    return [artist] if artist else []


def _artist_credit_names(recording: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for credit in recording.get('artist-credit') or []:
        if isinstance(credit, dict):
            name = str(credit.get('name') or '').strip()
            if name:
                names.append(name)
    return names


def _artist_credit_ids(recording: dict[str, Any]) -> list[dict[str, str]]:
    artists: list[dict[str, str]] = []
    seen: set[str] = set()
    for credit in recording.get('artist-credit') or []:
        if not isinstance(credit, dict):
            continue
        artist = credit.get('artist')
        if not isinstance(artist, dict):
            continue
        artist_id = str(artist.get('id') or '').strip()
        name = str(credit.get('name') or artist.get('name') or '').strip()
        if not artist_id or artist_id in seen:
            continue
        artists.append({'id': artist_id, 'name': name})
        seen.add(artist_id)
    return artists


def _artist_credit_text(recording: dict[str, Any]) -> str:
    names = _artist_credit_names(recording)
    return ' '.join(names)


def _release_date(release: dict[str, Any]) -> str:
    return str(release.get('date') or '').strip()


def _best_release(
    recording: dict[str, Any],
    target_album: str,
) -> Optional[dict[str, Any]]:
    releases = [
        release
        for release in recording.get('releases') or []
        if isinstance(release, dict)
    ]
    if not releases:
        return None
    if target_album:
        return max(
            releases,
            key=lambda release: (
                _ratio(release.get('title'), target_album),
                bool(_release_date(release)),
            ),
        )
    return max(releases, key=lambda release: bool(_release_date(release)))


def _candidate_score(
    recording: dict[str, Any],
    song: dict[str, Any],
) -> float:
    title_score = _ratio(recording.get('title'), song.get('name')) * 45

    target_artists = _artists(song)
    recording_artists = _artist_credit_names(recording)
    artist_scores: list[float] = []
    for target in target_artists:
        best = 0.0
        for candidate in recording_artists:
            best = max(best, _ratio(candidate, target))
        artist_scores.append(best)
    artist_score = (
        sum(artist_scores) / len(artist_scores) * 35
        if artist_scores
        else 0.0
    )
    if len(target_artists) > 1:
        artist_score += _ratio(
            _artist_credit_text(recording),
            ' '.join(target_artists),
        ) * 10

    album_score = 0.0
    album = str(song.get('album_name') or '').strip()
    release = _best_release(recording, album)
    if album and release:
        album_score = _ratio(release.get('title'), album) * 15

    duration_score = 0.0
    target_ms = song.get('duration_ms')
    candidate_ms = recording.get('length')
    try:
        diff = abs(int(candidate_ms) - int(target_ms))
    except (TypeError, ValueError):
        pass
    else:
        if diff <= 2500:
            duration_score = 5
        elif diff <= 8000:
            duration_score = 2

    return title_score + min(45, artist_score) + album_score + duration_score


def _musicbrainz_queries(
    title: str,
    artists: list[str],
    album: str,
) -> list[str]:
    artist_queries: list[str] = []
    if len(artists) > 1:
        joined = ' '.join(artists)
        artist_queries.append(f'artist:"{joined}"')
        artist_queries.append(
            ' AND '.join(f'artist:"{artist}"' for artist in artists)
        )
    artist_queries.extend(f'artist:"{artist}"' for artist in artists)

    queries: list[str] = []
    for artist_query in artist_queries:
        query = f'recording:"{title}" AND {artist_query}'
        if album:
            query += f' AND release:"{album}"'
        if query not in queries:
            queries.append(query)
    return queries


def _query(song: dict[str, Any]) -> Optional[dict[str, Any]]:
    global _LAST_REQUEST_AT

    title = str(song.get('name') or '').strip()
    artists = _artists(song)
    if not title or not artists:
        return None

    album = str(song.get('album_name') or '').strip()
    cache_key = (
        f'{_norm(title)}|{_norm(" ".join(artists))}|{_norm(album)}'
    )
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    queries = _musicbrainz_queries(title, artists, album)
    recordings: list[dict[str, Any]] = []

    try:
        seen_ids: set[str] = set()
        multi_query_count = 2 if len(artists) > 1 else 0
        for index, query in enumerate(queries):
            if recordings and index >= multi_query_count:
                break
            elapsed = time.monotonic() - _LAST_REQUEST_AT
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)
            response = requests.get(
                MUSICBRAINZ_RECORDING_URL,
                params={'query': query, 'fmt': 'json', 'limit': 8},
                headers={'User-Agent': USER_AGENT},
                timeout=8,
            )
            _LAST_REQUEST_AT = time.monotonic()
            response.raise_for_status()
            payload = response.json()
            for item in payload.get('recordings') or []:
                if not isinstance(item, dict):
                    continue
                recording_id = str(item.get('id') or '')
                if recording_id and recording_id in seen_ids:
                    continue
                if recording_id:
                    seen_ids.add(recording_id)
                recordings.append(item)
    except Exception:
        logger.opt(exception=True).warning(
            'MusicBrainz lookup failed for {!r} by {!r}',
            title,
            ', '.join(artists),
        )
        _CACHE[cache_key] = None
        return None

    if not recordings:
        _CACHE[cache_key] = None
        return None

    best = max(recordings, key=lambda item: _candidate_score(item, song))
    score = _candidate_score(best, song)
    if score < 72:
        logger.info(
            'MusicBrainz match rejected for {!r}: score={:.1f}',
            title,
            score,
        )
        _CACHE[cache_key] = None
        return None

    _CACHE[cache_key] = best
    return best


def enrich_song_metadata(song: dict[str, Any]) -> dict[str, Any]:
    """Return *song* with high-confidence MusicBrainz fields merged in."""

    recording = _query(song)
    if recording is None:
        return song

    enriched = dict(song)
    title = str(recording.get('title') or '').strip()
    if title:
        enriched['name'] = title

    artists = _artist_credit_names(recording)
    if artists:
        enriched['artists'] = artists
        enriched['artist'] = ', '.join(artists)

    release = _best_release(recording, str(song.get('album_name') or ''))
    if release:
        album = str(release.get('title') or '').strip()
        if album:
            enriched['album_name'] = album
        date = _release_date(release)
        if date:
            enriched['release_date'] = date
            enriched['year'] = date[:4]

    enriched['musicbrainz_recording_id'] = recording.get('id')
    artist_ids = _artist_credit_ids(recording)
    if artist_ids:
        enriched['musicbrainz_artist_ids'] = artist_ids
    if release and release.get('id'):
        enriched['musicbrainz_release_id'] = release.get('id')

    return enriched
