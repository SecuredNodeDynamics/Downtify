"""Find duplicate audio files in the local library."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .downloader import _normalize_duplicate_key
from .library_index import list_library_files_fast

_AUDIO_SUFFIXES = {
    '.mp3',
    '.m4a',
    '.mp4',
    '.aac',
    '.flac',
    '.ogg',
    '.opus',
    '.wav',
}
_FORMAT_SCORE = {
    '.flac': 50,
    '.wav': 40,
    '.m4a': 30,
    '.mp4': 28,
    '.aac': 26,
    '.ogg': 24,
    '.opus': 24,
    '.mp3': 20,
}


def _safe_audio_path(root: Path, relative_file: str) -> Path:
    root = root.resolve()
    target = (root / str(relative_file or '')).resolve()
    if target != root and root not in target.parents:
        raise ValueError('Invalid library path')
    if not target.is_file() or target.suffix.lower() not in _AUDIO_SUFFIXES:
        raise ValueError('Unsupported audio file')
    return target


def _group_key(item: dict[str, Any]) -> tuple[str, str] | None:
    artist = _normalize_duplicate_key(str(item.get('artist') or ''))
    title = _normalize_duplicate_key(str(item.get('title') or ''))
    if not artist or not title:
        return None
    return artist, title


def _copy_payload(root: Path, item: dict[str, Any]) -> dict[str, Any] | None:
    relative = str(item.get('file') or '').strip()
    if not relative:
        return None
    try:
        path = _safe_audio_path(root, relative)
        size = path.stat().st_size
    except (OSError, ValueError):
        return None
    suffix = path.suffix.lower()
    return {
        'file': relative,
        'title': str(item.get('title') or path.stem),
        'artist': str(item.get('artist') or ''),
        'album': str(item.get('album') or ''),
        'size_bytes': size,
        'format': suffix.lstrip('.'),
        'keep': False,
    }


def _keep_score(copy: dict[str, Any]) -> tuple[int, int, int]:
    suffix = f".{copy.get('format') or ''}"
    return (
        _FORMAT_SCORE.get(suffix, 0),
        int(copy.get('size_bytes') or 0),
        -len(str(copy.get('file') or '')),
    )


def find_duplicate_groups(root: Path) -> dict[str, Any]:
    base = root.resolve()
    items = list_library_files_fast(base)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        key = _group_key(item)
        if key is None:
            continue
        copy = _copy_payload(base, item)
        if copy is None:
            continue
        grouped[key].append(copy)

    groups: list[dict[str, Any]] = []
    extra_files = 0
    for (_artist_key, _title_key), copies in grouped.items():
        if len(copies) < 2:
            continue
        keep_index = max(
            range(len(copies)),
            key=lambda index: _keep_score(copies[index]),
        )
        for index, copy in enumerate(copies):
            copy['keep'] = index == keep_index
        extra_files += len(copies) - 1
        keeper = copies[keep_index]
        groups.append(
            {
                'id': f'{keeper["artist"]}::{keeper["title"]}',
                'artist': keeper['artist'],
                'title': keeper['title'],
                'copies': copies,
            }
        )
    groups.sort(
        key=lambda group: (group['artist'].casefold(), group['title'].casefold())
    )
    return {
        'scanned': len(items),
        'groups': groups,
        'duplicate_tracks': extra_files,
    }


def _remove_empty_parents(root: Path, start: Path) -> None:
    current = start.parent
    while current != root and root in current.parents:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def delete_library_files(root: Path, relative_files: list[str]) -> dict[str, Any]:
    base = root.resolve()
    deleted: list[str] = []
    errors: list[dict[str, str]] = []
    seen: set[str] = set()
    for relative in relative_files:
        name = str(relative or '').strip()
        if not name or name in seen:
            continue
        seen.add(name)
        try:
            target = _safe_audio_path(base, name)
            sidecar = target.with_suffix('.lrc')
            target.unlink()
            if sidecar.is_file():
                sidecar.unlink(missing_ok=True)
            _remove_empty_parents(base, target)
            deleted.append(name)
        except (OSError, ValueError) as exc:
            errors.append({'file': name, 'detail': str(exc)})
    return {
        'deleted': deleted,
        'failed': errors,
        'deleted_count': len(deleted),
        'failed_count': len(errors),
    }
