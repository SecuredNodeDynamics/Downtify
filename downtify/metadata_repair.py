"""Scan and repair existing library metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from loguru import logger
from mutagen import File as MutagenFile

from .artist_art import missing_artist_image_items, save_missing_artist_images
from .musicbrainz import enrich_song_metadata

AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.mp4', '.aac', '.flac', '.ogg', '.opus'}


def _first(tags: Any, keys: list[str]) -> str:
    if not tags:
        return ''
    for key in keys:
        value = tags.get(key)
        if isinstance(value, list) and value:
            return str(value[0])
        if value:
            return str(value)
    return ''


def _artists(tags: Any) -> list[str]:
    if tags:
        for key in ['artist', 'artists', '\xa9ART', 'TPE1']:
            value = tags.get(key)
            if isinstance(value, list) and value:
                artists = [
                    str(item).strip()
                    for item in value
                    if str(item).strip()
                ]
                if artists:
                    return artists
            if value:
                break
        else:
            value = ''
    else:
        value = ''
    if not value:
        return []
    for separator in (' / ', ';', ','):
        if separator in value:
            return [part.strip() for part in value.split(separator) if part.strip()]
    return [value.strip()]


def _song_from_file(path: Path) -> dict[str, Any]:
    audio = MutagenFile(str(path), easy=True)
    if audio is None:
        stem = path.stem
        if ' - ' in stem:
            artist, title = stem.split(' - ', 1)
            return {'name': title.strip(), 'artists': [artist.strip()]}
        return {'name': stem, 'artists': []}

    tags = audio.tags or {}
    release_date = _first(tags, ['date', '\xa9day', 'TDRC'])
    song = {
        'name': _first(tags, ['title', '\xa9nam', 'TIT2']) or path.stem,
        'artists': _artists(tags),
        'album_name': _first(tags, ['album', '\xa9alb', 'TALB']),
        'release_date': release_date,
        'year': release_date[:4] if len(release_date) >= 4 else '',
        'track_number': _first(tags, ['tracknumber', 'trkn', 'TRCK']),
        'disc_number': _first(tags, ['discnumber', 'disk', 'TPOS']),
        'musicbrainz_artist_ids': [
            {'id': artist_id, 'name': ''}
            for artist_id in _artists_from_ids(tags)
        ],
    }
    length = getattr(getattr(audio, 'info', None), 'length', None)
    if length:
        song['duration_ms'] = int(float(length) * 1000)
    return song


def _artists_from_ids(tags: Any) -> list[str]:
    if not tags:
        return []
    for key in ['musicbrainz_artistid', 'MusicBrainz Artist Id', 'TXXX:MusicBrainz Artist Id']:
        value = tags.get(key)
        if isinstance(value, list) and value:
            return [str(item).strip() for item in value if str(item).strip()]
        if value:
            text = str(value)
            for separator in (' / ', ';', ','):
                if separator in text:
                    return [
                        part.strip()
                        for part in text.split(separator)
                        if part.strip()
                    ]
            return [text.strip()]
    return []


def _public_song(song: dict[str, Any]) -> dict[str, Any]:
    release_date = str(song.get('release_date') or '')
    year = str(song.get('year') or '')
    return {
        'name': song.get('name') or '',
        'artists': song.get('artists') or [],
        'album_name': song.get('album_name') or '',
        'release_date': release_date,
        'year': year or (release_date[:4] if len(release_date) >= 4 else ''),
        'track_number': song.get('track_number') or '',
        'disc_number': song.get('disc_number') or '',
        'musicbrainz_recording_id': song.get('musicbrainz_recording_id') or '',
        'musicbrainz_release_id': song.get('musicbrainz_release_id') or '',
        'musicbrainz_artist_ids': song.get('musicbrainz_artist_ids') or [],
    }


def _changes(
    current: dict[str, Any],
    candidate: dict[str, Any],
) -> list[dict[str, str]]:
    fields = [
        ('name', 'Title'),
        ('artists', 'Artist'),
        ('album_name', 'Album'),
        ('release_date', 'Release date'),
        ('year', 'Year'),
    ]
    changes: list[dict[str, str]] = []
    for key, label in fields:
        before = current.get(key) or []
        after = candidate.get(key) or []
        if isinstance(before, list):
            before = ', '.join(str(item) for item in before if item)
        if isinstance(after, list):
            after = ', '.join(str(item) for item in after if item)
        if str(before or '') != str(after or ''):
            changes.append({
                'field': key,
                'label': label,
                'before': str(before or ''),
                'after': str(after or ''),
            })
    return changes


def _scan_item(root: Path, path: Path) -> dict[str, Any]:
    current = _song_from_file(path)
    candidate = enrich_song_metadata(current)
    matched = bool(candidate.get('musicbrainz_recording_id'))
    changes = _changes(current, candidate) if matched else []
    return {
        'file': path.relative_to(root).as_posix(),
        'current': _public_song(current),
        'candidate': _public_song(candidate) if matched else None,
        'matched': matched,
        'changes': changes,
    }


ProgressCallback = Callable[[dict[str, Any]], None]


def scan_library(
    root: Path,
    limit: int = 100,
    start: int = 0,
    progress_cb: ProgressCallback | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    files = [
        path
        for path in root.rglob('*')
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]
    files.sort(key=lambda path: path.relative_to(root).as_posix().casefold())
    total = len(files)
    start = max(0, min(start, total))
    selected = files[start : start + max(1, limit)]
    items: list[dict[str, Any]] = []
    clean_items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    batch_scanned = 0
    for path in selected:
        batch_scanned += 1
        current_offset = start + batch_scanned
        try:
            item = _scan_item(root, path)
        except Exception as exc:
            errors.append({
                'file': path.relative_to(root).as_posix(),
                'error': str(exc),
            })
            item = None
        if item is not None and item['matched'] and item['changes']:
            items.append(item)
        elif item is not None:
            clean_items.append(item)
        if progress_cb is not None:
            progress_cb({
                'scanned': current_offset,
                'batch_scanned': batch_scanned,
                'total': total,
                'matched': len(items),
                'items': list(items),
                'clean': list(clean_items),
                'start': start,
                'next_offset': current_offset,
            })
    next_offset = start + batch_scanned
    return {
        'root': str(root),
        'scanned': next_offset,
        'batch_scanned': batch_scanned,
        'total': total,
        'matched': len(items),
        'items': items,
        'clean': clean_items,
        'errors': errors,
        'start': start,
        'next_offset': next_offset,
        'complete': next_offset >= total,
    }


def scan_artist_images(root: Path, limit: int = 100) -> dict[str, Any]:
    root = root.resolve()
    files = [
        path
        for path in root.rglob('*')
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]
    files.sort(key=lambda path: path.relative_to(root).as_posix().casefold())
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    scanned = 0
    max_items = max(1, limit)
    for path in files:
        scanned += 1
        current = _song_from_file(path)
        candidate = enrich_song_metadata(current)
        artists = candidate.get('musicbrainz_artist_ids') or []
        for item in missing_artist_image_items(root, path, artists):
            key = (item['artist_id'], item['folder'])
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
            if len(items) >= max_items:
                return {
                    'root': str(root),
                    'scanned': scanned,
                    'total': len(files),
                    'items': items,
                    'matched': len(items),
                }
    return {
        'root': str(root),
        'scanned': scanned,
        'total': len(files),
        'items': items,
        'matched': len(items),
    }


def safe_library_path(root: Path, relative_file: str) -> Path:
    root = root.resolve()
    target = (root / relative_file).resolve()
    if target != root and root not in target.parents:
        raise ValueError('Invalid library path')
    if target.suffix.lower() not in AUDIO_EXTENSIONS:
        raise ValueError('Unsupported audio file')
    return target


def apply_text_tags(path: Path, metadata: dict[str, Any]) -> None:
    audio = MutagenFile(str(path), easy=True)
    if audio is None:
        raise ValueError('Unsupported audio file')
    if audio.tags is None and hasattr(audio, 'add_tags'):
        audio.add_tags()

    def set_key(key: str, value: Any, optional: bool = False) -> None:
        if value:
            try:
                audio[key] = value if isinstance(value, list) else [str(value)]
            except Exception:
                if not optional:
                    raise

    set_key('title', metadata.get('name'))
    set_key('artist', metadata.get('artists') or metadata.get('artist'))
    set_key('album', metadata.get('album_name'))
    set_key('date', metadata.get('release_date') or metadata.get('year'))
    set_key('tracknumber', metadata.get('track_number'))
    set_key('discnumber', metadata.get('disc_number'))
    set_key(
        'musicbrainz_trackid',
        metadata.get('musicbrainz_recording_id'),
        optional=True,
    )
    set_key(
        'musicbrainz_albumid',
        metadata.get('musicbrainz_release_id'),
        optional=True,
    )
    artist_ids = [
        artist.get('id')
        for artist in metadata.get('musicbrainz_artist_ids') or []
        if isinstance(artist, dict) and artist.get('id')
    ]
    set_key('musicbrainz_artistid', artist_ids, optional=True)
    audio.save()


def repair_artist_image(root: Path, relative_file: str, artist: dict[str, str]):
    path = safe_library_path(root, relative_file)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(relative_file)
    saved = save_missing_artist_images(root.resolve(), path, [artist])
    return {
        'artist': artist.get('name', ''),
        'artist_id': artist.get('id', ''),
        'file': path.relative_to(root.resolve()).as_posix(),
        'saved': saved,
    }


def repair_file(root: Path, relative_file: str) -> dict[str, Any]:
    path = safe_library_path(root, relative_file)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(relative_file)
    current = _song_from_file(path)
    candidate = enrich_song_metadata(current)
    if not candidate.get('musicbrainz_recording_id'):
        return _scan_item(root.resolve(), path)
    apply_text_tags(path, candidate)
    try:
        save_missing_artist_images(
            root.resolve(),
            path,
            candidate.get('musicbrainz_artist_ids') or [],
        )
    except Exception:
        logger.opt(exception=True).warning(
            'Failed to save artist image for {}',
            path,
        )
    updated = _song_from_file(path)
    remaining = _changes(updated, candidate)
    if remaining:
        fields = ', '.join(change['label'] for change in remaining)
        raise ValueError(f'Metadata write did not persist for: {fields}')
    return {
        'file': path.relative_to(root.resolve()).as_posix(),
        'current': _public_song(updated),
        'candidate': _public_song(candidate),
        'matched': True,
        'changes': [],
    }
