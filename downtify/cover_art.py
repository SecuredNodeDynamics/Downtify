"""Serve library cover art from embedded tags or folder sidecar images."""

from __future__ import annotations

import os
from collections import OrderedDict
from io import BytesIO
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

# The cache key includes the requested thumbnail size so the original artwork
# and each downscaled variant are cached independently. A size of 0 represents
# the untouched original bytes.
_CoverCacheKey = 'tuple[str, int, int, int]'

_cover_cache: 'OrderedDict[tuple[str, int, int, int], tuple[bytes, str | None]]' = (
    OrderedDict()
)
_cover_cache_lock = Lock()
_cover_cache_bytes = 0

# Pillow is optional. When unavailable (e.g. a stripped-down build) covers are
# served at their original resolution instead of failing.
_pillow_checked = False
_pillow_available = False


def _pillow_image():
    global _pillow_checked, _pillow_available
    if not _pillow_checked:
        _pillow_checked = True
        try:
            from PIL import Image  # noqa: PLC0415

            _pillow_available = True
            return Image
        except Exception:
            _pillow_available = False
            return None
    if not _pillow_available:
        return None
    try:
        from PIL import Image  # noqa: PLC0415

        return Image
    except Exception:
        return None


def resize_image_bytes(data: bytes, size: int) -> bytes | None:
    """Downscale image bytes to fit ``size`` x ``size``, returning JPEG bytes.

    Returns ``None`` when resizing is unnecessary (already small enough) or not
    possible (Pillow missing, unsupported/corrupt image), so callers fall back
    to the original bytes.
    """

    if size <= 0 or not data:
        return None
    image_mod = _pillow_image()
    if image_mod is None:
        return None
    try:
        with image_mod.open(BytesIO(data)) as img:
            width, height = img.size
            if max(width, height) <= size:
                return None
            thumb = img.convert('RGB') if img.mode not in {'RGB', 'L'} else img
            thumb.thumbnail((size, size), image_mod.LANCZOS)
            out = BytesIO()
            thumb.save(out, format='JPEG', quality=82, optimize=True)
            return out.getvalue()
    except Exception:
        return None


def _cover_cache_key(path: Path) -> tuple[str, int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (str(path), int(stat.st_mtime_ns), int(stat.st_size))


def _cover_cache_get(
    key: tuple[str, int, int, int],
) -> tuple[bytes, str | None] | None:
    with _cover_cache_lock:
        value = _cover_cache.get(key)
        if value is not None:
            _cover_cache.move_to_end(key)
        return value


def _cover_cache_put(
    key: tuple[str, int, int, int], data: bytes, mime: str | None
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


def _resolve_original(
    full: Path, base_key: tuple[str, int, int] | None
) -> tuple[bytes | None, str | None]:
    if base_key is not None:
        cached = _cover_cache_get((*base_key, 0))
        if cached is not None:
            return cached
    data, mime = resolve_cover_bytes(full)
    if data is not None and base_key is not None:
        _cover_cache_put((*base_key, 0), data, mime)
    return data, mime


def cover_response_for_file(root: Path, file: str, size: int = 0) -> Response:
    base = root.resolve()
    try:
        full = (base / file).resolve()
        full.relative_to(base)
    except (ValueError, RuntimeError):
        raise HTTPException(status_code=400, detail='Invalid path')
    if not full.is_file():
        raise HTTPException(status_code=404, detail='File not found')

    size = max(0, int(size or 0))
    base_key = _cover_cache_key(full)
    target_key = (*base_key, size) if base_key is not None else None

    cached = _cover_cache_get(target_key) if target_key is not None else None
    if cached is not None:
        data, mime = cached
    else:
        data, mime = _resolve_original(full, base_key)
        if data is not None and size > 0:
            resized = resize_image_bytes(data, size)
            if resized is not None:
                data, mime = resized, 'image/jpeg'
        if data is not None and target_key is not None:
            _cover_cache_put(target_key, data, mime)

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
