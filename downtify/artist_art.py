"""Artist image lookup and local artist folder artwork writing."""

from __future__ import annotations

import base64
import re
import struct
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

import requests
from loguru import logger
from mutagen import File as MutagenFile

from .musicbrainz import USER_AGENT, lookup_artist_id

MUSICBRAINZ_ARTIST_URL = 'https://musicbrainz.org/ws/2/artist/{mbid}'
COVERART_ARCHIVE_ARTIST_URL = 'https://coverartarchive.org/artist/{mbid}/front'
WIKIDATA_API_URL = 'https://www.wikidata.org/w/api.php'
WIKIDATA_IMAGE_PROPERTY = 'P18'

IMAGE_NAMES = (
    'folder.jpg',
    'folder.png',
    'folder.webp',
    'artist.jpg',
    'artist.png',
    'artist.webp',
    'thumb.jpg',
    'thumb.png',
    'thumb.webp',
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
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}

_IMAGE_CACHE: dict[str, bytes | None] = {}
_WIKIDATA_CACHE: dict[str, str | None] = {}


def _norm(value: str) -> str:
    return ' '.join(value.casefold().split())


def _safe_image_stem(value: str) -> str:
    stem = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', ' ', value).strip()
    stem = re.sub(r'\s+', ' ', stem).strip(' .')
    return stem or 'artist'


def _artist_folder_name(name: str) -> str:
    return _safe_image_stem(name)


