"""FastAPI router exposed by Downtify.

The endpoints intentionally mirror the surface that the previous
``spotdl``-powered backend exposed so the existing Vue frontend keeps
working without changes:

* ``GET  /api/version``
* ``GET  /api/songs/search``
* ``GET  /api/song/url`` and ``GET /api/url`` (alias)
* ``POST /api/download/url`` (optional JSON body: resolved Spotify row so
  ``track_number`` / ``album_track_total`` survive re-fetch by URL)
* ``POST /api/playlist/m3u``
* ``GET  /api/settings``
* ``POST /api/settings/update``
* ``WS   /api/ws``
* ``GET  /api/check_update``
* ``POST /api/update``
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

import requests
import yt_dlp
from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Query,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from loguru import logger

from . import artist_art, m3u, metadata_repair, providers, spotify
from .downloader import Downloader, preview_audio_for_song
from .history import DownloadHistoryDB
from .monitor import PlaylistMonitorDB, check_playlist
from .versioning import parse_version

DEFAULT_SETTINGS: dict[str, Any] = {
    'audio_providers': ['youtube-music'],
    'lyrics_providers': ['lrclib'],
    'download_lyrics': True,
    'format': 'mp3',
    'bitrate': '320',
    'output': '{artists} - {title}.{output-ext}',
    'generate_m3u': True,
    'max_parallel_downloads': 3,
    'organize_by_artist': False,
    'organize_by_album': False,
    'enhance_metadata': True,
    'server_media_location': '',
    'jellyfin_url': '',
    'jellyfin_api_key': '',
    'jellyfin_music_library': '',
    'enable_jellyfin_tools': True,
    'artist_folder_policy': 'artwork_available',
}

AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.flac', '.ogg', '.wav', '.aac', '.opus'}
GITHUB_REPO = 'SecuredNodeDynamics/Downtify'
GITHUB_API_BASE = f'https://api.github.com/repos/{GITHUB_REPO}'
GITHUB_RELEASES_URL = f'https://github.com/{GITHUB_REPO}/releases'


def _effective_lyrics_providers(settings: dict[str, Any]) -> list[str]:
    if not settings.get('download_lyrics', True):
        return []
    return [
        p
        for p in (settings.get('lyrics_providers') or [])
        if isinstance(p, str) and p
    ]


def _normalized_jellyfin_library_name(value: Any) -> str:
    normalized = unicodedata.normalize('NFKC', str(value or ''))
    normalized = ''.join(
        char
        for char in normalized
        if unicodedata.category(char) not in {'Cc', 'Cf'}
    )
    return re.sub(r'\s+', ' ', normalized).strip().casefold()


def _jellyfin_auth_headers(api_key: str) -> dict[str, str]:
    return {
        'X-Emby-Token': api_key,
        'X-MediaBrowser-Token': api_key,
    }


def _jellyfin_base_url(value: str) -> str:
    url = value.rstrip('/')
    if url and not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    return url


def _configured_jellyfin() -> tuple[str, dict[str, str]]:
    jellyfin_url = str(state.settings.get('jellyfin_url') or '').strip()
    jellyfin_api_key = str(
        state.settings.get('jellyfin_api_key') or ''
    ).strip()
    if not jellyfin_url or not jellyfin_api_key:
        raise HTTPException(
            status_code=400,
            detail='Jellyfin URL and API key are required',
        )
    return _jellyfin_base_url(jellyfin_url), _jellyfin_auth_headers(
        jellyfin_api_key
    )


def _matching_jellyfin_library(
    url: str,
    headers: dict[str, str],
) -> dict[str, Any] | None:
    configured = _normalized_jellyfin_library_name(
        state.settings.get('jellyfin_music_library')
    )
    libraries: list[dict[str, Any]] = []

    try:
        response = requests.get(
            f'{url}/Library/VirtualFolders',
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        libraries = _libraries_from_virtual_folders(response.json())
    except Exception:
        logger.opt(exception=True).warning(
            'Could not fetch Jellyfin virtual folders for matching'
        )

    if not libraries:
        response = requests.get(
            f'{url}/Items',
            headers=headers,
            params={'Recursive': False},
            timeout=10,
        )
        response.raise_for_status()
        libraries = _libraries_from_items(response.json())

    if configured:
        for library in libraries:
            names = {
                _normalized_jellyfin_library_name(library.get('name')),
                _normalized_jellyfin_library_name(library.get('id')),
            }
            if configured in names:
                return library
    return libraries[0] if libraries else None


def _dedupe_jellyfin_libraries(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    libraries = []
    seen_names = set()
    for library in candidates:
        name_key = _normalized_jellyfin_library_name(library.get('name'))
        if not name_key or name_key in seen_names:
            if name_key:
                logger.info(
                    'Skipping duplicate Jellyfin library candidate: '
                    f'{library.get("name")} (id: {library.get("id")})'
                )
            continue
        seen_names.add(name_key)
        libraries.append(library)
    return libraries


def _prefer_music_libraries(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    music = [
        library
        for library in candidates
        if str(library.get('collection_type') or '').casefold() == 'music'
    ]
    return music or candidates


def _libraries_from_virtual_folders(data: Any) -> list[dict[str, Any]]:
    items = data if isinstance(data, list) else data.get('Items', [])
    candidates = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get('Name') or '')
        item_id = item.get('ItemId') or item.get('Id') or name
        collection_type = (
            item.get('CollectionType') or item.get('collectionType') or ''
        )
        logger.info(
            f'Virtual folder: {name} - CollectionType: {collection_type} '
            f'- ItemId: {item_id}'
        )
        candidates.append({
            'id': item_id,
            'name': name,
            'type': 'VirtualFolder',
            'collection_type': collection_type,
        })
    return _dedupe_jellyfin_libraries(_prefer_music_libraries(candidates))


def _libraries_from_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    seen_ids = set()

    for item in data.get('Items', []):
        name = str(item.get('Name') or '')
        item_id = item.get('Id')
        item_type = item.get('Type', '')
        is_folder = item.get('IsFolder', False)

        logger.info(f'Item: {name} - Type: {item_type}, IsFolder: {is_folder}')

        is_library_folder = is_folder and item_type in {
            'Folder',
            'CollectionFolder',
        }
        if is_library_folder and item_id not in seen_ids:
            seen_ids.add(item_id)
            candidates.append({
                'id': item_id,
                'name': name,
                'type': item_type,
                'collection_type': item.get('CollectionType', ''),
            })

    return _dedupe_jellyfin_libraries(_prefer_music_libraries(candidates))


class ConnectionManager:
    """Tracks the active WebSocket clients keyed by ``client_id``."""

    def __init__(self) -> None:
        self._clients: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._clients[client_id] = ws

    def disconnect(self, client_id: str) -> None:
        self._clients.pop(client_id, None)

    async def send(self, client_id: str, message: dict[str, Any]) -> None:
        ws = self._clients.get(client_id)
        if ws is None:
            return
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            self._clients.pop(client_id, None)

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead: list[str] = []
        for client_id, ws in list(self._clients.items()):
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(client_id)
        for client_id in dead:
            self._clients.pop(client_id, None)


class AppState:
    version: str = '0.0.0'
    downloader: Optional[Downloader] = None
    default_download_dir: Path = Path('/downloads')
    connections: ConnectionManager = ConnectionManager()
    settings: dict[str, Any] = dict(DEFAULT_SETTINGS)
    settings_path: Optional[Path] = None
    loop: Optional[asyncio.AbstractEventLoop] = None
    monitor_db: Optional[PlaylistMonitorDB] = None
    history_db: Optional[DownloadHistoryDB] = None
    download_jobs: dict[str, dict[str, Any]] = {}
    download_semaphore: Optional[asyncio.Semaphore] = None
    metadata_scan: dict[str, Any] = {
        'status': 'idle',
        'limit': 100,
        'scanned': 0,
        'batch_scanned': 0,
        'total': 0,
        'matched': 0,
        'items': [],
        'clean': [],
        'completed': [],
        'error': '',
        'errors': [],
        'next_offset': 0,
        'complete': False,
    }
    metadata_scan_task: Optional[asyncio.Task] = None
    artist_image_scan: dict[str, Any] = {
        'status': 'idle',
        'limit': 50,
        'scanned': 0,
        'batch_scanned': 0,
        'total': 0,
        'matched': 0,
        'items': [],
        'clean': [],
        'failed': [],
        'completed': [],
        'error': '',
        'next_offset': 0,
        'complete': False,
    }
    artist_image_scan_task: Optional[asyncio.Task] = None
    repair_log: list[dict[str, Any]] = []


state = AppState()
router = APIRouter()


def _load_settings(path: Path) -> dict[str, Any]:
    """Load saved settings from *path*, merging with DEFAULT_SETTINGS as base."""
    try:
        saved = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(saved, dict):
            merged = dict(DEFAULT_SETTINGS)
            for k, v in saved.items():
                if k in DEFAULT_SETTINGS:
                    merged[k] = v
            return merged
    except Exception:
        pass
    return dict(DEFAULT_SETTINGS)


def _save_settings(path: Path, settings: dict[str, Any]) -> None:
    try:
        path.write_text(json.dumps(settings, indent=2), encoding='utf-8')
    except Exception as exc:
        logger.warning('Could not persist settings: {}', exc)


def _server_media_location() -> str:
    return str(state.settings.get('server_media_location') or '').strip()


def _compose_host_media_location() -> str:
    return os.getenv('DOWNTIFY_MEDIA_SAVE_LOCATION', '').strip()


def _path_within_root(path: Path, root: Path) -> Optional[Path]:
    try:
        return path.relative_to(root)
    except ValueError:
        return None


def _container_media_path_for(saved: str, container_root: Path) -> Path:
    requested = Path(saved).expanduser()
    if requested.exists():
        return requested

    roots = [
        _compose_host_media_location(),
        _mount_source_for(container_root),
    ]
    for root_value in roots:
        if not root_value:
            continue
        root = Path(root_value).expanduser()
        relative = _path_within_root(requested, root)
        if relative is not None:
            return container_root / relative

    return requested


def _effective_download_dir(fallback: Path | str | None = None) -> Path:
    saved = _server_media_location()
    if saved:
        container_root = state.default_download_dir
        return _container_media_path_for(saved, container_root)
    if fallback is not None:
        return Path(fallback)
    container_root = state.default_download_dir
    return container_root


def _apply_download_dir_from_settings() -> Path:
    target = _effective_download_dir(
        state.downloader.download_dir
        if state.downloader
        else state.default_download_dir
    )
    target.mkdir(parents=True, exist_ok=True)
    if state.downloader is not None:
        state.downloader.download_dir = target
    return target


def _active_download_dir() -> Path:
    try:
        return _apply_download_dir_from_settings()
    except Exception as exc:
        logger.warning('Could not prepare download directory: {}', exc)
        raise HTTPException(
            status_code=400,
            detail=f'Could not access server media location: {exc}',
        ) from exc


def _download_playlist_subdir(playlist_name: str) -> Optional[str]:
    subdir = m3u.sanitize_playlist_name(playlist_name)
    if not subdir:
        return None
    download_root_name = _active_download_dir().name
    if subdir.casefold() == download_root_name.casefold():
        logger.info(
            'Skipping redundant playlist subfolder {!r} because the active '
            'download root is already named {!r}',
            subdir,
            download_root_name,
        )
        return None
    return subdir


def _directory_summary(
    path: Path,
    external_path: Optional[str] = None,
) -> dict[str, Any]:
    exists = path.exists()
    file_count = 0
    audio_count = 0
    total_bytes = 0
    if exists:
        try:
            for item in path.rglob('*'):
                if not item.is_file():
                    continue
                file_count += 1
                try:
                    total_bytes += item.stat().st_size
                except OSError:
                    pass
                if item.suffix.lower() in AUDIO_EXTENSIONS:
                    audio_count += 1
        except Exception:
            pass

    try:
        usage = shutil.disk_usage(path if exists else path.parent)
        disk = {
            'total_bytes': usage.total,
            'used_bytes': usage.used,
            'free_bytes': usage.free,
            'percent_used': round((usage.used / usage.total) * 100, 1)
            if usage.total
            else 0,
        }
    except Exception:
        disk = {
            'total_bytes': 0,
            'used_bytes': 0,
            'free_bytes': 0,
            'percent_used': 0,
        }

    return {
        'path': str(path),
        'external_path': external_path,
        'exists': exists,
        'file_count': file_count,
        'audio_count': audio_count,
        'size_bytes': total_bytes,
        'disk': disk,
    }


def _decode_mountinfo_path(value: str) -> str:
    return (
        value
        .replace('\\040', ' ')
        .replace('\\011', '\t')
        .replace('\\012', '\n')
        .replace('\\134', '\\')
    )


def _mount_source_for(
    path: Path,
    mountinfo_path: Path = Path('/proc/self/mountinfo'),
) -> Optional[str]:
    target = str(path.resolve())
    try:
        lines = mountinfo_path.read_text(encoding='utf-8').splitlines()
    except Exception:
        return None

    best: Optional[str] = None
    best_len = -1
    for line in lines:
        fields = line.split()
        if len(fields) < 5:
            continue
        mount_point = _decode_mountinfo_path(fields[4])
        if mount_point != target:
            continue
        root = _decode_mountinfo_path(fields[3])
        if root in {'/', target}:
            continue
        if len(mount_point) > best_len:
            best = root
            best_len = len(mount_point)
    return best


def _external_download_path(download_dir: Path) -> Optional[str]:
    saved = _server_media_location()
    if saved:
        return saved
    configured = _compose_host_media_location()
    if configured:
        return configured
    return _mount_source_for(download_dir)


def _download_directory_summary(download_dir: Path) -> dict[str, Any]:
    external_path = _external_download_path(download_dir)
    storage_dir = download_dir

    summary = _directory_summary(storage_dir, external_path=external_path)
    summary['container_path'] = str(download_dir)
    summary['storage_path'] = str(storage_dir)
    summary['storage_path_matches_display'] = (
        external_path is None or str(storage_dir) == external_path
    )
    return summary


def _command_version(command: str, args: list[str]) -> dict[str, Any]:
    path = shutil.which(command)
    if not path:
        return {'available': False, 'path': None, 'version': None}
    try:
        result = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        output = (result.stdout or result.stderr or '').splitlines()
        version = output[0].strip() if output else None
    except Exception:
        version = None
    return {'available': True, 'path': path, 'version': version}


def _clean_version(value: Any) -> Optional[str]:
    version = str(value or '').strip().lstrip('vV')
    return version if parse_version(version) is not None else None


def _is_newer_version(candidate: str, current: str) -> bool:
    candidate_parsed = parse_version(candidate)
    current_parsed = parse_version(current)
    if candidate_parsed is None or current_parsed is None:
        return False
    return candidate_parsed > current_parsed


def _github_headers() -> dict[str, str]:
    return {
        'Accept': 'application/vnd.github+json',
        'User-Agent': f'Downtify/{state.version}',
    }


def _latest_github_version(timeout: int = 8) -> dict[str, Any]:
    try:
        response = requests.get(
            f'{GITHUB_API_BASE}/releases/latest',
            headers=_github_headers(),
            timeout=timeout,
        )
        if response.status_code != 404:
            response.raise_for_status()
            payload = response.json()
            version = _clean_version(payload.get('tag_name'))
            if version:
                return {
                    'latest_version': version,
                    'release_url': payload.get('html_url')
                    or GITHUB_RELEASES_URL,
                    'source': 'release',
                    'name': payload.get('name') or payload.get('tag_name'),
                    'published_at': payload.get('published_at'),
                    'error': '',
                }
    except Exception as exc:
        logger.warning('Could not check latest GitHub release: {}', exc)

    try:
        response = requests.get(
            f'{GITHUB_API_BASE}/tags',
            headers=_github_headers(),
            timeout=timeout,
        )
        response.raise_for_status()
        tags = response.json()
        versions = [
            version
            for tag in tags
            if isinstance(tag, dict)
            and (version := _clean_version(tag.get('name')))
        ]
        if versions:
            latest = max(
                versions, key=lambda item: parse_version(item) or (0, 0, 0)
            )
            return {
                'latest_version': latest,
                'release_url': f'{GITHUB_RELEASES_URL}/tag/v{latest}',
                'source': 'tag',
                'name': f'v{latest}',
                'published_at': None,
                'error': '',
            }
    except Exception as exc:
        logger.warning('Could not check latest GitHub tag: {}', exc)
        return {
            'latest_version': None,
            'release_url': GITHUB_RELEASES_URL,
            'source': 'github',
            'name': None,
            'published_at': None,
            'error': str(exc),
        }

    return {
        'latest_version': None,
        'release_url': GITHUB_RELEASES_URL,
        'source': 'github',
        'name': None,
        'published_at': None,
        'error': 'No valid releases or tags found',
    }


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _is_docker_runtime() -> bool:
    return (
        Path('/.dockerenv').exists()
        or bool(os.getenv('DOWNTIFY_CONTAINER'))
        or os.getenv('container') in {'docker', 'podman'}
    )


def _run_update_command(
    args: list[str], cwd: Path
) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _run_docker_command(
    args: list[str], timeout: int = 120
) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _docker_self_update_container() -> str:
    return (
        os.getenv('DOWNTIFY_SELF_UPDATE_CONTAINER', '').strip()
        or os.getenv('HOSTNAME', '').strip()
        or 'downtify'
    )


def _docker_self_update_image() -> str:
    return os.getenv(
        'DOWNTIFY_SELF_UPDATE_IMAGE',
        'containrrr/watchtower:latest',
    ).strip()


def _docker_container_image(docker: str, container: str) -> str:
    configured = os.getenv('DOWNTIFY_SELF_UPDATE_TARGET_IMAGE', '').strip()
    if configured:
        return configured

    result = _run_docker_command(
        [docker, 'inspect', '--format', '{{.Config.Image}}', container],
        timeout=15,
    )
    if result.returncode != 0:
        output = (result.stdout or result.stderr or '').strip()
        raise RuntimeError(
            output or f'Could not inspect Docker container {container}'
        )
    return result.stdout.strip()


def _start_docker_self_update() -> dict[str, Any]:
    docker = shutil.which('docker')
    socket_path = Path('/var/run/docker.sock')
    container = _docker_self_update_container()
    helper_name = (
        f'downtify-self-update-{int(datetime.now(timezone.utc).timestamp())}'
    )
    image = _docker_self_update_image()
    target_image = os.getenv('DOWNTIFY_SELF_UPDATE_TARGET_IMAGE', '').strip()
    commands = [
        f'docker pull {target_image or "<current Downtify image>"}',
        'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock '
        f'{image} --run-once --cleanup --include-restarting {container}',
    ]
    if not docker or not socket_path.exists():
        return {
            'success': False,
            'updated': False,
            'mode': 'docker',
            'requires_restart': True,
            'requires_manual': True,
            'message': (
                'Docker self-update needs the host Docker socket mounted at '
                '/var/run/docker.sock and the Docker CLI available in the '
                'Downtify container.'
            ),
            'commands': commands,
        }

    try:
        target_image = _docker_container_image(docker, container)
    except RuntimeError as exc:
        return {
            'success': False,
            'updated': False,
            'mode': 'docker',
            'requires_restart': True,
            'requires_manual': True,
            'message': 'Could not inspect the running Downtify container.',
            'commands': commands,
            'pull_output': str(exc),
        }

    commands = [
        f'docker pull {target_image}',
        'docker run --rm -v /var/run/docker.sock:/var/run/docker.sock '
        f'{image} --run-once --cleanup --include-restarting {container}',
    ]

    pull = _run_docker_command([docker, 'pull', target_image], timeout=300)
    pull_output = (pull.stdout or pull.stderr or '').strip()
    if pull.returncode != 0:
        return {
            'success': False,
            'updated': False,
            'mode': 'docker',
            'requires_restart': True,
            'requires_manual': True,
            'message': 'Could not pull the latest Downtify Docker image.',
            'commands': commands,
            'pull_output': pull_output,
        }

    command = [
        docker,
        'run',
        '-d',
        '--name',
        helper_name,
        '-v',
        '/var/run/docker.sock:/var/run/docker.sock',
        image,
        '--run-once',
        '--cleanup',
        '--include-restarting',
        container,
    ]
    result = _run_docker_command(command, timeout=30)
    output = (result.stdout or result.stderr or '').strip()
    if result.returncode != 0:
        return {
            'success': False,
            'updated': False,
            'mode': 'docker',
            'requires_restart': True,
            'requires_manual': True,
            'message': 'Could not start Docker self-update helper.',
            'commands': commands,
            'pull_output': '\n'.join(
                part for part in [pull_output, output] if part
            ),
        }

    helper_message = (
        f'Docker self-update helper {output or helper_name} started for '
        f'{container}. Downtify container restart/recreate is scheduled.'
    )
    logger.warning(helper_message)
    terminal_output = '\n'.join(
        part
        for part in [
            f'$ docker pull {target_image}',
            pull_output,
            (
                '$ docker run --rm -v /var/run/docker.sock:/var/run/docker.sock '
                f'{image} --run-once --cleanup --include-restarting {container}'
            ),
            helper_message,
        ]
        if part
    )

    return {
        'success': True,
        'updated': True,
        'mode': 'docker',
        'requires_restart': False,
        'requires_manual': False,
        'restart_scheduled': True,
        'message': (
            'Latest Docker image pulled. Downtify is recreating the container '
            'and will restart shortly.'
        ),
        'helper_container': output,
        'target_image': target_image,
        'pull_output': pull_output,
        'terminal_output': terminal_output,
    }


@router.get('/api/version')
def get_version() -> str:
    return state.version


@router.get('/api/check_update')
def check_update() -> dict[str, Any]:
    latest = _latest_github_version()
    latest_version = latest.get('latest_version')
    update_available = bool(
        latest_version and _is_newer_version(latest_version, state.version)
    )
    return {
        'current_version': state.version,
        'latest_version': latest_version,
        'update_available': update_available,
        'release_url': latest.get('release_url') or GITHUB_RELEASES_URL,
        'source': latest.get('source'),
        'name': latest.get('name'),
        'published_at': latest.get('published_at'),
        'error': latest.get('error') or '',
    }


@router.post('/api/update')
def update_app() -> dict[str, Any]:
    status = check_update()
    if not status.get('update_available'):
        return {
            **status,
            'success': True,
            'updated': False,
            'mode': 'noop',
            'requires_restart': False,
            'requires_manual': False,
            'message': 'Downtify is already up to date.',
        }

    if _is_docker_runtime():
        return {**status, **_start_docker_self_update()}

    root = _project_root()
    if not (root / '.git').exists():
        return {
            **status,
            'success': False,
            'updated': False,
            'mode': 'source',
            'requires_restart': True,
            'requires_manual': True,
            'message': (
                'This installation is not a Git checkout, so Downtify cannot '
                'update it automatically.'
            ),
        }

    git = shutil.which('git')
    if not git:
        raise HTTPException(status_code=500, detail='git is not installed')

    try:
        remote = _run_update_command(
            [git, 'remote', 'get-url', 'origin'], root
        )
        fetch = _run_update_command([git, 'fetch', '--tags', 'origin'], root)
        pull = _run_update_command([git, 'pull', '--ff-only'], root)
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=504, detail='Update command timed out'
        ) from exc

    if remote.returncode != 0 or fetch.returncode != 0 or pull.returncode != 0:
        return {
            **status,
            'success': False,
            'updated': False,
            'mode': 'source',
            'requires_restart': True,
            'requires_manual': True,
            'message': 'Automatic update failed. Check the command output.',
            'remote': (remote.stdout or remote.stderr or '').strip(),
            'fetch_output': (fetch.stdout or fetch.stderr or '').strip(),
            'pull_output': (pull.stdout or pull.stderr or '').strip(),
        }

    return {
        **status,
        'success': True,
        'updated': True,
        'mode': 'source',
        'requires_restart': True,
        'requires_manual': False,
        'message': 'Update downloaded. Restart Downtify to run the new version.',
        'remote': remote.stdout.strip(),
        'fetch_output': (fetch.stdout or fetch.stderr or '').strip(),
        'pull_output': (pull.stdout or pull.stderr or '').strip(),
    }


@router.get('/api/health')
def get_health() -> dict[str, Any]:
    download_dir = (
        _active_download_dir()
        if state.downloader is not None
        else Path('/downloads')
    )
    database_dir = (
        state.settings_path.parent
        if state.settings_path is not None
        else Path('/data')
    )
    history = state.history_db.list(limit=5) if state.history_db else []
    completed_24h = (
        state.history_db.count_completed_since(
            datetime.now(timezone.utc) - timedelta(hours=24)
        )
        if state.history_db
        else 0
    )
    queue_counts: dict[str, int] = {}
    for job in state.download_jobs.values():
        status = str(job.get('status') or 'unknown')
        queue_counts[status] = queue_counts.get(status, 0) + 1
    active_queue_total = sum(
        count
        for status, count in queue_counts.items()
        if status in {'queued', 'downloading'}
    )

    failed_recent = sum(1 for item in history if item.get('status') == 'error')

    return {
        'status': 'ok' if failed_recent == 0 else 'attention',
        'version': state.version,
        'python': sys.version.split()[0],
        'tools': {
            'ffmpeg': _command_version('ffmpeg', ['-version']),
            'yt_dlp': {
                'available': True,
                'path': None,
                'version': getattr(yt_dlp.version, '__version__', None),
            },
        },
        'downloads': _download_directory_summary(download_dir),
        'data': _directory_summary(database_dir),
        'settings': {
            'format': state.settings.get('format'),
            'bitrate': state.settings.get('bitrate'),
            'max_parallel_downloads': state.settings.get(
                'max_parallel_downloads'
            ),
            'generate_m3u': state.settings.get('generate_m3u'),
            'download_lyrics': state.settings.get('download_lyrics'),
            'organize_by_artist': state.settings.get('organize_by_artist'),
            'organize_by_album': state.settings.get('organize_by_album'),
            'enhance_metadata': state.settings.get('enhance_metadata'),
        },
        'queue': {
            'total': active_queue_total,
            'all_total': len(state.download_jobs),
            'counts': queue_counts,
        },
        'history': {
            'recent': history,
            'recent_failures': failed_recent,
            'completed_24h': completed_24h,
        },
    }


@router.get('/api/songs/search')
def search_endpoint(query: str = Query('')) -> list[dict[str, Any]]:
    return providers.search_media(query, limit=80)


def _metadata_scan_status() -> dict[str, Any]:
    return dict(state.metadata_scan)


def _artist_folder_policy() -> str:
    policy = str(state.settings.get('artist_folder_policy') or '').strip()
    if policy in {'artwork_available', 'primary_only', 'existing_only'}:
        return policy
    return 'artwork_available'


def _scan_resume_start(
    previous: dict[str, Any],
    reset: bool,
    root: Path,
) -> tuple[int, bool]:
    root_key = str(root.resolve())
    previous_root = str(previous.get('root') or '')
    if reset or previous_root != root_key:
        return 0, False
    total = int(previous.get('total') or 0)
    start = int(previous.get('next_offset') or 0)
    if total > 0 and start >= total:
        return 0, False
    return start, start > 0


def _add_repair_log(
    kind: str,
    status: str,
    target: str,
    detail: str = '',
    result: dict[str, Any] | None = None,
) -> None:
    state.repair_log.insert(
        0,
        {
            'kind': kind,
            'status': status,
            'target': target,
            'detail': detail,
            'result': result or {},
            'created_at': datetime.now(timezone.utc).isoformat(),
        },
    )
    del state.repair_log[100:]


def _merge_items_by(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
    key_field: str,
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for item in [*existing, *incoming]:
        key = str(item.get(key_field) or '')
        if not key:
            continue
        if key not in merged:
            order.append(key)
        merged[key] = item
    return [merged[key] for key in order]


def _completed_metadata_files() -> set[str]:
    return {
        str(item.get('file') or '')
        for item in state.metadata_scan.get('completed') or []
        if item.get('file')
    }


def _exclude_completed_metadata_items(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    completed = _completed_metadata_files()
    if not completed:
        return items
    return [
        item for item in items if str(item.get('file') or '') not in completed
    ]


def _merge_artist_image_items(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    order: list[tuple[str, str, str]] = []
    for item in [*existing, *incoming]:
        key = _artist_image_item_key(item)
        if not any(key):
            continue
        if key not in merged:
            order.append(key)
        merged[key] = item
    return [merged[key] for key in order]


def _artist_image_item_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(item.get('artist_id') or ''),
        str(item.get('artist') or ''),
        str(item.get('folder') or ''),
    )


def _completed_artist_image_keys() -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for item in state.artist_image_scan.get('completed') or []:
        keys.update(_completed_artist_image_keys_for_result(item))
    return keys


def _completed_artist_image_keys_for_result(
    item: dict[str, Any],
) -> set[tuple[str, str, str]]:
    artist = str(item.get('artist') or '')
    artist_id = str(item.get('artist_id') or '')
    keys: set[tuple[str, str, str]] = set()
    for saved in item.get('saved') or []:
        folder = str(saved).split('/', 1)[0]
        keys.add((artist_id, artist, folder))
    for verified in item.get('verified') or []:
        folder = str(verified).split('/', 1)[0]
        keys.add((artist_id, artist, folder))
    return keys


def _exclude_completed_artist_images(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    completed = _completed_artist_image_keys()
    if not completed:
        return items
    return [
        item for item in items if _artist_image_item_key(item) not in completed
    ]


async def _run_metadata_scan(
    limit: int, start: int, scan_all: bool = False
) -> None:
    if state.downloader is None:
        state.metadata_scan = {
            **state.metadata_scan,
            'status': 'error',
            'error': 'Downloader not ready',
        }
        return

    def progress(update: dict[str, Any]) -> None:
        items = _merge_items_by(
            list(state.metadata_scan.get('items') or []),
            list(update.get('items') or []),
            'file',
        )
        items = _exclude_completed_metadata_items(items)
        clean = _merge_items_by(
            list(state.metadata_scan.get('clean') or []),
            list(update.get('clean') or []),
            'file',
        )
        state.metadata_scan = {
            **state.metadata_scan,
            **update,
            'items': items,
            'clean': clean,
            'matched': len(items),
            'status': 'scanning',
            'limit': limit,
        }

    try:
        download_dir = _active_download_dir()
        result = await asyncio.to_thread(
            metadata_repair.scan_library,
            download_dir,
            1_000_000 if scan_all else limit,
            start,
            progress,
        )
        items = _merge_items_by(
            list(state.metadata_scan.get('items') or []),
            list(result.get('items') or []),
            'file',
        )
        items = _exclude_completed_metadata_items(items)
        clean = _merge_items_by(
            list(state.metadata_scan.get('clean') or []),
            list(result.get('clean') or []),
            'file',
        )
        state.metadata_scan = {
            **state.metadata_scan,
            **result,
            'items': items,
            'clean': clean,
            'matched': len(items),
            'limit': limit,
            'status': 'done',
            'error': '',
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.exception('Metadata scan failed')
        state.metadata_scan = {
            **state.metadata_scan,
            'status': 'error',
            'error': str(exc),
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }


@router.post('/api/metadata/scan')
async def start_metadata_scan(request: Request) -> dict[str, Any]:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    download_dir = _active_download_dir()
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    try:
        limit = max(1, min(500, int(payload.get('limit', 100))))
    except (TypeError, ValueError):
        limit = 100
    reset = bool(payload.get('reset', False))
    scan_all = bool(payload.get('all', False))

    task = state.metadata_scan_task
    if task is not None and not task.done():
        return _metadata_scan_status()

    previous = state.metadata_scan
    start, continuing = _scan_resume_start(previous, reset, download_dir)
    previous_items = (
        _exclude_completed_metadata_items(previous.get('items') or [])
        if continuing
        else []
    )
    previous_clean = (previous.get('clean') or []) if continuing else []

    state.metadata_scan = {
        'status': 'scanning',
        'limit': limit,
        'scanned': 0,
        'batch_scanned': 0,
        'total': 0,
        'matched': len(previous_items),
        'items': previous_items,
        'clean': previous_clean,
        'completed': previous.get('completed') or [],
        'error': '',
        'errors': [],
        'root': str(download_dir.resolve()),
        'next_offset': start,
        'complete': False,
        'started_at': datetime.now(timezone.utc).isoformat(),
    }
    state.metadata_scan_task = asyncio.create_task(
        _run_metadata_scan(limit, start, scan_all)
    )
    return _metadata_scan_status()


@router.get('/api/metadata/scan/status')
def metadata_scan_status() -> dict[str, Any]:
    return _metadata_scan_status()


async def _run_artist_image_scan(
    limit: int,
    start: int,
    scan_all: bool = False,
) -> None:
    if state.downloader is None:
        state.artist_image_scan = {
            **state.artist_image_scan,
            'status': 'error',
            'error': 'Downloader not ready',
        }
        return

    def progress(update: dict[str, Any]) -> None:
        if 'items' in update:
            update = {
                **update,
                'items': _with_artist_image_preview(update['items']),
            }
        items = _merge_artist_image_items(
            list(state.artist_image_scan.get('items') or []),
            list(update.get('items') or []),
        )
        items = _exclude_completed_artist_images(items)
        clean = _merge_items_by(
            list(state.artist_image_scan.get('clean') or []),
            list(update.get('clean') or []),
            'file',
        )
        state.artist_image_scan = {
            **state.artist_image_scan,
            **update,
            'items': items,
            'clean': clean,
            'matched': len(items),
            'status': 'scanning',
            'limit': limit,
        }

    try:
        download_dir = _active_download_dir()
        result = await asyncio.to_thread(
            metadata_repair.scan_artist_images,
            download_dir,
            1_000_000 if scan_all else limit,
            start,
            progress,
            _artist_folder_policy(),
        )
        result_items = _with_artist_image_preview(result.get('items') or [])
        items = _merge_artist_image_items(
            list(state.artist_image_scan.get('items') or []),
            result_items,
        )
        items = _exclude_completed_artist_images(items)
        clean = _merge_items_by(
            list(state.artist_image_scan.get('clean') or []),
            list(result.get('clean') or []),
            'file',
        )
        state.artist_image_scan = {
            **state.artist_image_scan,
            **result,
            'items': items,
            'clean': clean,
            'matched': len(items),
            'limit': limit,
            'status': 'done',
            'error': '',
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.exception('Artist image scan failed')
        state.artist_image_scan = {
            **state.artist_image_scan,
            'status': 'error',
            'error': str(exc),
            'finished_at': datetime.now(timezone.utc).isoformat(),
        }


@router.post('/api/metadata/artist-images/scan')
async def scan_artist_images(request: Request) -> dict[str, Any]:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    download_dir = _active_download_dir()
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    try:
        limit = max(1, min(200, int(payload.get('limit', 50))))
    except (TypeError, ValueError):
        limit = 50
    reset = bool(payload.get('reset', False))
    scan_all = bool(payload.get('all', False))
    task = state.artist_image_scan_task
    if task is not None and not task.done():
        return dict(state.artist_image_scan)
    previous = state.artist_image_scan
    start, continuing = _scan_resume_start(previous, reset, download_dir)
    previous_items = (
        _exclude_completed_artist_images(previous.get('items') or [])
        if continuing
        else []
    )
    previous_clean = (previous.get('clean') or []) if continuing else []
    state.artist_image_scan = {
        'status': 'scanning',
        'limit': limit,
        'scanned': 0,
        'batch_scanned': 0,
        'total': 0,
        'matched': len(previous_items),
        'items': previous_items,
        'clean': previous_clean,
        'failed': previous.get('failed') or [],
        'completed': previous.get('completed') or [],
        'error': '',
        'root': str(download_dir.resolve()),
        'next_offset': start,
        'complete': False,
        'started_at': datetime.now(timezone.utc).isoformat(),
    }
    state.artist_image_scan_task = asyncio.create_task(
        _run_artist_image_scan(limit, start, scan_all)
    )
    return dict(state.artist_image_scan)


@router.get('/api/metadata/artist-images/status')
def artist_image_scan_status() -> dict[str, Any]:
    return dict(state.artist_image_scan)


def _artist_image_preview_url(item: dict[str, Any]) -> str:
    file = str(item.get('file') or '')
    artist_id = str(item.get('artist_id') or '')
    artist = str(item.get('artist') or '')
    return (
        '/api/metadata/artist-images/preview?'
        f'file={quote(file)}&artist_id={quote(artist_id)}&artist={quote(artist)}'
    )


def _artist_folder_preview_url(folder: str) -> str:
    return f'/api/metadata/artist-images/folder-preview?folder={quote(folder)}'


def _with_artist_image_preview(
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            **item,
            'preview_url': item.get('preview_url')
            or _artist_image_preview_url(item),
        }
        for item in items
    ]


@router.get('/api/metadata/artist-images/folder-preview')
def artist_folder_image_preview(folder: str = Query(...)) -> Response:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    download_dir = _active_download_dir().resolve()
    try:
        target = (download_dir / folder).resolve()
        target.relative_to(download_dir)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail='Invalid folder') from exc
    if not target.is_dir():
        raise HTTPException(status_code=404, detail='Artist folder not found')
    image_paths = artist_art.artist_image_paths(target)
    if not image_paths:
        raise HTTPException(status_code=404, detail='Artist image not found')
    image = image_paths[0]
    try:
        data = image.read_bytes()
    except OSError as exc:
        raise HTTPException(
            status_code=404, detail='Artist image not found'
        ) from exc
    return Response(
        content=data,
        media_type=artist_art.media_type_for_image(data),
        headers={'Cache-Control': 'no-store'},
    )


@router.get('/api/metadata/artist-images/preview')
def artist_image_preview(
    file: str = Query(...),
    artist_id: str = Query(...),
    artist: str = Query(...),
) -> Response:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    download_dir = _active_download_dir()
    try:
        path = metadata_repair.safe_library_path(
            download_dir,
            file,
        )
        data, _source = artist_art.artist_or_fallback_image(
            artist_id,
            path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail='File not found') from exc
    except Exception as exc:
        logger.exception('Artist image preview failed for {}', file)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not data:
        raise HTTPException(status_code=404, detail='Preview not available')
    return Response(
        content=data,
        media_type=artist_art.media_type_for_image(data),
        headers={'Cache-Control': 'no-store'},
    )


@router.post('/api/metadata/artist-images/apply')
async def apply_artist_image(request: Request) -> dict[str, Any]:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    download_dir = _active_download_dir()
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Invalid JSON') from exc
    file = str(payload.get('file') or '').strip()
    artist = {
        'id': str(payload.get('artist_id') or '').strip(),
        'name': str(payload.get('artist') or '').strip(),
    }
    folder = str(payload.get('folder') or '').strip()
    if not file or not artist['name']:
        raise HTTPException(
            status_code=400,
            detail='file and artist are required',
        )
    try:
        result = metadata_repair.repair_artist_image(
            download_dir,
            file,
            artist,
            artist_folder_policy=_artist_folder_policy(),
            target_folder=folder,
        )
        completed = list(state.artist_image_scan.get('completed') or [])
        completed.append(result)
        result_keys = _completed_artist_image_keys()
        result_keys.update(_completed_artist_image_keys_for_result(result))
        items = [
            item
            for item in state.artist_image_scan.get('items') or []
            if _artist_image_item_key(item) not in result_keys
        ]
        state.artist_image_scan = {
            **state.artist_image_scan,
            'items': items,
            'matched': len(items),
            'completed': completed,
        }
        detail = ', '.join(result.get('verified') or result.get('saved') or [])
        _add_repair_log(
            'artist_image',
            'success',
            result.get('artist') or file,
            detail,
            result=result,
        )
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail='File not found') from exc
    except ValueError as exc:
        _add_repair_log('artist_image', 'failed', artist['name'], str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception('Artist image repair failed for {}', file)
        _add_repair_log('artist_image', 'failed', artist['name'], str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post('/api/metadata/apply')
async def apply_metadata(request: Request) -> dict[str, Any]:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    download_dir = _active_download_dir()
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Invalid JSON') from exc
    file = str(payload.get('file') or '').strip()
    if not file:
        raise HTTPException(status_code=400, detail='file is required')
    try:
        result = metadata_repair.repair_file(
            download_dir,
            file,
            artist_folder_policy=_artist_folder_policy(),
        )
        completed = list(state.metadata_scan.get('completed') or [])
        completed.append(result)
        items = [
            item
            for item in state.metadata_scan.get('items') or []
            if str(item.get('file') or '') != result.get('file')
        ]
        state.metadata_scan = {
            **state.metadata_scan,
            'items': items,
            'matched': len(items),
            'completed': completed,
        }
        _add_repair_log('metadata', 'success', file, result=result)
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail='File not found') from exc
    except ValueError as exc:
        _add_repair_log('metadata', 'failed', file, str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception('Metadata repair failed for {}', file)
        _add_repair_log('metadata', 'failed', file, str(exc))
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get('/api/metadata/repair-log')
def metadata_repair_log(limit: int = Query(50)) -> list[dict[str, Any]]:
    return state.repair_log[: max(1, min(100, limit))]


@router.get('/api/album/youtube')
def youtube_album_endpoint(
    browse_id: str = Query(...),
) -> list[dict[str, Any]]:
    tracks = providers.album_tracks_from_browse_id(browse_id)
    if not tracks:
        raise HTTPException(
            status_code=404, detail='No tracks found for this album'
        )
    return tracks


@router.get('/api/song/url')
def song_url_endpoint(url: str = Query(...)):
    return _resolve_url(url)


@router.get('/api/url')
def url_endpoint(url: str = Query(...)):
    return _resolve_url(url)


@router.get('/api/preview')
def preview_endpoint(url: str = Query(...)) -> dict[str, Any]:
    parsed = spotify.parse_spotify_url(url)
    if parsed is None:
        raise HTTPException(status_code=400, detail='Invalid Spotify URL')
    kind, _sid = parsed
    resolved = _resolve_url(url)
    tracks = resolved if isinstance(resolved, list) else [resolved]
    return {'type': kind, 'tracks': tracks}


@router.post('/api/preview/youtube')
def youtube_preview_endpoint(
    song: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    video_id, match = providers.find_match(song)
    if not video_id:
        raise HTTPException(
            status_code=404,
            detail='No YouTube Music preview fallback found',
        )
    preview = providers._result_to_song(match or {'videoId': video_id}) or {
        'song_id': video_id,
        'source': 'youtube',
        'url': f'https://music.youtube.com/watch?v={video_id}',
    }
    return {
        'video_id': video_id,
        'embed_url': f'https://www.youtube.com/embed/{video_id}',
        'track': preview,
    }


@router.post('/api/preview/audio')
def audio_preview_endpoint(song: dict[str, Any] = Body(...)) -> dict[str, Any]:
    try:
        return preview_audio_for_song(song)
    except Exception as exc:
        logger.exception('Failed to resolve preview audio for {}', song)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _resolve_url(url: str):
    parsed = spotify.parse_spotify_url(url)
    if parsed is None:
        raise HTTPException(status_code=400, detail='Invalid Spotify URL')
    kind, sid = parsed
    try:
        if kind == 'track':
            return spotify.track_from_id(sid)
        if kind == 'album':
            return spotify.album_tracks_from_id(sid)
        if kind == 'playlist':
            return spotify.playlist_tracks_from_id(sid)
    except Exception as exc:
        logger.exception('Failed to resolve Spotify URL {}', url)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    raise HTTPException(
        status_code=400, detail=f'Unsupported entity type: {kind}'
    )


def _merge_client_track_hints(
    base: dict[str, Any],
    hints: Optional[dict[str, Any]],
) -> None:
    """Copy tagging fields from the client-resolved Spotify row.

    ``POST /api/download/url`` re-fetches metadata from the URL only, which loses
    ``track_number`` for rows that came from an album/playlist browse.
    """

    if not isinstance(hints, dict) or not hints:
        return
    tn = hints.get('track_number')
    if tn is not None:
        try:
            iv = int(tn)
        except (TypeError, ValueError):
            pass
        else:
            if iv > 0:
                base['track_number'] = iv
    tt = hints.get('album_track_total')
    if tt is not None:
        try:
            tv = int(tt)
        except (TypeError, ValueError):
            pass
        else:
            if tv > 0:
                base['album_track_total'] = tv
    rd = hints.get('release_date')
    if isinstance(rd, str) and rd.strip():
        base['release_date'] = rd.strip()
    yr = hints.get('year')
    if isinstance(yr, str) and yr.strip():
        base['year'] = yr.strip()


def _song_for_download(url: str) -> dict[str, Any]:
    parsed = spotify.parse_spotify_url(url)
    if parsed is not None:
        kind, sid = parsed
        if kind == 'track':
            return spotify.track_from_id(sid)
        raise HTTPException(
            status_code=400,
            detail='Only Spotify track URLs are supported here',
        )
    if 'youtube.com' in url or 'youtu.be' in url or 'music.youtube' in url:
        match = re.search(r'(?:v=|youtu\.be/)([A-Za-z0-9_-]{6,})', url)
        if not match:
            raise HTTPException(status_code=400, detail='Invalid YouTube URL')
        return providers.song_from_video_id(match.group(1))
    raise HTTPException(status_code=400, detail='Unsupported URL')


def _register_job(
    song: dict[str, Any],
    status: str = 'queued',
    history_id: Optional[int] = None,
) -> str:
    song_id = str(song.get('song_id') or song.get('url') or id(song))
    state.download_jobs[song_id] = {
        'song': song,
        'status': status,
        'progress': 0,
        'message': '',
        'filename': None,
        'history_id': history_id,
    }
    return song_id


async def _run_download(
    song: dict[str, Any],
    song_id: str,
    subdir: Optional[str] = None,
    history_id: Optional[int] = None,
    skip_duplicates: bool = True,
) -> Optional[str]:
    """Run a single download to completion, updating jobs state and broadcasting WS events."""

    if state.downloader is None:
        raise RuntimeError('Downloader not ready')
    _active_download_dir()

    loop = state.loop or asyncio.get_running_loop()
    job = state.download_jobs.get(song_id)
    if job is None:
        song_id = _register_job(song, status='downloading')
        job = state.download_jobs[song_id]
    else:
        job['status'] = 'downloading'

    if history_id is None:
        history_id = job.get('history_id')
    if history_id is not None and state.history_db is not None:
        state.history_db.mark_running(history_id)

    if skip_duplicates:
        existing = state.downloader.duplicate_filename_for(song, subdir=subdir)
        if existing:
            job['status'] = 'done'
            job['filename'] = existing
            job['progress'] = 100
            job['message'] = 'Already downloaded'
            if history_id is not None and state.history_db is not None:
                state.history_db.mark_skipped(history_id, existing)
            await state.connections.broadcast({
                'song': song,
                'progress': 100,
                'message': 'Already downloaded',
                'status': 'done',
                'filename': existing,
            })
            return existing

    await state.connections.broadcast({
        'song': song,
        'progress': 0,
        'message': '',
        'status': 'downloading',
    })

    def progress(pct: float, message: str) -> None:
        j = state.download_jobs.get(song_id)
        if j:
            j['progress'] = pct
            j['message'] = message
        asyncio.run_coroutine_threadsafe(
            state.connections.broadcast({
                'song': song,
                'progress': pct,
                'message': message,
                'status': 'downloading',
            }),
            loop,
        )

    sem = state.download_semaphore
    try:
        async with sem if sem is not None else contextlib.nullcontext():
            filename = await loop.run_in_executor(
                None,
                lambda: state.downloader.download(
                    song, progress, subdir=subdir
                ),
            )
    except Exception as exc:
        logger.exception('Download failed for {}', song_id)
        job['status'] = 'error'
        job['message'] = f'Error: {exc}'
        if history_id is not None and state.history_db is not None:
            state.history_db.mark_error(history_id, str(exc))
        await state.connections.broadcast({
            'song': song,
            'progress': 0,
            'message': f'Error: {exc}',
            'status': 'error',
        })
        raise

    job['status'] = 'done'
    job['filename'] = filename
    job['progress'] = 100
    if history_id is not None and state.history_db is not None:
        state.history_db.mark_done(history_id, filename)
    await state.connections.broadcast({
        'song': song,
        'progress': 100,
        'message': 'Done',
        'status': 'done',
        'filename': filename,
    })
    return filename


@router.post('/api/download/url')
async def download_endpoint(
    url: str = Query(...),
    client_id: str = Query(''),
    client_hints: Optional[dict[str, Any]] = Body(None),
):
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')

    song = _song_for_download(url)
    tn_before = song.get('track_number')
    yr_before = song.get('year') or song.get('release_date')
    _merge_client_track_hints(song, client_hints)
    logger.debug(
        'download/url: url={} body={} tn_before={!r} tn_after={!r} '
        'date_before={!r} date_after_year={!r} date_after_rd={!r}',
        url[:140],
        'json' if isinstance(client_hints, dict) else 'none',
        tn_before,
        song.get('track_number'),
        yr_before,
        song.get('year'),
        song.get('release_date'),
    )
    song_id = _register_job(song, status='downloading')
    history_id = (
        state.history_db.create(song, status='downloading', source_url=url)
        if state.history_db is not None
        else None
    )
    if history_id is not None:
        state.download_jobs[song_id]['history_id'] = history_id

    try:
        filename = await _run_download(song, song_id, history_id=history_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return filename


async def _process_batch(
    songs: list[dict[str, Any]],
    job_ids: list[str],
    history_ids: list[Optional[int]],
    playlist_url: str,
    generate_m3u: bool,
) -> None:
    # Resolve the playlist name up-front so all tracks land in a single,
    # per-playlist sub-folder. Loose batches (e.g. albums or unrelated
    # tracks) keep the legacy flat layout under download_dir.
    playlist_subdir: Optional[str] = None
    playlist_name: Optional[str] = None
    parsed = spotify.parse_spotify_url(playlist_url) if playlist_url else None
    if parsed is not None and parsed[0] == 'playlist':
        try:
            playlist_name, _ = await asyncio.to_thread(
                spotify.playlist_info_and_tracks, parsed[1]
            )
            playlist_subdir = _download_playlist_subdir(playlist_name)
        except Exception:
            logger.exception(
                'Failed to resolve playlist name for {}', playlist_url
            )

    async def _bounded(
        song: dict[str, Any],
        song_id: str,
        history_id: Optional[int],
    ) -> dict[str, Any]:
        try:
            filename = await _run_download(
                song,
                song_id,
                subdir=playlist_subdir,
                history_id=history_id,
            )
        except Exception:
            filename = None
        return {'song': song, 'filename': filename}

    results = await asyncio.gather(
        *[
            _bounded(s, sid, hid)
            for s, sid, hid in zip(songs, job_ids, history_ids)
        ],
        return_exceptions=False,
    )

    if not (generate_m3u and playlist_subdir and playlist_name):
        return

    entries: list[dict[str, Any]] = []
    for r in results:
        if not r or not r.get('filename'):
            continue
        s = r['song']
        entries.append({
            'filename': r['filename'],
            'title': s.get('name') or '',
            'artist': ', '.join(s.get('artists') or []),
            'duration': s.get('duration') or 0,
        })
    if not entries:
        return

    # When organize_by_artist is on, songs land in per-artist folders instead
    # of the playlist subfolder, so the M3U must go to the legacy Playlists/
    # directory (playlist_subdir=None) where relative paths still resolve.
    organize = bool(state.downloader and state.downloader.organize_by_artist)
    try:
        download_dir = _active_download_dir()
        await asyncio.to_thread(
            m3u.write_m3u,
            download_dir,
            playlist_name,
            entries,
            playlist_subdir=None if organize else playlist_subdir,
        )
    except Exception:
        logger.exception('Failed to write M3U for {}', playlist_url)


@router.post('/api/download/batch')
async def download_batch_endpoint(request: Request) -> dict[str, Any]:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Invalid JSON') from exc

    songs = payload.get('songs') or []
    if not isinstance(songs, list) or not songs:
        raise HTTPException(
            status_code=400, detail='songs must be a non-empty list'
        )
    playlist_url = str(payload.get('playlist_url') or '')
    generate_m3u = bool(payload.get('generate_m3u', True))

    valid_songs: list[dict[str, Any]] = []
    job_ids: list[str] = []
    history_ids: list[Optional[int]] = []
    for song in songs:
        if not isinstance(song, dict):
            continue
        history_id = (
            state.history_db.create(song, status='queued')
            if state.history_db is not None
            else None
        )
        song_id = _register_job(song, status='queued', history_id=history_id)
        valid_songs.append(song)
        job_ids.append(song_id)
        history_ids.append(history_id)
        await state.connections.broadcast({
            'song': song,
            'progress': 0,
            'message': '',
            'status': 'queued',
        })

    if not valid_songs:
        raise HTTPException(status_code=400, detail='No valid songs in batch')

    task = asyncio.create_task(
        _process_batch(
            valid_songs, job_ids, history_ids, playlist_url, generate_m3u
        )
    )

    def _log_batch_failure(t: asyncio.Task) -> None:
        if t.cancelled():
            return
        exc = t.exception()
        if exc is not None:
            logger.opt(exception=exc).error('Batch processing crashed')

    task.add_done_callback(_log_batch_failure)
    return {'job_ids': job_ids, 'count': len(job_ids)}


@router.get('/api/queue')
def get_queue() -> list[dict[str, Any]]:
    return list(state.download_jobs.values())


@router.delete('/api/queue')
def clear_queue() -> dict:
    state.download_jobs.clear()
    return {'cleared': True}


@router.delete('/api/queue/item')
def remove_queue_item(song_id: str = Query(...)) -> dict:
    if song_id in state.download_jobs:
        del state.download_jobs[song_id]
        return {'removed': True}
    return {'removed': False}


@router.get('/api/history')
def list_history(limit: int = Query(100)) -> list[dict[str, Any]]:
    if state.history_db is None:
        return []
    return state.history_db.list(limit=limit)


@router.delete('/api/history')
def clear_history() -> dict:
    if state.history_db is not None:
        state.history_db.clear()
    return {'cleared': True}


@router.post('/api/history/{history_id}/retry')
async def retry_history_item(history_id: int) -> dict[str, Any]:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    if state.history_db is None:
        raise HTTPException(status_code=500, detail='History not ready')

    item = state.history_db.get(history_id)
    if item is None:
        raise HTTPException(status_code=404, detail='History item not found')

    song = item.get('song')
    if not isinstance(song, dict) or not song:
        raise HTTPException(status_code=400, detail='History item has no song')

    song_id = _register_job(song, status='queued', history_id=history_id)
    await state.connections.broadcast({
        'song': song,
        'progress': 0,
        'message': 'Queued',
        'status': 'queued',
    })

    async def _retry() -> None:
        try:
            await _run_download(song, song_id, history_id=history_id)
        except Exception:
            pass

    task = asyncio.create_task(_retry())

    def _log_retry_failure(t: asyncio.Task) -> None:
        if t.cancelled():
            return
        exc = t.exception()
        if exc is not None:
            logger.opt(exception=exc).error('History retry crashed')

    task.add_done_callback(_log_retry_failure)
    return {'job_id': song_id, 'history_id': history_id}


@router.post('/api/playlist/m3u')
async def write_playlist_m3u_endpoint(request: Request) -> dict[str, Any]:
    """Write an M3U for the playlist after the per-track downloads.

    The frontend POSTs ``{playlist_url, tracks: [{filename, title,
    artist, duration}, ...]}``. The playlist name is resolved
    server-side via :func:`spotify.playlist_info_and_tracks` so the
    existing ``/api/song/url`` shape stays untouched.
    """

    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Invalid JSON') from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail='Invalid payload')

    playlist_url = str(payload.get('playlist_url') or '').strip()
    if not playlist_url:
        raise HTTPException(status_code=400, detail='Missing playlist_url')
    parsed = spotify.parse_spotify_url(playlist_url)
    if parsed is None or parsed[0] != 'playlist':
        raise HTTPException(
            status_code=400, detail='Not a Spotify playlist URL'
        )

    tracks = payload.get('tracks') or []
    if not isinstance(tracks, list):
        raise HTTPException(status_code=400, detail='tracks must be a list')

    try:
        playlist_name, _ = await asyncio.to_thread(
            spotify.playlist_info_and_tracks, parsed[1]
        )
    except Exception as exc:
        logger.exception('Failed to resolve playlist {}', playlist_url)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    entries = [t for t in tracks if isinstance(t, dict)]
    playlist_subdir = _download_playlist_subdir(playlist_name)
    organize = bool(state.downloader and state.downloader.organize_by_artist)
    download_dir = _active_download_dir()
    target, kept = m3u.write_m3u(
        download_dir,
        playlist_name,
        entries,
        playlist_subdir=None if organize else playlist_subdir,
    )
    if target is None:
        raise HTTPException(
            status_code=400, detail='No tracks resolved to a file on disk'
        )
    return {'path': str(target), 'count': kept}


@router.get('/api/settings')
def get_settings_endpoint(client_id: str = Query('')) -> dict[str, Any]:
    return state.settings


@router.post('/api/settings/update')
async def update_settings_endpoint(
    request: Request, client_id: str = Query('')
) -> dict[str, Any]:
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    if isinstance(payload, dict):
        for key, value in payload.items():
            if key in DEFAULT_SETTINGS:
                state.settings[key] = value
        if state.downloader is not None:
            fmt = payload.get('format')
            if isinstance(fmt, str) and fmt:
                state.downloader.audio_format = fmt
            bitrate = payload.get('bitrate')
            if isinstance(bitrate, str) and bitrate:
                state.downloader.audio_bitrate = bitrate
            output = payload.get('output')
            if isinstance(output, str) and output:
                state.downloader.output_template = output.replace(
                    '.{output-ext}', ''
                )
            if 'lyrics_providers' in payload or 'download_lyrics' in payload:
                state.downloader.lyrics_providers = (
                    _effective_lyrics_providers(state.settings)
                )
            if 'organize_by_artist' in payload:
                state.downloader.organize_by_artist = bool(
                    payload['organize_by_artist']
                )
            if 'organize_by_album' in payload:
                state.downloader.organize_by_album = bool(
                    payload['organize_by_album']
                )
            if 'enhance_metadata' in payload:
                state.downloader.enhance_metadata = bool(
                    payload['enhance_metadata']
                )
            if 'server_media_location' in payload:
                _apply_download_dir_from_settings()
        if 'max_parallel_downloads' in payload:
            try:
                count = max(1, int(payload['max_parallel_downloads']))
                state.download_semaphore = asyncio.Semaphore(count)
            except (TypeError, ValueError):
                pass
    if state.settings_path is not None:
        _save_settings(state.settings_path, state.settings)
    return state.settings


@router.get('/api/jellyfin/debug')
def jellyfin_debug(
    jellyfin_url: str = Query(''),
    jellyfin_api_key: str = Query(''),
) -> dict[str, Any]:
    """Debug endpoint to see raw Jellyfin response."""
    if not jellyfin_url or not jellyfin_api_key:
        raise HTTPException(
            status_code=400,
            detail='Jellyfin URL and API key are required',
        )

    try:
        url = jellyfin_url.rstrip('/')
        headers = _jellyfin_auth_headers(jellyfin_api_key)

        virtual_response = requests.get(
            f'{url}/Library/VirtualFolders',
            headers=headers,
            timeout=10,
        )
        virtual_response.raise_for_status()
        virtual_data = virtual_response.json()

        items_response = requests.get(
            f'{url}/Items',
            headers=headers,
            params={'Recursive': False},
            timeout=10,
        )
        items_response.raise_for_status()
        items_data = items_response.json()

        return {
            'virtual_folders_raw_response': virtual_data,
            'virtual_folders_count': len(virtual_data)
            if isinstance(virtual_data, list)
            else len(virtual_data.get('Items', [])),
            'virtual_folders': _libraries_from_virtual_folders(virtual_data),
            'items_raw_response': items_data,
            'items_count': len(items_data.get('Items', [])),
            'items': [
                {
                    'name': item.get('Name'),
                    'id': item.get('Id'),
                    'collectionType': item.get('CollectionType'),
                    'type': item.get('Type'),
                }
                for item in items_data.get('Items', [])
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/api/jellyfin/libraries')
def jellyfin_libraries_endpoint(
    jellyfin_url: str = Query(''),
    jellyfin_api_key: str = Query(''),
) -> dict[str, Any]:
    """Fetch available music libraries from Jellyfin server."""
    if not jellyfin_url or not jellyfin_api_key:
        raise HTTPException(
            status_code=400,
            detail='Jellyfin URL and API key are required',
        )

    try:
        # Normalize URL (remove trailing slash and handle http/https)
        url = jellyfin_url.rstrip('/')

        # Ensure we have a valid URL
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        headers = _jellyfin_auth_headers(jellyfin_api_key)
        logger.info(
            f'Fetching Jellyfin virtual folders from {url}/Library/VirtualFolders'
        )

        try:
            response = requests.get(
                f'{url}/Library/VirtualFolders',
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            libraries = _libraries_from_virtual_folders(data)
            logger.info(f'Jellyfin virtual folder count: {len(libraries)}')
            return {
                'success': True,
                'source': 'virtual_folders',
                'libraries': libraries,
            }
        except requests.exceptions.HTTPError as e:
            status_code = getattr(e.response, 'status_code', 'unknown')
            logger.warning(
                f'Jellyfin virtual folders request failed with '
                f'{status_code}; falling back to /Items'
            )

        logger.info(f'Fetching Jellyfin libraries from {url}/Items')
        response = requests.get(
            f'{url}/Items',
            headers=headers,
            params={'Recursive': False},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        logger.info(
            f'Jellyfin response items count: {len(data.get("Items", []))}'
        )

        return {
            'success': True,
            'source': 'items',
            'libraries': _libraries_from_items(data),
        }
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail='Jellyfin server timeout - server took too long to respond',
        )
    except requests.exceptions.ConnectionError as e:
        logger.error(f'Connection error to Jellyfin: {e}')
        raise HTTPException(
            status_code=503,
            detail=f'Cannot connect to Jellyfin server at {jellyfin_url}. Check that the URL is correct and the server is running.',
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail='Jellyfin API key is invalid or expired',
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f'Jellyfin error: {e.response.reason}',
        )
    except Exception as e:
        logger.error(f'Error fetching Jellyfin libraries: {e}')
        raise HTTPException(
            status_code=500,
            detail=f'Failed to fetch Jellyfin libraries: {str(e)}',
        )


def _artist_compare_key(value: Any) -> str:
    normalized = unicodedata.normalize('NFKC', str(value or ''))
    normalized = ''.join(
        char
        for char in normalized
        if unicodedata.category(char) not in {'Cc', 'Cf'}
    )
    return re.sub(r'\s+', ' ', normalized).strip().casefold()


def _named_items(
    names: dict[str, str],
    folders: dict[str, str] | None = None,
    folder_images: dict[str, bool] | None = None,
    files: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    return [
        {
            'name': name,
            'has_image': bool((folder_images or {}).get(key)),
            'missing_image': not bool((folder_images or {}).get(key)),
            **(
                {
                    'folder': folder,
                    **(
                        {'preview_url': _artist_folder_preview_url(folder)}
                        if (folder_images or {}).get(key)
                        else {}
                    ),
                }
                if (folder := (folders or {}).get(key))
                else {}
            ),
            **({'file': file} if (file := (files or {}).get(key)) else {}),
        }
        for key, name in sorted(
            names.items(),
            key=lambda item: item[1].casefold(),
        )
    ]


def _local_artist_inventory(root: Path) -> dict[str, dict[str, Any]]:
    folders: dict[str, str] = {}
    folder_images: dict[str, bool] = {}
    tag_artists: dict[str, str] = {}
    tag_files: dict[str, str] = {}

    if root.exists():
        for item in root.iterdir():
            if item.is_dir():
                key = _artist_compare_key(item.name)
                if key:
                    folders.setdefault(key, item.name)
                    folder_images[key] = bool(
                        artist_art.artist_image_paths(item)
                    )
        for path in root.rglob('*'):
            if (
                not path.is_file()
                or path.suffix.lower() not in AUDIO_EXTENSIONS
            ):
                continue
            try:
                song = metadata_repair._song_from_file(path)
            except Exception:
                logger.opt(exception=True).warning(
                    'Could not read artists from {} for reconciliation',
                    path,
                )
                continue
            for artist in song.get('artists') or []:
                key = _artist_compare_key(artist)
                if key:
                    tag_artists.setdefault(key, str(artist))
                    try:
                        tag_files.setdefault(
                            key, path.relative_to(root).as_posix()
                        )
                    except ValueError:
                        tag_files.setdefault(key, path.name)

    return {
        'folders': folders,
        'folder_images': folder_images,
        'tags': tag_artists,
        'tag_files': tag_files,
    }


def _artist_names_from_jellyfin_items(
    items: list[dict[str, Any]],
) -> dict[str, str]:
    artists: dict[str, str] = {}
    for item in items:
        names: list[Any] = []
        names.extend(item.get('Artists') or [])
        names.extend(item.get('AlbumArtists') or [])
        for artist_item in item.get('ArtistItems') or []:
            if isinstance(artist_item, dict):
                names.append(artist_item.get('Name'))
        for name in names:
            key = _artist_compare_key(name)
            if key:
                artists.setdefault(key, str(name).strip())
    return artists


def _jellyfin_artist_inventory(
    url: str,
    headers: dict[str, str],
    library: dict[str, Any] | None,
) -> dict[str, str]:
    params: dict[str, Any] = {'Recursive': True}
    if library and library.get('id'):
        params['ParentId'] = library['id']

    artists: dict[str, str] = {}
    try:
        response = requests.get(
            f'{url}/Artists',
            headers=headers,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        for item in response.json().get('Items', []):
            name = item.get('Name')
            key = _artist_compare_key(name)
            if key:
                artists.setdefault(key, str(name).strip())
    except Exception:
        logger.opt(exception=True).warning(
            'Could not fetch Jellyfin /Artists; falling back to audio items'
        )

    if artists:
        return artists

    item_params = {
        **params,
        'IncludeItemTypes': 'Audio',
        'Fields': 'Artists,AlbumArtists,ArtistItems',
    }
    response = requests.get(
        f'{url}/Items',
        headers=headers,
        params=item_params,
        timeout=30,
    )
    response.raise_for_status()
    return _artist_names_from_jellyfin_items(response.json().get('Items', []))


@router.get('/api/jellyfin/artists/reconcile')
def reconcile_jellyfin_artists() -> dict[str, Any]:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    download_dir = _active_download_dir()
    try:
        url, headers = _configured_jellyfin()
        library = _matching_jellyfin_library(url, headers)
        jellyfin_artists = _jellyfin_artist_inventory(url, headers, library)
        local = _local_artist_inventory(download_dir)
        folders = local['folders']
        folder_images = local.get('folder_images', {})
        tags = local['tags']
        tag_files = local.get('tag_files', {})

        jellyfin_keys = set(jellyfin_artists)
        folder_keys = set(folders)
        tag_keys = set(tags)
        matched_keys = jellyfin_keys & folder_keys
        missing_image_keys = {
            key for key in jellyfin_keys if not folder_images.get(key)
        }
        return {
            'success': True,
            'library': library or {},
            'counts': {
                'jellyfin': len(jellyfin_keys),
                'folders': len(folder_keys),
                'tags': len(tag_keys),
                'jellyfin_only': len(jellyfin_keys - folder_keys),
                'folder_only': len(folder_keys - jellyfin_keys),
                'tag_only': len(tag_keys - jellyfin_keys),
                'matched': len(matched_keys),
                'local_images': sum(
                    1 for key in jellyfin_keys if folder_images.get(key)
                ),
                'missing_local_images': len(missing_image_keys),
            },
            'jellyfin_only': _named_items(
                {
                    key: jellyfin_artists[key]
                    for key in jellyfin_keys - folder_keys
                },
                files=tag_files,
            ),
            'folder_only': _named_items(
                {key: folders[key] for key in folder_keys - jellyfin_keys},
                folders,
                folder_images,
                tag_files,
            ),
            'tag_only': _named_items(
                {key: tags[key] for key in tag_keys - jellyfin_keys},
                files=tag_files,
            ),
            'matched': _named_items(
                {key: folders[key] for key in matched_keys},
                folders,
                folder_images,
                tag_files,
            ),
            'missing_images': _named_items(
                {key: jellyfin_artists[key] for key in missing_image_keys},
                folders,
                folder_images,
                tag_files,
            ),
        }
    except HTTPException:
        raise
    except requests.exceptions.Timeout as exc:
        raise HTTPException(
            status_code=504, detail='Jellyfin server timeout'
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise HTTPException(
            status_code=503, detail='Cannot connect to Jellyfin'
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status_code = (
            exc.response.status_code if exc.response is not None else 502
        )
        raise HTTPException(
            status_code=status_code, detail='Jellyfin request failed'
        ) from exc
    except Exception as exc:
        logger.exception('Jellyfin artist reconciliation failed')
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post('/api/jellyfin/refresh')
def refresh_jellyfin_library() -> dict[str, Any]:
    try:
        url, headers = _configured_jellyfin()
        library = _matching_jellyfin_library(url, headers)
        if library and library.get('id'):
            response = requests.post(
                f'{url}/Items/{library["id"]}/Refresh',
                headers=headers,
                params={
                    'Recursive': True,
                    'MetadataRefreshMode': 'Default',
                    'ImageRefreshMode': 'Default',
                    'ReplaceAllMetadata': False,
                    'ReplaceAllImages': False,
                },
                timeout=20,
            )
            response.raise_for_status()
            return {
                'success': True,
                'source': 'library',
                'library': library,
            }

        response = requests.post(
            f'{url}/Library/Refresh',
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        return {'success': True, 'source': 'global', 'library': library or {}}
    except HTTPException:
        raise
    except requests.exceptions.Timeout as exc:
        raise HTTPException(
            status_code=504, detail='Jellyfin server timeout'
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise HTTPException(
            status_code=503, detail='Cannot connect to Jellyfin'
        ) from exc
    except requests.exceptions.HTTPError as exc:
        status_code = (
            exc.response.status_code if exc.response is not None else 502
        )
        raise HTTPException(
            status_code=status_code, detail='Jellyfin refresh failed'
        ) from exc
    except Exception as exc:
        logger.exception('Jellyfin library refresh failed')
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.websocket('/api/ws')
async def websocket_endpoint(
    ws: WebSocket, client_id: str = Query(...)
) -> None:
    await state.connections.connect(client_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        state.connections.disconnect(client_id)
    except Exception:
        state.connections.disconnect(client_id)


# ---------------------------------------------------------------------------
# Playlist monitoring endpoints
# ---------------------------------------------------------------------------


def _require_monitor_db() -> PlaylistMonitorDB:
    if state.monitor_db is None:
        raise HTTPException(
            status_code=500, detail='Monitor database not ready'
        )
    return state.monitor_db


@router.get('/api/monitor/playlists')
async def list_monitor_playlists() -> list[dict[str, Any]]:
    db = _require_monitor_db()
    playlists = await asyncio.to_thread(db.list_playlists)
    return [p.to_dict() for p in playlists]


@router.post('/api/monitor/playlists')
async def add_monitor_playlist(request: Request) -> dict[str, Any]:
    db = _require_monitor_db()
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    url = payload.get('url', '')
    interval_minutes = int(payload.get('interval_minutes', 60))

    parsed = spotify.parse_spotify_url(url)
    if parsed is None or parsed[0] != 'playlist':
        raise HTTPException(
            status_code=400, detail='A valid Spotify playlist URL is required'
        )

    _, spotify_id = parsed

    existing = await asyncio.to_thread(db.get_by_spotify_id, spotify_id)
    if existing is not None:
        raise HTTPException(
            status_code=409, detail='This playlist is already being monitored'
        )

    try:
        name, _tracks = await asyncio.to_thread(
            spotify.playlist_info_and_tracks, spotify_id
        )
    except Exception as exc:
        logger.exception('Failed to resolve playlist {}', spotify_id)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    playlist = await asyncio.to_thread(
        db.add_playlist, spotify_id, name, url, interval_minutes
    )

    # Kick off the first download pass immediately so the user does not have
    # to wait up to a full monitor sweep interval for the initial backfill.
    if state.downloader is not None:
        loop = state.loop or asyncio.get_running_loop()

        async def _initial_check(pl=playlist) -> None:
            try:
                await check_playlist(
                    pl,
                    db,
                    state.downloader,  # type: ignore[arg-type]
                    state.connections.broadcast,
                    loop,
                    state.settings,
                )
            except Exception:
                logger.exception('Initial check failed for playlist {}', pl.id)

        asyncio.create_task(_initial_check())

    return playlist.to_dict()


@router.patch('/api/monitor/playlists/{playlist_id}')
async def update_monitor_playlist(
    playlist_id: int, request: Request
) -> dict[str, Any]:
    db = _require_monitor_db()
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    kwargs: dict[str, Any] = {}
    if 'interval_minutes' in payload:
        kwargs['interval_minutes'] = int(payload['interval_minutes'])
    if 'enabled' in payload:
        kwargs['enabled'] = bool(payload['enabled'])

    updated = await asyncio.to_thread(
        db.update_playlist, playlist_id, **kwargs
    )
    if updated is None:
        raise HTTPException(
            status_code=404, detail='Monitored playlist not found'
        )
    return updated.to_dict()


@router.delete('/api/monitor/playlists/{playlist_id}')
async def delete_monitor_playlist(playlist_id: int) -> dict[str, Any]:
    db = _require_monitor_db()
    deleted = await asyncio.to_thread(db.delete_playlist, playlist_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail='Monitored playlist not found'
        )
    return {'deleted': True, 'id': playlist_id}


@router.post('/api/monitor/playlists/{playlist_id}/check')
async def manual_check_playlist(playlist_id: int) -> dict[str, Any]:
    db = _require_monitor_db()
    playlist = await asyncio.to_thread(db.get_playlist, playlist_id)
    if playlist is None:
        raise HTTPException(
            status_code=404, detail='Monitored playlist not found'
        )
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')

    loop = state.loop or asyncio.get_running_loop()

    async def _run() -> None:
        try:
            count = await check_playlist(
                playlist,  # type: ignore[arg-type]
                db,
                state.downloader,  # type: ignore[arg-type]
                state.connections.broadcast,
                loop,
            )
            logger.info(
                'Manual check: downloaded {} new track(s) from "{}"',
                count,
                playlist.name,
            )  # type: ignore[union-attr]
        except Exception:
            logger.exception(
                'Manual check failed for playlist {}', playlist_id
            )

    asyncio.create_task(_run())
    return {'status': 'check_started', 'id': playlist_id}
