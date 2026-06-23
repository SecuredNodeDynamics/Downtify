"""Build a lightweight browse index for downloaded library files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mutagen import File as MutagenFile

from .metadata_repair import AUDIO_EXTENSIONS, _first, _song_from_file, safe_library_path

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
            }
        return {'name': stem, 'artists': [], 'album_name': ''}


def _genre_name(path: Path) -> str:
    try:
        audio = MutagenFile(str(path), easy=True)
        if audio is not None and audio.tags:
            genre = _first(audio.tags, ['genre', '\xa9gen', 'TCON'])
            if genre:
                return genre
    except Exception:
        pass
    try:
        from mutagen.id3 import ID3

        tags = ID3(str(path))
        return _first(tags, ['TCON'])
    except Exception:
        return ''


def read_library_entry(root: Path, relative: str) -> dict[str, str]:
    path = safe_library_path(root, relative)
    song = _song_from_file_safe(path)
    artist = _artist_name(relative, song) or 'Unknown Artist'
    album = _album_name(relative, song)
    genre = _genre_name(path)
    title = str(song.get('name') or path.stem).strip() or path.stem
    return {
        'file': relative,
        'title': title,
        'artist': artist,
        'album': album,
        'genre': genre,
    }


def list_library_files(root: Path) -> list[dict[str, str]]:
    base = root.resolve()
    if not base.exists():
        return []

    items: list[dict[str, str]] = []
    for path in sorted(base.rglob('*')):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _LIST_EXTENSIONS:
            continue
        relative = path.relative_to(base).as_posix()
        try:
            items.append(read_library_entry(base, relative))
        except ValueError:
            continue
    return items