def _safe_artist_folder_path(root: Path, name: str) -> Path | None:
    if not name:
        return None
    target = (root / _artist_folder_name(name)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    return target


def _safe_artist_folder(
    root: Path,
    name: str,
    *,
    create: bool = False,
) -> Path | None:
    target = _safe_artist_folder_path(root, name)
    if target is None:
        return None
    if create:
        target.mkdir(parents=True, exist_ok=True)
    return target if target.is_dir() else None


def artist_folders_for_file(
    root: Path,
    path: Path,
    artists: list[dict[str, str]],
    *,
    include_missing: bool = False,
) -> list[Path]:
    """Return artist folders that should receive local artwork."""

    root = root.resolve()
    folders: list[Path] = []
    seen: set[Path] = set()
    for artist in artists:
        folder = _safe_artist_folder(
            root,
            artist.get('name', ''),
            create=include_missing,
        )
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


def _allows_missing_artist_folder(policy: str) -> bool:
    return policy != 'existing_only'


def _artists_for_policy(
    artists: list[dict[str, str]],
    policy: str,
) -> list[dict[str, str]]:
    if policy == 'primary_only':
        return artists[:1]
    return artists


def _target_image_stem(folder: Path, artist_name: str = '') -> str:
    return _safe_image_stem(artist_name or folder.name)


def has_named_artist_image(folder: Path, *, artist_name: str = '') -> bool:
    stem = _target_image_stem(folder, artist_name).casefold()
    return any(
        path.is_file()
        and path.suffix.casefold() in IMAGE_EXTENSIONS
        and path.stem.casefold() == stem
        for path in folder.iterdir()
    )


def has_jellyfin_sidecar_image(folder: Path) -> bool:
    """Backward-compatible alias for :func:`has_named_artist_image`."""

    return has_named_artist_image(folder)


def has_artist_image(folder: Path) -> bool:
    if has_named_artist_image(folder):
        return True
    return any(
        path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS
        for path in folder.iterdir()
    )


def artist_image_paths(folder: Path) -> list[Path]:
    paths = [
        folder / name
        for name in IMAGE_NAMES
        if (folder / name).is_file()
    ]
    paths.extend(
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS
    )
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


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
    if not url:
        return None
    response = requests.get(
        url,
        headers={'User-Agent': USER_AGENT},
        timeout=20,
        allow_redirects=True,
    )
    if response.status_code in {400, 404}:
        return None
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        return None
    content_type = response.headers.get('content-type', '')
    if content_type and not content_type.casefold().startswith('image/'):
        return None
    return response.content


def artist_image_bytes(mbid: str) -> bytes | None:
    if not mbid:
        return None
    if mbid in _IMAGE_CACHE:
        return _IMAGE_CACHE[mbid]

    data: bytes | None = None
    try:
        url = _wikimedia_artist_image_url(mbid)
        data = _download_image(url) if url else None
    except Exception:
        logger.opt(exception=True).warning(
            'Failed to fetch Wikimedia artist image for MusicBrainz artist {}',
            mbid,
        )
        data = None
    if not data:
        try:
            data = _download_image(
                COVERART_ARCHIVE_ARTIST_URL.format(mbid=mbid)
            )
        except Exception:
            logger.opt(exception=True).warning(
                'Failed to fetch Cover Art Archive image for MusicBrainz artist {}',
                mbid,
            )
            data = None
    if data:
        _IMAGE_CACHE[mbid] = data
        return data

    _IMAGE_CACHE[mbid] = None
    return None


def _picture_from_vorbis_block(value: str) -> bytes | None:
    try:
        block = base64.b64decode(value)
        offset = 0
        _pic_type = struct.unpack_from('>I', block, offset)[0]
        offset += 4
        mime_len = struct.unpack_from('>I', block, offset)[0]
        offset += 4 + mime_len
        desc_len = struct.unpack_from('>I', block, offset)[0]
        offset += 4 + desc_len
        offset += 16
        data_len = struct.unpack_from('>I', block, offset)[0]
        offset += 4
        return block[offset : offset + data_len]
    except Exception:
        return None


def embedded_cover_bytes(path: Path) -> bytes | None:
    audio = MutagenFile(str(path))
    if audio is None:
        return None

    pictures = getattr(audio, 'pictures', None)
    if pictures:
        return pictures[0].data

    tags = audio.tags or {}
    getall = getattr(tags, 'getall', None)
    if callable(getall):
        apic = getall('APIC')
        if apic:
            return apic[0].data

    covr = tags.get('covr') if hasattr(tags, 'get') else None
    if covr:
        return bytes(covr[0])

    blocks = tags.get('metadata_block_picture') if hasattr(tags, 'get') else None
    if isinstance(blocks, list):
        for block in blocks:
            data = _picture_from_vorbis_block(str(block))
            if data:
                return data
    return None


def resolve_artist_mbid(
    artist: dict[str, str],
    fallback_path: Path | None = None,
) -> str:
    artist_id = str(artist.get('id') or '').strip()
    if artist_id:
        return artist_id

    artist_name = str(artist.get('name') or '').strip()
    if not artist_name:
        return ''

    return lookup_artist_id(artist_name) or ''


def artist_or_fallback_image(
    mbid: str,
    fallback_path: Path | None = None,
) -> tuple[bytes | None, str]:
    image = artist_image_bytes(mbid)
    if image:
        return image, 'Wikimedia Commons'
    if fallback_path is not None:
        image = embedded_cover_bytes(fallback_path)
        if image:
            return image, 'Album cover fallback'
    return None, ''


def _extension_for_image(data: bytes) -> str:
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return '.webp'
    return '.jpg'


def artist_image_target_path(
    folder: Path,
    image_data: bytes,
    *,
    artist_name: str = '',
) -> Path:
    extension = _extension_for_image(image_data)
    stem = _safe_image_stem(artist_name or folder.name)
    return folder / f'{stem}{extension}'


def _legacy_folder_sidecar_paths(folder: Path) -> list[Path]:
    return [
        folder / name
        for name in IMAGE_NAMES
        if name.casefold().startswith('folder.')
        and (folder / name).is_file()
    ]


def _relative_saved_path(path: Path, root: Path | None) -> str:
    if root is None:
        return path.name
    try:
        return path.relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def ensure_named_artist_image(
    folder: Path,
    root: Path | None = None,
    *,
    artist_name: str = '',
) -> list[str]:
    """Ensure artwork uses ``{ArtistName}.{ext}`` and remove legacy ``folder.*`` files."""

    migrated: list[str] = []
    target_stem = _target_image_stem(folder, artist_name).casefold()
    named_targets = [
        path
        for path in artist_image_paths(folder)
        if path.stem.casefold() == target_stem
    ]
    if named_targets:
        for legacy in _legacy_folder_sidecar_paths(folder):
            legacy.unlink(missing_ok=True)
        return migrated

    source: Path | None = None
    for path in artist_image_paths(folder):
        source = path
        break
    if source is None:
        return migrated

    extension = source.suffix.casefold() or _extension_for_image(
        source.read_bytes()
    )
    target = folder / f'{_target_image_stem(folder, artist_name)}{extension}'
    if not target.exists():
        target.write_bytes(source.read_bytes())
        migrated.append(_relative_saved_path(target, root))

    for legacy in _legacy_folder_sidecar_paths(folder):
        if legacy.resolve() != target.resolve():
            legacy.unlink(missing_ok=True)

    generic_sidecars = {
        name.casefold()
        for name in IMAGE_NAMES
        if not name.casefold().startswith('folder.')
    }
    if (
        source.name.casefold() in generic_sidecars
        and source.resolve() != target.resolve()
    ):
        source.unlink(missing_ok=True)

    return migrated


def ensure_jellyfin_sidecar_image(
    folder: Path,
    root: Path | None = None,
    *,
    artist_name: str = '',
) -> list[str]:
    """Backward-compatible alias for :func:`ensure_named_artist_image`."""

    return ensure_named_artist_image(
        folder,
        root,
        artist_name=artist_name,
    )


def media_type_for_image(data: bytes) -> str:
    extension = _extension_for_image(data)
    if extension == '.png':
        return 'image/png'
    if extension == '.webp':
        return 'image/webp'
    return 'image/jpeg'


def save_missing_artist_images(
    root: Path,
    path: Path,
    artists: list[dict[str, str]],
    artist_folder_policy: str = 'artwork_available',
) -> list[str]:
    """Write local artist images for existing artist folders if missing."""

    saved: list[str] = []
    for artist in _artists_for_policy(artists, artist_folder_policy):
        folders = artist_folders_for_file(
            root,
            path,
            [artist],
            include_missing=False,
        )
        folders = [folder for folder in folders if not has_artist_image(folder)]
        planned_folder = _safe_artist_folder_path(root, artist.get('name', ''))
        if (
            not folders
            and planned_folder is not None
            and not planned_folder.exists()
            and _allows_missing_artist_folder(artist_folder_policy)
        ):
            folders = [planned_folder]
        if not folders:
            continue
        image, _source = artist_or_fallback_image(
            resolve_artist_mbid(artist, path),
            path,
        )
        if not image:
            continue
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
            target = artist_image_target_path(
                folder,
                image,
                artist_name=artist.get('name', ''),
            )
            if target.exists():
                continue
            target.write_bytes(image)
            saved.append(unquote(target.relative_to(root.resolve()).as_posix()))
            saved.extend(ensure_named_artist_image(folder, root.resolve()))
    return saved


def missing_artist_image_items(
    root: Path,
    path: Path,
    artists: list[dict[str, str]],
    artist_folder_policy: str = 'artwork_available',
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for artist in _artists_for_policy(artists, artist_folder_policy):
        folders = [
            folder
            for folder in artist_folders_for_file(
                root,
                path,
                [artist],
                include_missing=False,
            )
            if not has_artist_image(folder)
        ]
        planned_folder = _safe_artist_folder_path(root, artist.get('name', ''))
        if (
            not folders
            and planned_folder is not None
            and not planned_folder.exists()
            and _allows_missing_artist_folder(artist_folder_policy)
        ):
            folders = [planned_folder]
        image, source = artist_or_fallback_image(
            resolve_artist_mbid(artist, path),
            path,
        )
        if not image:
            continue
        for folder in folders:
            target = artist_image_target_path(
                folder,
                image,
                artist_name=artist.get('name', ''),
            )
            items.append({
                'artist': artist.get('name', ''),
                'artist_id': artist.get('id', ''),
                'file': path.relative_to(root.resolve()).as_posix(),
                'folder': folder.relative_to(root.resolve()).as_posix(),
                'target': target.relative_to(root.resolve()).as_posix(),
                'source': source,
            })
    return items
