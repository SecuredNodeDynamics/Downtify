"""Scan and repair existing library metadata."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from loguru import logger
from mutagen import File as MutagenFile

from .artist_art import (
    artist_folders_for_file,
    artist_image_paths,
    artist_image_target_path,
    artist_or_fallback_image,
    embedded_cover_bytes,
    ensure_named_artist_image,
    has_named_artist_image,
    missing_artist_image_items,
    prune_stale_artist_sidecars,
    resolve_artist_mbid,
    save_missing_artist_images,
)
from .musicbrainz import enrich_song_metadata

AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.mp4', '.aac', '.flac', '.ogg', '.opus'}

_FEATURED_ARTIST_SPLIT = re.compile(
    r'\s+(?:feat\.?|ft\.?|featuring|with)\s+',
    re.IGNORECASE,
)
_ENSEMBLE_SUFFIXES = (
    ' orchestra',
    ' ensemble',
    ' symphony',
    ' philharmonic',
    ' choir',
    ' quartet',
    ' quintet',
    ' sextet',
    ' octet',
    ' band',
    ' singers',
    ' vocalists',
)


def _strip_ensemble_suffix(name: str) -> str:
    text = str(name or '').strip()
    if not text:
        return ''
    lowered = text.casefold()
    for suffix in _ENSEMBLE_SUFFIXES:
        if lowered.endswith(suffix) and len(text) > len(suffix) + 2:
            return text[: -len(suffix)].strip()
    return ''


def expand_artist_names(names: list[str]) -> list[str]:
    """Split compound artist tags such as ``Artist A feat. Artist B``."""

    expanded: list[str] = []
    seen: set[str] = set()
    for name in names:
        text = str(name or '').strip()
        if not text:
            continue
        parts = [text]
        for separator in (' / ', ';', ','):
            if separator in text:
                parts = [
                    segment.strip()
                    for segment in text.split(separator)
                    if segment.strip()
                ]
                break
        split_parts: list[str] = []
        for part in parts:
            split_parts.extend(
                segment.strip()
                for segment in _FEATURED_ARTIST_SPLIT.split(part)
                if segment.strip()
            )
        for artist in split_parts or [text]:
            key = artist.casefold()
            if key in seen:
                continue
            seen.add(key)
            expanded.append(artist)
    return expanded


def artist_search_names(artist_name: str) -> list[str]:
    artist_name = str(artist_name or '').strip()
    if not artist_name:
        return []
    names = expand_artist_names([artist_name])
    seen = {name.casefold() for name in names}
    lowered = artist_name.casefold()
    for separator in (' & ', ' and '):
        if separator not in lowered:
            continue
        start = lowered.index(separator)
        end = start + len(separator)
        primary = artist_name[:start].strip()
        secondary = artist_name[end:].strip()
        for part in (primary, secondary):
            if part and part.casefold() not in seen:
                names.insert(0, part)
                seen.add(part.casefold())
        break
    variant = _strip_ensemble_suffix(artist_name)
    if variant and variant.casefold() not in seen:
        names.append(variant)
        seen.add(variant.casefold())
    return names


def _first(tags: Any, keys: list[str]) -> str:
    if not tags:
        return ''
    for key in keys:
        try:
            value = tags.get(key)
        except (ValueError, KeyError):
            continue
        if isinstance(value, list) and value:
            return str(value[0])
        if value:
            return str(value)
    return ''


def _genre_from_path(path: Path) -> str:
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
        pass
    try:
        from mutagen.mp4 import MP4

        audio = MP4(str(path))
        return _first(audio, ['\xa9gen'])
    except Exception:
        pass
    try:
        from mutagen.flac import FLAC

        audio = FLAC(str(path))
        if audio.tags:
            return _first(audio, ['genre'])
    except Exception:
        pass
    return ''


def _artists(tags: Any) -> list[str]:
    if tags:
        value = ''
        for key in ['artist', 'artists', '\xa9ART', 'TPE1']:
            try:
                value = tags.get(key)
            except (KeyError, ValueError):
                continue
            if isinstance(value, list) and value:
                artists = [
                    str(item).strip() for item in value if str(item).strip()
                ]
                if artists:
                    return artists
            if value:
                break
    else:
        value = ''
    if not value:
        return []
    for separator in (' / ', ';', ','):
        if separator in value:
            return [
                part.strip() for part in value.split(separator) if part.strip()
            ]
    return [str(value).strip()]


def _open_easy_audio(path: Path) -> Any:
    """Open *path* for easy (string-keyed) tag access.

    ``MutagenFile(easy=True)`` only sniffs the first bytes of a file and returns
    ``None`` for some otherwise-valid m4a/mp4 containers (notably yt-dlp output on
    the embedded Android backend, where the ``ftyp`` atom isn't where the quick
    sniff looks).     The format-specific classes parse the full atom tree, so fall
    back to one chosen by extension before giving up. Returns ``None`` only when
    the file genuinely cannot be parsed.

    ``MutagenFile`` exceptions are intentionally left to propagate so callers
    that already handle them (and rely on the raise to trigger their own
    fallbacks) keep behaving exactly as before; the extension fallback only
    kicks in for the silent ``None`` sniff result.
    """

    audio = MutagenFile(str(path), easy=True)
    if audio is not None:
        return audio

    ext = path.suffix.lower()
    try:
        if ext in {'.m4a', '.mp4', '.aac'}:
            from mutagen.easymp4 import EasyMP4

            return EasyMP4(str(path))
        if ext == '.mp3':
            from mutagen.mp3 import EasyMP3

            return EasyMP3(str(path))
        if ext == '.flac':
            from mutagen.flac import FLAC

            return FLAC(str(path))
        if ext in {'.ogg', '.oga'}:
            from mutagen.oggvorbis import OggVorbis

            return OggVorbis(str(path))
        if ext == '.opus':
            from mutagen.oggopus import OggOpus

            return OggOpus(str(path))
    except Exception:
        return None
    return None


def _song_from_file(path: Path) -> dict[str, Any]:
    audio = _open_easy_audio(path)
    if audio is None:
        stem = path.stem
        if ' - ' in stem:
            artist, title = stem.split(' - ', 1)
            return {'name': title.strip(), 'artists': [artist.strip()]}
        return {'name': stem, 'artists': []}

    tags = audio.tags or {}
    release_date = _first(tags, ['date', '\xa9day', 'TDRC'])
    artists = _artists(tags)
    artist_ids = _artists_from_ids(tags)
    song = {
        'name': _first(tags, ['title', '\xa9nam', 'TIT2']) or path.stem,
        'artists': artists,
        'album_name': _first(tags, ['album', '\xa9alb', 'TALB']),
        'genre': _first(tags, ['genre', '\xa9gen', 'TCON']),
        'release_date': release_date,
        'year': release_date[:4] if len(release_date) >= 4 else '',
        'track_number': _first(tags, ['tracknumber', 'trkn', 'TRCK']),
        'disc_number': _first(tags, ['discnumber', 'disk', 'TPOS']),
        'musicbrainz_artist_ids': [
            {
                'id': artist_id,
                'name': artists[index] if index < len(artists) else '',
            }
            for index, artist_id in enumerate(artist_ids)
        ],
    }
    length = getattr(getattr(audio, 'info', None), 'length', None)
    if length:
        song['duration_ms'] = int(float(length) * 1000)
    if not song.get('genre'):
        song['genre'] = _genre_from_path(path)
    return song


def _artists_from_ids(tags: Any) -> list[str]:
    if not tags:
        return []
    for key in [
        'musicbrainz_artistid',
        'MusicBrainz Artist Id',
        'TXXX:MusicBrainz Artist Id',
    ]:
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
        'cover_url': song.get('cover_url') or '',
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


def _album_image_scan_item(root: Path, path: Path) -> dict[str, Any]:
    current = _song_from_file(path)
    candidate = enrich_song_metadata(current)
    matched = bool(candidate.get('cover_url'))
    try:
        has_cover = bool(embedded_cover_bytes(path))
    except Exception:
        has_cover = False
    needs_cover = matched and not has_cover
    changes = []
    if needs_cover:
        changes.append({
            'field': 'cover',
            'label': 'Album cover',
            'before': 'Missing embedded cover',
            'after': 'Available cover art',
        })
    elif matched:
        changes.append({
            'field': 'cover',
            'label': 'Album cover',
            'before': 'Existing embedded cover',
            'after': 'Available replacement cover art',
        })
    return {
        'file': path.relative_to(root).as_posix(),
        'current': _public_song(current),
        'candidate': _public_song(candidate) if matched else None,
        'matched': matched,
        'has_cover': has_cover,
        'changes': changes,
    }


def _album_image_scan_files(root: Path) -> list[Path]:
    files = [
        path
        for path in root.rglob('*')
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]
    files.sort(key=lambda path: path.relative_to(root).as_posix().casefold())

    selected: list[Path] = []
    seen_albums: set[str] = set()
    for path in files:
        try:
            current = _song_from_file(path)
        except Exception:
            current = {}
        album = str(current.get('album_name') or '').strip()
        artists = ', '.join(
            str(artist).strip()
            for artist in current.get('artists') or []
            if str(artist).strip()
        )
        if album:
            key = f'{artists.casefold()}::{album.casefold()}'
        else:
            parent = path.parent.relative_to(root).as_posix().casefold()
            key = f'{parent}::{path.stem.casefold()}'
        if key in seen_albums:
            continue
        seen_albums.add(key)
        selected.append(path)
    return selected


def _expanded_artist_repair(current: dict[str, Any]) -> dict[str, Any]:
    artists = [
        str(artist).strip()
        for artist in current.get('artists') or []
        if str(artist).strip()
    ]
    proposed = expand_artist_names(artists)
    changed = bool(proposed) and proposed != artists
    return {
        'matched': changed,
        'current_artists': artists,
        'proposed_artists': proposed,
        'changes': [
            {
                'field': 'artists',
                'label': 'Artists',
                'before': ', '.join(artists),
                'after': ', '.join(proposed),
            }
        ]
        if changed
        else [],
    }


def _folder_artist_repair(
    root: Path,
    path: Path,
    artists: list[str],
) -> dict[str, Any]:
    artists = [str(artist).strip() for artist in artists if str(artist).strip()]
    if len(artists) < 2:
        return {'matched': False, 'changes': []}
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError:
        return {'matched': False, 'changes': []}
    if len(relative.parts) < 2:
        return {'matched': False, 'changes': []}
    folder_name = relative.parts[0]
    artist_keys = {artist.casefold() for artist in artists}
    folder_key = folder_name.casefold()
    if folder_key in artist_keys:
        return {'matched': False, 'changes': []}
    if not any(artist.casefold() in folder_key for artist in artists):
        return {'matched': False, 'changes': []}
    return {
        'matched': True,
        'changes': [
            {
                'field': 'artist_folder',
                'label': 'Artist folder',
                'before': folder_name,
                'after': ', '.join(artists),
            }
        ],
    }


def _artist_tag_scan_item(root: Path, path: Path) -> dict[str, Any]:
    current = _song_from_file(path)
    repair = _expanded_artist_repair(current)
    artists = repair['proposed_artists'] or repair['current_artists']
    folder_repair = _folder_artist_repair(root, path, artists)
    changes = [*repair['changes'], *folder_repair['changes']]
    return {
        'file': path.relative_to(root).as_posix(),
        'current': _public_song(current),
        'candidate': {
            **_public_song(current),
            'artists': artists,
        },
        'matched': repair['matched'] or folder_repair['matched'],
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


def _artist_image_scan_candidates(
    root: Path,
    path: Path,
    current: dict[str, Any] | None = None,
    artist_folder_policy: str = 'artwork_available',
) -> list[dict[str, Any]]:
    current = current or _song_from_file(path)
    candidate = enrich_song_metadata(current)
    artists = _combined_artist_refs(current, candidate)
    return missing_artist_image_items(
        root,
        path,
        artists,
        artist_folder_policy=artist_folder_policy,
    )


def scan_grouped_artists(
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
    errors: list[dict[str, str]] = []
    batch_scanned = 0
    for path in selected:
        batch_scanned += 1
        current_offset = start + batch_scanned
        try:
            item = _artist_tag_scan_item(root, path)
        except Exception as exc:
            errors.append({
                'file': path.relative_to(root).as_posix(),
                'error': str(exc),
            })
            item = None
        if item is not None and item['matched'] and item['changes']:
            items.append(item)
        if progress_cb is not None:
            progress_cb({
                'scanned': current_offset,
                'batch_scanned': batch_scanned,
                'total': total,
                'matched': len(items),
                'items': list(items),
                'clean': [],
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
        'clean': [],
        'errors': errors,
        'start': start,
        'next_offset': next_offset,
        'complete': next_offset >= total,
    }


def _combined_artist_refs(
    current: dict[str, Any],
    candidate: dict[str, Any],
) -> list[dict[str, str]]:
    artists: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_names: set[str] = set()

    def add(artist_id: Any, name: Any) -> None:
        artist_id = str(artist_id or '').strip()
        name = str(name or '').strip()
        if not artist_id and not name:
            return
        if artist_id and artist_id in seen_ids:
            return
        name_key = name.casefold()
        if not artist_id and name_key in seen_names:
            return
        artists.append({'id': artist_id, 'name': name})
        if artist_id:
            seen_ids.add(artist_id)
        if name_key:
            seen_names.add(name_key)

    for source in [current, candidate]:
        for artist in source.get('musicbrainz_artist_ids') or []:
            if isinstance(artist, dict):
                add(artist.get('id'), artist.get('name'))
        for name in expand_artist_names(source.get('artists') or []):
            add('', name)

    return artists


def scan_artist_images(
    root: Path,
    limit: int = 100,
    start: int = 0,
    progress_cb: ProgressCallback | None = None,
    artist_folder_policy: str = 'artwork_available',
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
    seen: set[tuple[str, str, str]] = set()
    batch_scanned = 0
    for path in selected:
        batch_scanned += 1
        current_offset = start + batch_scanned
        current: dict[str, Any] | None = None
        try:
            current = _song_from_file(path)
            candidates = _artist_image_scan_candidates(
                root,
                path,
                current,
                artist_folder_policy=artist_folder_policy,
            )
        except Exception:
            logger.opt(exception=True).warning(
                'Failed to scan artist image candidate {}',
                path,
            )
            candidates = []
        for item in candidates:
            key = (item['artist_id'], item['artist'], item['folder'])
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
        if not candidates:
            clean_items.append(_artist_image_clean_item(root, path, current))
        if progress_cb is not None:
            progress_cb({
                'scanned': current_offset,
                'batch_scanned': batch_scanned,
                'total': total,
                'items': list(items),
                'clean': list(clean_items),
                'matched': len(items),
                'start': start,
                'next_offset': current_offset,
            })
    next_offset = start + batch_scanned
    return {
        'root': str(root),
        'scanned': next_offset,
        'batch_scanned': batch_scanned,
        'total': total,
        'items': items,
        'clean': clean_items,
        'matched': len(items),
        'start': start,
        'next_offset': next_offset,
        'complete': next_offset >= total,
    }


def scan_album_images(
    root: Path,
    limit: int = 100,
    start: int = 0,
    progress_cb: ProgressCallback | None = None,
) -> dict[str, Any]:
    clean_status_limit = 200
    root = root.resolve()
    files = _album_image_scan_files(root)
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
        if progress_cb is not None:
            progress_cb({
                'scanned': current_offset,
                'batch_scanned': batch_scanned,
                'total': total,
                'matched': len(items),
                'items': list(items),
                'clean': list(clean_items[-clean_status_limit:]),
                'start': start,
                'next_offset': current_offset,
            })
        try:
            item = _album_image_scan_item(root, path)
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
        is_last_selected = batch_scanned == len(selected)
        if progress_cb is not None and is_last_selected:
            progress_cb({
                'scanned': current_offset,
                'batch_scanned': batch_scanned,
                'total': total,
                'matched': len(items),
                'items': list(items),
                'clean': list(clean_items[-clean_status_limit:]),
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
        'clean': clean_items[-clean_status_limit:],
        'errors': errors,
        'start': start,
        'next_offset': next_offset,
        'complete': next_offset >= total,
    }


def _artist_image_clean_item(
    root: Path,
    path: Path,
    current: dict[str, Any] | None,
) -> dict[str, Any]:
    artists = []
    if current is not None:
        artists = [
            str(artist).strip()
            for artist in current.get('artists') or []
            if str(artist).strip()
        ]
    try:
        file = path.relative_to(root.resolve()).as_posix()
    except ValueError:
        file = path.name
    return {
        'file': file,
        'artist': ', '.join(artists),
        'folder': file.split('/', 1)[0] if '/' in file else '',
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
    audio = _open_easy_audio(path)
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
    set_key('genre', metadata.get('genre'), optional=True)
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


def apply_artist_tags(path: Path, artists: list[str]) -> None:
    audio = _open_easy_audio(path)
    if audio is None:
        raise ValueError('Unsupported audio file')
    if audio.tags is None and hasattr(audio, 'add_tags'):
        audio.add_tags()
    values = [str(artist).strip() for artist in artists if str(artist).strip()]
    if not values:
        raise ValueError('No artist names to write')
    audio['artist'] = values
    audio.save()


def _artist_folder_verify_result(
    root: Path,
    path: Path,
    current_artists: list[str],
    proposed_artists: list[str],
) -> dict[str, Any]:
    root = root.resolve()
    current_compounds = [
        artist
        for artist in current_artists
        if expand_artist_names([artist]) != [artist]
    ]
    old_folders: list[Path] = []
    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        relative = Path(path.name)
    if relative.parts and current_compounds:
        first_folder = (root / relative.parts[0]).resolve()
        first_key = first_folder.name.casefold()
        if first_folder.is_dir() and any(
            artist.casefold() == first_key for artist in current_compounds
        ):
            old_folders.append(first_folder)
    elif relative.parts and _folder_artist_repair(
        root,
        path,
        proposed_artists,
    )['matched']:
        first_folder = (root / relative.parts[0]).resolve()
        if first_folder.is_dir():
            old_folders.append(first_folder)

    artist_refs = [{'id': '', 'name': artist} for artist in proposed_artists]
    folders = artist_folders_for_file(
        root,
        path,
        artist_refs,
        include_missing=True,
    )
    created_folders = [
        folder.relative_to(root).as_posix()
        for folder in folders
        if folder.exists()
    ]

    final_path = path
    if old_folders and folders:
        old_folder = old_folders[0]
        primary_folder = folders[0]
        try:
            suffix_parts = path.resolve().relative_to(old_folder).parts
        except ValueError:
            suffix_parts = (path.name,)
        target = primary_folder.joinpath(*suffix_parts).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ValueError('Invalid repaired artist folder path') from exc
        if target != path.resolve():
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise ValueError(
                    f'Repaired file already exists: '
                    f'{target.relative_to(root).as_posix()}'
                )
            path.rename(target)
            final_path = target

    removed_folders: list[str] = []
    remaining_folders: list[str] = []
    for folder in old_folders:
        if not folder.exists():
            removed_folders.append(folder.relative_to(root).as_posix())
            continue
        for child in sorted(
            (item for item in folder.rglob('*') if item.is_dir()),
            key=lambda item: len(item.parts),
            reverse=True,
        ):
            try:
                child.rmdir()
            except OSError:
                pass
        try:
            folder.rmdir()
            removed_folders.append(folder.relative_to(root).as_posix())
        except OSError:
            remaining_folders.append(folder.relative_to(root).as_posix())

    missing_created = [
        artist
        for artist, folder in zip(proposed_artists, folders)
        if not folder.exists()
    ]
    if missing_created:
        raise ValueError(
            'Artist folder creation did not persist for: '
            + ', '.join(missing_created)
        )
    if old_folders and not removed_folders and not remaining_folders:
        raise ValueError('Old grouped artist folder verification failed')

    return {
        'file': final_path.relative_to(root).as_posix(),
        'created_folders': created_folders,
        'removed_folders': removed_folders,
        'old_folders_remaining': remaining_folders,
        'folder_verified': bool(created_folders),
    }


ArtistImageFetcher = Callable[[str, dict[str, str]], tuple[bytes | None, str]]


def repair_artist_image(
    root: Path,
    relative_file: str,
    artist: dict[str, str],
    artist_folder_policy: str = 'artwork_available',
    target_folder: str = '',
    image_fetchers: list[ArtistImageFetcher] | None = None,
):
    root = root.resolve()
    artist_name = str(artist.get('name') or '').strip()
    if not artist_name:
        raise ValueError('Artist name is required')

    folder = _safe_artist_image_folder(root, target_folder)
    if folder is None and artist_name and not relative_file:
        folder = _safe_artist_image_folder(root, artist_name)

    path: Path | None = None
    relative_file = str(relative_file or '').strip()
    if relative_file:
        path = safe_library_path(root, relative_file)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(relative_file)

    if folder is not None:
        saved = _save_artist_image_to_folder(
            root,
            path,
            artist,
            folder,
            image_fetchers=image_fetchers,
        )
    elif path is not None:
        saved = save_missing_artist_images(
            root,
            path,
            [artist],
            artist_folder_policy=artist_folder_policy,
        )
    else:
        raise ValueError('A library file or artist folder is required')

    verified = _verified_artist_image_paths(root, path, artist, folder)
    if not verified and saved:
        verified = sorted(
            {
                relative
                for relative in saved
                if (root / relative).is_file()
            }
        )
    if not verified:
        raise ValueError(
            'No artist image source found (MusicBrainz, album art, Jellyfin, '
            'Spotify, Apple Music, or Discogs)'
        )
    return _finalize_artist_image_repair_result(
        root,
        artist,
        folder,
        {
            'artist': artist_name,
            'artist_id': artist.get('id', ''),
            'file': path.relative_to(root).as_posix() if path is not None else '',
            'saved': saved,
            'verified': verified,
        },
    )


def repair_artist_image_bytes(
    root: Path,
    relative_file: str,
    artist: dict[str, str],
    image: bytes,
    target_folder: str = '',
):
    root = root.resolve()
    artist_name = str(artist.get('name') or '').strip()
    if not artist_name:
        raise ValueError('Artist name is required')
    if not image:
        raise ValueError('Image data is required')

    folder = _safe_artist_image_folder(root, target_folder)
    if folder is None and artist_name and not relative_file:
        folder = _safe_artist_image_folder(root, artist_name)
    if folder is None:
        raise ValueError('A library file or artist folder is required')

    path: Path | None = None
    relative_file = str(relative_file or '').strip()
    if relative_file:
        path = safe_library_path(root, relative_file)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(relative_file)

    folder.mkdir(parents=True, exist_ok=True)
    target = artist_image_target_path(
        folder,
        image,
        artist_name=artist_name,
    )
    target.write_bytes(image)
    prune_stale_artist_sidecars(
        folder,
        artist_name=artist_name,
        keep=target,
    )
    saved = sorted(
        {
            target.relative_to(root).as_posix(),
            *ensure_named_artist_image(
                folder,
                root,
                artist_name=artist_name,
            ),
        }
    )
    verified = _verified_artist_image_paths(root, path, artist, folder)
    if not verified and saved:
        verified = sorted(
            {
                relative
                for relative in saved
                if (root / relative).is_file()
            }
        )
    if not verified:
        raise ValueError('Artist image was not written')
    return _finalize_artist_image_repair_result(
        root,
        artist,
        folder,
        {
            'artist': artist_name,
            'artist_id': artist.get('id', ''),
            'file': path.relative_to(root).as_posix() if path is not None else '',
            'saved': saved,
            'verified': verified,
        },
    )


def _safe_artist_image_folder(root: Path, folder: str) -> Path | None:
    folder = str(folder or '').strip()
    if not folder:
        return None
    target = (root / folder).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError('Invalid artist folder') from exc
    return target


def _existing_folder_image_paths(
    root: Path,
    folder: Path,
    *,
    artist_name: str = '',
) -> list[str]:
    if not folder.is_dir():
        return []
    if not has_named_artist_image(folder, artist_name=artist_name):
        return []
    saved = ensure_named_artist_image(
        folder,
        root,
        artist_name=artist_name,
    )
    paths: list[str] = []
    for image_path in artist_image_paths(folder):
        try:
            paths.append(image_path.resolve().relative_to(root.resolve()).as_posix())
        except ValueError:
            continue
    return sorted(set(paths + saved))


def fetch_artist_image_bytes(
    path: Path | None,
    artist: dict[str, str],
    *,
    image_fetchers: list[ArtistImageFetcher] | None = None,
) -> tuple[bytes | None, str]:
    fallback_path = path
    for artist_name in artist_search_names(str(artist.get('name') or '').strip()):
        probe = dict(artist)
        probe['name'] = artist_name
        image: bytes | None = None
        if fallback_path is not None:
            try:
                image = embedded_cover_bytes(fallback_path)
            except Exception:
                image = None
            if image:
                return image, 'Album art'
        if image_fetchers:
            for fetch in image_fetchers:
                image, source = fetch(artist_name, probe)
                if image:
                    return image, source
        mbid = resolve_artist_mbid(probe, fallback_path)
        image, source = artist_or_fallback_image(mbid, fallback_path)
        if image:
            return image, source or ''
    return None, ''


def _save_artist_image_to_folder(
    root: Path,
    path: Path | None,
    artist: dict[str, str],
    folder: Path,
    *,
    image_fetchers: list[ArtistImageFetcher] | None = None,
) -> list[str]:
    artist_name = str(artist.get('name') or '').strip()
    existing = _existing_folder_image_paths(
        root,
        folder,
        artist_name=artist_name,
    )
    if existing:
        return existing

    image, _source = fetch_artist_image_bytes(
        path,
        artist,
        image_fetchers=image_fetchers,
    )
    if not image:
        return []
    folder.mkdir(parents=True, exist_ok=True)
    target = artist_image_target_path(
        folder,
        image,
        artist_name=artist_name,
    )
    if not target.exists():
        target.write_bytes(image)
    saved = [target.relative_to(root).as_posix()]
    saved.extend(
        ensure_named_artist_image(
            folder,
            root,
            artist_name=artist_name,
        )
    )
    return sorted(set(saved))


def _verified_artist_image_paths(
    root: Path,
    path: Path | None,
    artist: dict[str, str],
    target_folder: Path | None = None,
) -> list[str]:
    verified: list[str] = []
    if target_folder is not None:
        folders = [target_folder] if target_folder.is_dir() else []
    elif path is not None:
        folders = artist_folders_for_file(
            root,
            path,
            [artist],
            include_missing=False,
        )
    else:
        folders = []
    for folder in folders:
        for image_path in artist_image_paths(folder):
            try:
                relative = image_path.resolve().relative_to(root)
            except ValueError:
                continue
            verified.append(relative.as_posix())
    return sorted(set(verified))


def verify_artist_folder_image(
    root: Path,
    artist: dict[str, str],
    folder: Path | None,
    *,
    saved: list[str] | None = None,
    verified: list[str] | None = None,
) -> dict[str, Any]:
    """Confirm artist artwork exists on disk in the expected artist folder."""

    artist_name = str(artist.get('name') or '').strip()
    root = root.resolve()
    candidate_paths = sorted(set((saved or []) + (verified or [])))

    on_disk: list[str] = []
    for relative in candidate_paths:
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            continue
        if path.is_file() and path.stat().st_size > 0:
            on_disk.append(relative)

    target_folder = folder
    if target_folder is None and on_disk:
        target_folder = (root / on_disk[0].split('/', 1)[0]).resolve()

    folder_ready = False
    folder_relative = ''
    if target_folder is not None and target_folder.is_dir():
        try:
            folder_relative = target_folder.relative_to(root).as_posix()
        except ValueError:
            folder_relative = target_folder.name
        folder_ready = has_named_artist_image(
            target_folder,
            artist_name=artist_name,
        )

    return {
        'verified_on_disk': bool(on_disk) and folder_ready,
        'verified': on_disk,
        'folder': folder_relative,
    }


def _finalize_artist_image_repair_result(
    root: Path,
    artist: dict[str, str],
    folder: Path | None,
    result: dict[str, Any],
) -> dict[str, Any]:
    check = verify_artist_folder_image(
        root,
        artist,
        folder,
        saved=result.get('saved') or [],
        verified=result.get('verified') or [],
    )
    if not check['verified_on_disk']:
        raise ValueError('Artist image was not written to the artist folder')
    result['verified_on_disk'] = True
    result['verified'] = check['verified']
    if check['folder']:
        result['folder'] = check['folder']
    return result


def repair_file(
    root: Path,
    relative_file: str,
    candidate: dict[str, Any] | None = None,
    artist_folder_policy: str = 'artwork_available',
) -> dict[str, Any]:
    path = safe_library_path(root, relative_file)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(relative_file)
    current = _song_from_file(path)
    candidate = candidate if isinstance(candidate, dict) else None
    if candidate is None:
        candidate = enrich_song_metadata(current)
    if not candidate.get('musicbrainz_recording_id'):
        return _scan_item(root.resolve(), path)
    apply_text_tags(path, candidate)
    try:
        save_missing_artist_images(
            root.resolve(),
            path,
            candidate.get('musicbrainz_artist_ids') or [],
            artist_folder_policy=artist_folder_policy,
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


def repair_album_image(
    root: Path,
    relative_file: str,
    candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = safe_library_path(root, relative_file)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(relative_file)
    current = _song_from_file(path)
    candidate = candidate if isinstance(candidate, dict) else None
    if candidate is None:
        candidate = enrich_song_metadata(current)
    if not candidate.get('cover_url'):
        raise ValueError('No album cover source found')

    # Reuse the downloader tag writer so every supported audio container gets
    # cover art written with the same mutagen rules as fresh downloads.
    from .downloader import embed_metadata

    merged = {**current, **candidate}
    embed_metadata(path, merged)
    updated = _album_image_scan_item(root.resolve(), path)
    if not updated.get('has_cover'):
        raise ValueError('Album cover write did not persist')
    return {
        **updated,
        'matched': True,
        'changes': [],
    }


def repair_grouped_artists(
    root: Path,
    relative_file: str,
    artists: list[str] | None = None,
) -> dict[str, Any]:
    path = safe_library_path(root, relative_file)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(relative_file)
    current = _song_from_file(path)
    proposed = [
        str(artist).strip()
        for artist in artists or []
        if str(artist).strip()
    ]
    if not proposed:
        proposed = _expanded_artist_repair(current)['proposed_artists']
    if not proposed:
        proposed = [
            str(artist).strip()
            for artist in current.get('artists') or []
            if str(artist).strip()
        ]
    if not proposed:
        return _artist_tag_scan_item(root.resolve(), path)

    if proposed != [
        str(artist).strip()
        for artist in current.get('artists') or []
        if str(artist).strip()
    ]:
        apply_artist_tags(path, proposed)
    updated = _song_from_file(path)
    remaining = _expanded_artist_repair(updated)
    if remaining['matched']:
        raise ValueError('Artist tag write did not persist')
    current_artists = [
        str(artist).strip()
        for artist in current.get('artists') or []
        if str(artist).strip()
    ]
    updated_artists = [
        str(artist).strip()
        for artist in updated.get('artists') or []
        if str(artist).strip()
    ]
    if updated_artists != proposed:
        raise ValueError('Artist tag write did not persist')
    folder_result = _artist_folder_verify_result(
        root.resolve(),
        path,
        current_artists,
        proposed,
    )
    final_path = safe_library_path(root, folder_result['file'])
    updated = _song_from_file(final_path)
    return {
        'file': folder_result['file'],
        'current': _public_song(updated),
        'candidate': {
            **_public_song(updated),
            'artists': proposed,
        },
        'matched': True,
        'changes': [],
        'folder_verification': folder_result,
    }
