"""Build a lightweight browse index for downloaded library files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .metadata_repair import (
    AUDIO_EXTENSIONS,
    _genre_from_path,
    _song_from_file,
    safe_library_path,
)
from .musicbrainz import lookup_artist_genre, warm_artist_genre_cache

_LIST_EXTENSIONS = {ext for ext in AUDIO_EXTENSIONS if ext != '.mp4'}


def _path_parts(file: str) -> list[str]:
    return [part.strip() for part in str(file or '').split('/') if part.strip()]


def _artist_name(file: str, song: dict[str, Any]) -> str:
    parts = _path_parts(file)
    if len(parts) > 1:
        return parts[0]
    artists = song.get('artists') or []
    if artists:
        return str(artists[0]).strip()
    stem = Path(file).stem
    if ' - ' in stem:
        return stem.split(' - ', 1)[0].strip()
    return ''


def _album_name(file: str, song: dict[str, Any]) -> str:
    parts = _path_parts(file)
    if len(parts) > 2:
        return parts[1]
    return str(song.get('album_name') or '').strip()


def _song_from_file_safe(path: Path) -> dict[str, Any]:
    try:
        return _song_from_file(path)
    except Exception:
        stem = path.stem
        if ' - ' in stem:
            artist, title = stem.split(' - ', 1)
            return {
                'name': title.strip(),
                'artists': [artist.strip()],
                'album_name': '',
                'genre': '',
            }
        return {'name': stem, 'artists': [], 'album_name': '', 'genre': ''}


def _genre_for_entry(
    path: Path,
    song: dict[str, Any],
    artist: str,
    artist_genres: dict[str, str],
    *,
    fetch_missing_genres: bool,
) -> str:
    genre = str(song.get('genre') or '').strip() or _genre_from_path(path)
    if genre or not artist or artist == 'Unknown Artist':
        return genre

    if artist in artist_genres:
        return artist_genres[artist]

    genre = lookup_artist_genre(artist, fetch=fetch_missing_genres)
    artist_genres[artist] = genre
    return genre


def read_library_entry(
    root: Path,
    relative: str,
    artist_genres: dict[str, str],
    *,
    fetch_missing_genres: bool,
) -> dict[str, str]:
    path = safe_library_path(root, relative)
    song = _song_from_file_safe(path)
    artist = _artist_name(relative, song) or 'Unknown Artist'
    album = _album_name(relative, song)
    genre = _genre_for_entry(
        path,
        song,
        artist,
        artist_genres,
        fetch_missing_genres=fetch_missing_genres,
    )
    title = str(song.get('name') or path.stem).strip() or path.stem
    return {
        'file': relative,
        'title': title,
        'artist': artist,
        'album': album,
        'genre': genre,
    }


def list_library_files(
    root: Path,
    *,
    fetch_missing_genres: bool = True,
) -> list[dict[str, str]]:
    base = root.resolve()
    if not base.exists():
        return []

    artist_genres: dict[str, str] = {}
    items: list[dict[str, str]] = []
    for path in sorted(base.rglob('*')):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _LIST_EXTENSIONS:
            continue
        relative = path.relative_to(base).as_posix()
        try:
            items.append(
                read_library_entry(
                    base,
                    relative,
                    artist_genres,
                    fetch_missing_genres=fetch_missing_genres,
                )
            )
        except ValueError:
            continue
    return items


def schedule_artist_genre_warmup(root: Path) -> None:
    """Warm the artist genre cache for artists missing file tags."""

    items = list_library_files(root, fetch_missing_genres=False)
    artists = sorted(
        {
            item['artist']
            for item in items
            if item['artist']
            and item['artist'] != 'Unknown Artist'
            and not item.get('genre')
        }
    )
    if artists:
        warm_artist_genre_cache(artists)
