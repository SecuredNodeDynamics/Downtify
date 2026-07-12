"""Build a lightweight browse index for downloaded library files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from .genres import browse_genre, canonical_genre
from .metadata_repair import (
    AUDIO_EXTENSIONS,
    _genre_from_path,
    _song_from_file,
    safe_library_path,
)
from .musicbrainz import (
    enrich_song_metadata,
    lookup_artist_genre,
    remember_artist_genre,
    warm_artist_genre_cache,
)

# Keep the listing in sync with the "is it already downloaded?" check
# (downloader._AUDIO_EXTENSIONS) and metadata repair so a file can never count
# as "owned" in search yet be invisible in the library. On the embedded Android
# backend a track can land as an ``.mp4``/``.wav`` container, so those must be
# listable too.
_LIST_EXTENSIONS = AUDIO_EXTENSIONS | {'.wav'}
_ALBUM_GENRE_CACHE_LOADED = False
_ALBUM_GENRE_CACHE: dict[str, str] = {}


def _data_dir() -> Path:
    import os

    return Path(os.getenv('DOWNTIFY_DATA_DIR', os.getenv('DATABASE_DIR', '/data')))


def _album_genre_cache_path() -> Path:
    return _data_dir() / 'album_genre_cache.json'


def _load_album_genre_cache() -> None:
    global _ALBUM_GENRE_CACHE_LOADED
    if _ALBUM_GENRE_CACHE_LOADED:
        return
    path = _album_genre_cache_path()
    if path.exists():
        try:
            import json

            payload = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(payload, dict):
                for key, value in payload.items():
                    genre = canonical_genre(str(value or ''))
                    if isinstance(key, str) and genre:
                        _ALBUM_GENRE_CACHE[key] = genre
        except Exception:
            pass
    _ALBUM_GENRE_CACHE_LOADED = True


def _save_album_genre_cache() -> None:
    import json

    path = _album_genre_cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(_ALBUM_GENRE_CACHE, indent=2, sort_keys=True),
            encoding='utf-8',
        )
    except Exception:
        pass


def _remember_album_genre(album_key: str, genre: str) -> None:
    key = str(album_key or '').strip()
    label = canonical_genre(genre)
    if not key or not label:
        return
    _load_album_genre_cache()
    _ALBUM_GENRE_CACHE[key] = label
    _save_album_genre_cache()


def _album_genre_from_cache(album_key: str) -> str:
    key = str(album_key or '').strip()
    if not key:
        return ''
    _load_album_genre_cache()
    return canonical_genre(_ALBUM_GENRE_CACHE.get(key, ''))


def _path_parts(file: str) -> list[str]:
    return [part.strip() for part in str(file or '').split('/') if part.strip()]


def _unique_artist_names(*values: Any) -> list[str]:
    artists: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        if isinstance(value, list):
            items = value
        else:
            items = re.split(r'[,/&]+', str(value))
        for item in items:
            name = str(item or '').strip()
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            artists.append(name)
    return artists


def _artists_for_entry(
    file: str,
    song: dict[str, Any],
    primary: str,
) -> list[str]:
    parts = _path_parts(file)
    folder_artist = parts[0] if len(parts) > 1 else ''
    artists = _unique_artist_names(
        song.get('artists'),
        primary,
        folder_artist,
    )
    if artists:
        return artists
    if primary:
        return [primary]
    return []


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
        if re.match(r'^\d+\s*-\s*', stem):
            title = re.sub(r'^\d+\s*-\s*', '', stem).strip() or stem
            return {'name': title, 'artists': [], 'album_name': '', 'genre': ''}
        if ' - ' in stem:
            artist, title = stem.split(' - ', 1)
            return {
                'name': title.strip(),
                'artists': [artist.strip()],
                'album_name': '',
                'genre': '',
            }
        return {'name': stem, 'artists': [], 'album_name': '', 'genre': ''}


def _album_folder_key(file: str) -> str:
    parts = _path_parts(file)
    if len(parts) > 2:
        return f'{parts[0]}\0{parts[1]}'
    return ''


def _library_genre_fields(genre: str) -> dict[str, str]:
    canonical = canonical_genre(genre)
    browse = browse_genre(canonical) if canonical else ''
    return {
        'genre': canonical,
        'browse_genre': browse or canonical,
    }


def enrich_library_genres(items: list[dict[str, str]]) -> list[dict[str, str]]:
    """Fill missing genres from album/artist peers and the on-disk artist cache."""

    if not items:
        return items

    by_artist: dict[str, str] = {}
    by_album: dict[str, str] = {}

    for item in items:
        genre = canonical_genre(item.get('genre') or '')
        if genre:
            fields = _library_genre_fields(genre)
            item.update(fields)
            artist = str(item.get('artist') or '').strip()
            if artist and artist not in by_artist:
                by_artist[artist] = genre
            album_key = _album_folder_key(str(item.get('file') or ''))
            if album_key and album_key not in by_album:
                by_album[album_key] = genre

    for item in items:
        if canonical_genre(item.get('genre') or ''):
            continue
        file = str(item.get('file') or '')
        artist = str(item.get('artist') or '').strip()
        genre = canonical_genre(
            by_album.get(_album_folder_key(file))
            or by_artist.get(artist)
            or _album_genre_from_cache(_album_folder_key(file))
            or lookup_artist_genre(artist, fetch=False)
        )
        if genre:
            item.update(_library_genre_fields(genre))

    return items


def _genre_for_entry(
    path: Path,
    song: dict[str, Any],
    artist: str,
    artist_genres: dict[str, str],
    *,
    fetch_missing_genres: bool,
) -> str:
    genre = canonical_genre(
        str(song.get('genre') or '').strip() or _genre_from_path(path)
    )
    if genre or not artist or artist == 'Unknown Artist':
        return genre

    if artist in artist_genres:
        return artist_genres[artist]

    genre = canonical_genre(
        lookup_artist_genre(artist, fetch=fetch_missing_genres)
    )
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
    if not album:
        album = _album_name_from_tags(path)
    genre = _genre_for_entry(
        path,
        song,
        artist,
        artist_genres,
        fetch_missing_genres=fetch_missing_genres,
    )
    title = str(song.get('name') or path.stem).strip() or path.stem
    artists = _artists_for_entry(relative, song, artist)
    return {
        'file': relative,
        'title': title,
        'artist': artist,
        'artists': artists,
        'album': album,
        **_library_genre_fields(genre),
    }


def _album_name_from_tags(path: Path) -> str:
    try:
        from mutagen.id3 import ID3

        tags = ID3(str(path))
        frame = tags.get('TALB')
        if frame is None:
            return ''
        text = getattr(frame, 'text', None)
        if text:
            return str(text[0]).strip()
        return str(frame).strip()
    except Exception:
        return ''


def _artists_from_path_tags(path: Path) -> list[str]:
    try:
        artists = _song_from_file(path).get('artists') or []
        if artists:
            return _unique_artist_names(artists)
    except Exception:
        pass
    try:
        from mutagen.id3 import ID3

        tags = ID3(str(path))
        frame = tags.get('TPE1')
        if frame is None:
            return []
        text = getattr(frame, 'text', None)
        value = ', '.join(str(item) for item in text) if text else str(frame)
        return _unique_artist_names(value)
    except Exception:
        return []


def read_library_entry_fast(
    root: Path,
    relative: str,
) -> dict[str, str]:
    """Build a browse entry from paths, reading tags only when needed."""

    path = safe_library_path(root, relative)
    parts = _path_parts(relative)
    song: dict[str, Any] = {}
    if len(parts) <= 2:
        song = _song_from_file_safe(path)
    else:
        song = {'artists': _artists_from_path_tags(path)}
    artist = _artist_name(relative, song) or 'Unknown Artist'
    album = _album_name(relative, song)
    if not album:
        album = _album_name_from_tags(path)
    stem = path.stem
    tagged_title = str(song.get('name') or '').strip()
    title = tagged_title or (
        stem.split(' - ', 1)[-1].strip() if ' - ' in stem else stem
    )
    genre = canonical_genre(
        str(song.get('genre') or '').strip() or _genre_from_path(path)
    )
    genre_fields = _library_genre_fields(genre) if genre else {
        'genre': '',
        'browse_genre': '',
    }
    artists = _artists_for_entry(relative, song, artist)
    return {
        'file': relative,
        'title': title or stem,
        'artist': artist,
        'artists': artists,
        'album': album,
        **genre_fields,
    }


def list_library_files_fast(root: Path) -> list[dict[str, str]]:
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
            items.append(read_library_entry_fast(base, relative))
        except ValueError:
            continue
    return enrich_library_genres(items)


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
    return enrich_library_genres(items)


def _album_samples_without_genre(
    items: list[dict[str, str]],
) -> list[tuple[str, str]]:
    seen: set[str] = set()
    samples: list[tuple[str, str]] = []
    for item in items:
        if canonical_genre(item.get('genre') or ''):
            continue
        album_key = _album_folder_key(str(item.get('file') or ''))
        if not album_key or album_key in seen:
            continue
        seen.add(album_key)
        samples.append((album_key, str(item.get('file') or '')))
    return samples


def warm_library_genres(
    root: Path,
    *,
    progress_cb: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, int]:
    """Populate genre cache and album tags via MusicBrainz in the background."""

    items = list_library_files(root, fetch_missing_genres=False)
    missing_artists = sorted(
        {
            item['artist']
            for item in items
            if item['artist']
            and item['artist'] != 'Unknown Artist'
            and not canonical_genre(item.get('genre') or '')
        }
    )
    if missing_artists:
        warm_artist_genre_cache(missing_artists)

    items = enrich_library_genres(list_library_files(root, fetch_missing_genres=False))
    album_samples = _album_samples_without_genre(items)
    albums_warmed = 0
    for index, (_album_key, relative) in enumerate(album_samples, start=1):
        try:
            path = safe_library_path(root, relative)
            song = _song_from_file_safe(path)
            enriched = enrich_song_metadata(song)
            genre = canonical_genre(str(enriched.get('genre') or ''))
            if genre:
                albums_warmed += 1
                remember_artist_genre(_artist_name(relative, enriched), genre)
                _remember_album_genre(_album_key, genre)
        except Exception:
            continue
        if progress_cb is not None:
            progress_cb({
                'phase': 'albums',
                'current': index,
                'total': len(album_samples),
                'albums_warmed': albums_warmed,
            })

    final_items = enrich_library_genres(
        list_library_files(root, fetch_missing_genres=False)
    )
    tagged = sum(
        1 for item in final_items if canonical_genre(item.get('genre') or '')
    )
    return {
        'artists_warmed': len(missing_artists),
        'albums_warmed': albums_warmed,
        'tagged_tracks': tagged,
        'total_tracks': len(final_items),
    }


def schedule_artist_genre_warmup(root: Path) -> None:
    """Warm the artist genre cache for artists missing file tags."""

    warm_library_genres(root)


def media_item_key(item: dict[str, Any]) -> str:
    for field in ('song_id', 'browse_id', 'url'):
        value = str(item.get(field) or '').strip()
        if value:
            return value
    return ''


def _artist_keys(item: dict[str, Any]) -> set[str]:
    from .downloader import _normalize_duplicate_key

    keys: set[str] = set()
    for artist in item.get('artists') or []:
        key = _normalize_duplicate_key(str(artist or ''))
        if key:
            keys.add(key)
    combined = str(item.get('artist') or '').strip()
    if combined:
        for part in re.split(r'[,/&]+', combined):
            key = _normalize_duplicate_key(part)
            if key:
                keys.add(key)
    return keys


def _artist_keys_match(left: set[str], right: str) -> bool:
    from .downloader import _normalize_duplicate_key

    if not left:
        return True
    item_key = _normalize_duplicate_key(right)
    if not item_key:
        return False
    if item_key in left:
        return True
    return any(
        ak in item_key or item_key in ak for ak in left if ak and item_key
    )


def _library_item_artist_names(item: dict[str, Any]) -> list[str]:
    names = _unique_artist_names(item.get('artists'), item.get('artist'))
    primary = str(item.get('artist') or '').strip()
    if names:
        return names
    return [primary] if primary else []


def track_in_library_from_metadata(
    song: dict[str, Any],
    items: list[dict[str, str]],
) -> bool:
    from .downloader import _normalize_duplicate_key

    title_key = _normalize_duplicate_key(str(song.get('name') or ''))
    if not title_key:
        return False
    artist_keys = _artist_keys(song)
    for item in items:
        item_title = _normalize_duplicate_key(str(item.get('title') or ''))
        if item_title != title_key:
            continue
        for lib_artist in _library_item_artist_names(item):
            if _artist_keys_match(artist_keys, lib_artist):
                return True
    return False


def album_in_library(
    album: dict[str, Any],
    items: list[dict[str, str]],
) -> bool:
    from .downloader import _normalize_duplicate_key

    album_name = str(album.get('name') or album.get('album_name') or '').strip()
    if not album_name:
        return False

    album_key = _normalize_duplicate_key(album_name)
    if not album_key:
        return False

    expected_tracks = _expected_album_track_count(album)
    matched = 0
    artist_keys = _artist_keys(album)
    for item in items:
        if _normalize_duplicate_key(str(item.get('album') or '')) != album_key:
            continue
        for lib_artist in _library_item_artist_names(item):
            if _artist_keys_match(artist_keys, lib_artist):
                matched += 1
                break
    if expected_tracks > 0:
        return matched >= expected_tracks
    return matched > 0


def _expected_album_track_count(album: dict[str, Any]) -> int:
    for field in (
        'track_count',
        'album_track_total',
        'tracks_count',
        'total_tracks',
    ):
        try:
            count = int(album.get(field) or 0)
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            return count
    tracks = album.get('tracks')
    return len(tracks) if isinstance(tracks, list) else 0


def media_in_library(
    item: dict[str, Any],
    *,
    downloader: Any,
    library_items: list[dict[str, str]],
) -> bool:
    media_type = str(item.get('media_type') or 'track').strip().lower()
    if media_type == 'album':
        return album_in_library(item, library_items)
    if downloader is not None and downloader.duplicate_filename_for(item):
        return True
    return track_in_library_from_metadata(item, library_items)


_library_changed_callbacks: list[Callable[[], None]] = []


def register_library_changed_callback(callback: Callable[[], None]) -> None:
    _library_changed_callbacks.append(callback)


def notify_library_changed() -> None:
    for callback in list(_library_changed_callbacks):
        try:
            callback()
        except Exception:
            pass
