"""Jellyfin-compatible metadata formatter."""

from __future__ import annotations

from typing import Any


def _coerce_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        iv = int(value)
    except (TypeError, ValueError):
        return None
    return iv if iv > 0 else None


def _split_artists(value: Any) -> list[str]:
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    out.append(text)
            elif isinstance(item, dict):
                name = str(item.get('name') or '').strip()
                if name:
                    out.append(name)
        return out

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        for sep in [' / ', ';', ',', ' & ']:
            if sep in text:
                parts = [a.strip() for a in text.split(sep)]
                return [a for a in parts if a]
        return [text]

    return []


def format_for_jellyfin(song: dict[str, Any]) -> dict[str, Any]:
    out = dict(song)

    artists = _split_artists(song.get('artists'))
    if not artists:
        artists = _split_artists(song.get('artist'))
    out['artists'] = artists

    is_compilation = len(artists) > 1 or bool(song.get('compilation'))
    out['compilation'] = is_compilation

    album_artist = str(song.get('album_artist') or '').strip()
    if not album_artist:
        album_artist = 'Various Artists' if is_compilation else (
            artists[0] if artists else 'Unknown Artist'
        )
    out['album_artist'] = album_artist

    disc_number = _coerce_int(song.get('disc_number'))
    out['disc_number'] = disc_number if disc_number is not None else 1
    out['disc_total'] = _coerce_int(song.get('disc_total'))

    release_date = str(song.get('release_date') or '').strip()
    year = str(song.get('year') or '').strip()
    if not year and len(release_date) >= 4 and release_date[:4].isdigit():
        year = release_date[:4]

    out['release_date'] = release_date
    out['year'] = year

    out['track_number'] = _coerce_int(song.get('track_number'))
    out['album_track_total'] = _coerce_int(song.get('album_track_total'))

    out['album_name'] = str(song.get('album_name') or '').strip() or 'Unknown Album'
    out['name'] = str(song.get('name') or '').strip() or 'Unknown Title'

    return out
