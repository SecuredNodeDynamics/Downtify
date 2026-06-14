"""Artist image lookup and Jellyfin-friendly sidecar writing."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

import requests
from loguru import logger

from .musicbrainz import USER_AGENT

FANART_API_URL = 'https://webservice.fanart.tv/v3/music/{mbid}'
MUSICBRAINZ_ARTIST_URL = 'https://musicbrainz.org/ws/2/artist/{mbid}'
WIKIDATA_API_URL = 'https://www.wikidata.org/w/api.php'
WIKIDATA_IMAGE_PROPERTY = 'P18'

IMAGE_NAMES = (
    'folder.jpg',
    'folder.png',
    'folder.webp',
    'poster.jpg',
    'poster.png',
    'poster.webp',
    'cover.jpg',
    'cover.png',
    'cover.webp',
    'default.jpg',
    'default.png',
    'default.webp',
)

_IMAGE_CACHE: dict[str, bytes | None] = {}
_WIKIDATA_CACHE: dict[str, str | None] = {}


def _norm(value: str) -> str:
    return ' '.join(value.casefold().split())


def _safe_artist_folder(root: Path, name: str) -> Path | None:
    if not name:
        return None
    target = (root / name).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    return target if target.is_dir() else None


def artist_folders_for_file(
    root: Path,
    path: Path,
    artists: list[dict[str, str]],
) -> list[Path]:
    """Return existing artist folders that should receive local artwork."""

    root = root.resolve()
    folders: list[Path] = []
    seen: set[Path] = set()
    for artist in artists:
        folder = _safe_artist_folder(root, artist.get('name', ''))
        if folder and folder not in seen:
            folders.append(folder)
            seen.add(folder)

    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        return folders
    if len(relative.parts) < 2:
        return folders

    first_folder = (root / relative.parts[0]).resolve()
    if first_folder.is_dir() and first_folder not in seen:
        folder_name = _norm(first_folder.name)
        for artist in artists:
            if _norm(artist.get('name', '')) == folder_name:
                folders.append(first_folder)
                seen.add(first_folder)
                break
    return folders


def has_artist_image(folder: Path) -> bool:
    return any((folder / name).exists() for name in IMAGE_NAMES)


def _best_fanart_url(payload: dict[str, Any]) -> str:
    for key in ('artistthumb', 'artistbackground', 'hdmusiclogo'):
        images = payload.get(key)
        if not isinstance(images, list):
            continue
        ranked = sorted(
            (
                image
                for image in images
                if isinstance(image, dict) and image.get('url')
            ),
            key=lambda image: int(str(image.get('likes') or '0')),
            reverse=True,
        )
        if ranked:
            return str(ranked[0]['url'])
    return ''


def _fanart_artist_image_url(mbid: str) -> str:
    api_key = os.environ.get('DOWNTIFY_FANART_API_KEY', '').strip()
    if not api_key:
        return ''
    response = requests.get(
        FANART_API_URL.format(mbid=mbid),
        params={'api_key': api_key},
        timeout=12,
    )
    if response.status_code == 404:
        return ''
    response.raise_for_status()
    return _best_fanart_url(response.json())


def _wikidata_id_from_url(url: str) -> str:
    parsed = urlparse(url)
    if 'wikidata.org' not in parsed.netloc:
        return ''
    match = re.search(r'/wiki/(Q\d+)$', parsed.path)
    return match.group(1) if match else ''


def _wikidata_id_for_artist(mbid: str) -> str:
    if mbid in _WIKIDATA_CACHE:
        return _WIKIDATA_CACHE[mbid] or ''
    response = requests.get(
        MUSICBRAINZ_ARTIST_URL.format(mbid=mbid),
        params={'inc': 'url-rels', 'fmt': 'json'},
        headers={'User-Agent': USER_AGENT},
        timeout=12,
    )
    if response.status_code == 404:
        _WIKIDATA_CACHE[mbid] = None
        return ''
    response.raise_for_status()
    for relation in response.json().get('relations') or []:
        if not isinstance(relation, dict):
            continue
        target = relation.get('url')
        if not isinstance(target, dict):
            continue
        wikidata_id = _wikidata_id_from_url(str(target.get('resource') or ''))
        if wikidata_id:
            _WIKIDATA_CACHE[mbid] = wikidata_id
            return wikidata_id
    _WIKIDATA_CACHE[mbid] = None
    return ''


def _wikimedia_artist_image_url(mbid: str) -> str:
    wikidata_id = _wikidata_id_for_artist(mbid)
    if not wikidata_id:
        return ''
    response = requests.get(
        WIKIDATA_API_URL,
        params={
            'action': 'wbgetentities',
            'ids': wikidata_id,
            'props': 'claims',
            'format': 'json',
        },
        headers={'User-Agent': USER_AGENT},
        timeout=12,
    )
    response.raise_for_status()
    entity = response.json().get('entities', {}).get(wikidata_id, {})
    claims = entity.get('claims', {})
    images = claims.get(WIKIDATA_IMAGE_PROPERTY) or []
    for image in images:
        mainsnak = image.get('mainsnak') if isinstance(image, dict) else None
        datavalue = mainsnak.get('datavalue') if isinstance(mainsnak, dict) else None
        filename = datavalue.get('value') if isinstance(datavalue, dict) else ''
        if filename:
            return (
                'https://commons.wikimedia.org/wiki/Special:FilePath/'
                f'{quote(str(filename))}'
            )
    return ''


def _download_image(url: str) -> bytes | None:
    response = requests.get(
        url,
        headers={'User-Agent': USER_AGENT},
        timeout=20,
        allow_redirects=True,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    content_type = response.headers.get('content-type', '')
    if content_type and not content_type.casefold().startswith('image/'):
        return None
    return response.content


def artist_image_bytes(mbid: str) -> bytes | None:
    if not mbid:
        return None
    if mbid in _IMAGE_CACHE:
        return _IMAGE_CACHE[mbid]

    for source in (_fanart_artist_image_url, _wikimedia_artist_image_url):
        try:
            url = source(mbid)
            if not url:
                continue
            data = _download_image(url)
        except Exception:
            logger.opt(exception=True).warning(
                'Failed to fetch artist image for MusicBrainz artist {}',
                mbid,
            )
            continue
        if data:
            _IMAGE_CACHE[mbid] = data
            return data

    _IMAGE_CACHE[mbid] = None
    return None


def _extension_for_image(data: bytes) -> str:
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return '.webp'
    return '.jpg'


def save_missing_artist_images(
    root: Path,
    path: Path,
    artists: list[dict[str, str]],
) -> list[str]:
    """Write local artist images for existing artist folders if missing."""

    saved: list[str] = []
    for artist in artists:
        folders = artist_folders_for_file(root, path, [artist])
        folders = [folder for folder in folders if not has_artist_image(folder)]
        if not folders:
            continue
        image = artist_image_bytes(artist.get('id', ''))
        if not image:
            continue
        extension = _extension_for_image(image)
        for folder in folders:
            target = folder / f'folder{extension}'
            if target.exists():
                continue
            target.write_bytes(image)
            saved.append(unquote(target.relative_to(root.resolve()).as_posix()))
    return saved
