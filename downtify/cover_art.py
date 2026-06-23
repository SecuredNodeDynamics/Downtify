"""Serve library cover art from embedded tags or folder sidecar images."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import Response

from .artist_art import (
    artist_image_paths,
    embedded_cover_bytes,
    media_type_for_image,
)


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

    data, mime = resolve_cover_bytes(full)
    if data is None:
        raise HTTPException(status_code=404, detail='No cover art found')
    return Response(
        content=data,
        media_type=mime or 'image/jpeg',
        headers={
            'Cache-Control': 'public, max-age=86400',
            'Access-Control-Allow-Origin': '*',
            'Cross-Origin-Resource-Policy': 'cross-origin',
            'ETag': f'"{int(full.stat().st_mtime)}"',
        },
    )
