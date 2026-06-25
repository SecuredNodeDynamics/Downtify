"""Serve library cover art from embedded tags or folder sidecar images."""

from __future__ import annotations

import os
from collections import OrderedDict
from pathlib import Path
from threading import Lock

from fastapi import HTTPException
from fastapi.responses import Response

from .artist_art import (
    artist_image_paths,
    embedded_cover_bytes,
    media_type_for_image,
)

# Parsing ID3/MP4 tags and extracting the embedded artwork on every request is
# expensive — especially on the embedded Android (Chaquopy) build, where the
# library view fires many cover requests in a row. Cache resolved cover bytes
# keyed by the file's identity (path + mtime + size) so repeated requests are
# served from memory and auto-invalidate when a file is re-tagged.
_COVER_CACHE_MAX_ENTRIES = int(
    os.getenv('DOWNTIFY_COVER_CACHE_ENTRIES', '128')
)
_COVER_CACHE_MAX_BYTES = int(
    os.getenv('DOWNTIFY_COVER_CACHE_BYTES', str(48 * 1024 * 1024))
)

_cover_cache: 'OrderedDict[tuple[str, int, int], tuple[bytes, str | None]]' = (
    OrderedDict()
)
_cover_cache_lock = Lock()
_cover_cache_bytes = 0


def _cover_cache_key(path: Path) -> tuple[str, int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (str(path), int(stat.st_mtime_ns), int(stat.st_size))


def _cover_cache_get(
    key: tuple[str, int, int],
) -> tuple[bytes, str | None] | None:
    with _cover_cache_lock:
        value = _cover_cache.get(key)
        if value is not None:
            _cover_cache.move_to_end(key)
        return value


def _cover_cache_put(
    key: tuple[str, int, int], data: bytes, mime: str | None
) -> None:
    global _cover_cache_bytes
    size = len(data)
    if size > _COVER_CACHE_MAX_BYTES:
        return
    with _cover_cache_lock:
        existing = _cover_cache.pop(key, None)
        if existing is not None:
            _cover_cache_bytes -= len(existing[0])
        _cover_cache[key] = (data, mime)
        _cover_cache_bytes += size
        while _cover_cache and (
            len(_cover_cache) > _COVER_CACHE_MAX_ENTRIES
            or _cover_cache_bytes > _COVER_CACHE_MAX_BYTES
        ):
            _, evicted = _cover_cache.popitem(last=False)
            _cover_cache_bytes -= len(evicted[0])


def clear_cover_cache() -> None:
    global _cover_cache_bytes
    with _cover_cache_lock:
        _cover_cache.clear()
        _cover_cache_bytes = 0


def _embedded_cover_bytes(path: Path) -> bytes | None:
    try:
        from mutagen.id3 import ID3

        tag = ID3(str(path))
        for frame in tag.getall('APIC'):
            if frame.data:
                return frame.data
    except Exception:
        pass
    try:
        return embedded_cover_bytes(path)
    except Exception:
        return None


def resolve_cover_bytes(path: Path) -> tuple[bytes | None, str | None]:
    """Return cover bytes from embedded tags or nearby folder images."""

    data = _embedded_cover_bytes(path)
    if data:
        return data, media_type_for_image(data)

    folder = path.parent
    for _ in range(4):
        if not folder.is_dir():
            break
        for image_path in artist_image_paths(folder):
            try:
                sidecar = image_path.read_bytes()
            except OSError:
                continue
            if sidecar:
                return sidecar, media_type_for_image(sidecar)
        if folder == folder.parent:
            break
        folder = folder.parent

    return None, None


def cover_response_for_file(root: Path, file: str) -> Response:
    base = root.resolve()
    try:
        full = (base / file).resolve()
        full.relative_to(base)
    except (ValueError, RuntimeError):
        raise HTTPException(status_code=400, detail='Invalid path')
    if not full.is_file():
        raise HTTPException(status_code=404, detail='File not found')

    cache_key = _cover_cache_key(full)
    cached = _cover_cache_get(cache_key) if cache_key is not None else None
    if cached is not None:
        data, mime = cached
    else:
        data, mime = resolve_cover_bytes(full)
        if data is not None and cache_key is not None:
            _cover_cache_put(cache_key, data, mime)

    if data is None:
        raise HTTPException(status_code=404, detail='No cover art found')
    return Response(
        content=data,
        media_type=mime or 'image/jpeg',
        headers={
            'Cache-Control': 'public, max-age=604800, immutable',
            'Access-Control-Allow-Origin': '*',
            'Cross-Origin-Resource-Policy': 'cross-origin',
            'ETag': f'"{int(full.stat().st_mtime)}"',
        },
    )
