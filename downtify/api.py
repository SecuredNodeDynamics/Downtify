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
}

AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.flac', '.ogg', '.wav', '.aac', '.opus'}


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
        char for char in normalized if unicodedata.category(char) not in {'Cc', 'Cf'}
    )
    return re.sub(r'\s+', ' ', normalized).strip().casefold()


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
        'completed': [],
        'error': '',
        'next_offset': 0,
        'complete': False,
    }
    artist_image_scan_task: Optional[asyncio.Task] = None


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
        value.replace('\\040', ' ')
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
    saved = str(state.settings.get('server_media_location') or '').strip()
    if saved:
        return saved
    configured = os.getenv('DOWNTIFY_MEDIA_SAVE_LOCATION', '').strip()
    if configured:
        return configured
    return _mount_source_for(download_dir)


def _download_directory_summary(download_dir: Path) -> dict[str, Any]:
    external_path = _external_download_path(download_dir)
    storage_dir = download_dir
    if external_path:
        external_dir = Path(external_path)
        if external_dir.exists():
            storage_dir = external_dir

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


@router.get('/api/version')
def get_version() -> str:
    return state.version


@router.get('/api/check_update')
def check_update() -> Optional[dict[str, Any]]:
    return None


@router.get('/api/health')
def get_health() -> dict[str, Any]:
    download_dir = (
        state.downloader.download_dir
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


async def _run_metadata_scan(limit: int, start: int) -> None:
    if state.downloader is None:
        state.metadata_scan = {
            **state.metadata_scan,
            'status': 'error',
            'error': 'Downloader not ready',
        }
        return

    def progress(update: dict[str, Any]) -> None:
        state.metadata_scan = {
            **state.metadata_scan,
            **update,
            'status': 'scanning',
            'limit': limit,
        }

    try:
        result = await asyncio.to_thread(
            metadata_repair.scan_library,
            state.downloader.download_dir,
            limit,
            start,
            progress,
        )
        state.metadata_scan = {
            **state.metadata_scan,
            **result,
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
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    try:
        limit = max(1, min(500, int(payload.get('limit', 100))))
    except (TypeError, ValueError):
        limit = 100
    reset = bool(payload.get('reset', False))

    task = state.metadata_scan_task
    if task is not None and not task.done():
        return _metadata_scan_status()

    previous = state.metadata_scan
    total = int(previous.get('total') or 0)
    start = 0 if reset else int(previous.get('next_offset') or 0)
    if total > 0 and start >= total:
        start = 0

    state.metadata_scan = {
        'status': 'scanning',
        'limit': limit,
        'scanned': 0,
        'batch_scanned': 0,
        'total': 0,
        'matched': 0,
        'items': [],
        'clean': [],
        'completed': previous.get('completed') or [],
        'error': '',
        'errors': [],
        'next_offset': start,
        'complete': False,
        'started_at': datetime.now(timezone.utc).isoformat(),
    }
    state.metadata_scan_task = asyncio.create_task(
        _run_metadata_scan(limit, start)
    )
    return _metadata_scan_status()


@router.get('/api/metadata/scan/status')
def metadata_scan_status() -> dict[str, Any]:
    return _metadata_scan_status()


async def _run_artist_image_scan(limit: int, start: int) -> None:
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
        state.artist_image_scan = {
            **state.artist_image_scan,
            **update,
            'status': 'scanning',
            'limit': limit,
        }

    try:
        result = await asyncio.to_thread(
            metadata_repair.scan_artist_images,
            state.downloader.download_dir,
            limit,
            start,
            progress,
        )
        state.artist_image_scan = {
            **state.artist_image_scan,
            **result,
            'items': _with_artist_image_preview(result.get('items') or []),
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
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    try:
        limit = max(1, min(200, int(payload.get('limit', 50))))
    except (TypeError, ValueError):
        limit = 50
    reset = bool(payload.get('reset', False))
    task = state.artist_image_scan_task
    if task is not None and not task.done():
        return dict(state.artist_image_scan)
    previous = state.artist_image_scan
    total = int(previous.get('total') or 0)
    start = 0 if reset else int(previous.get('next_offset') or 0)
    if total > 0 and start >= total:
        start = 0
    state.artist_image_scan = {
        'status': 'scanning',
        'limit': limit,
        'scanned': 0,
        'batch_scanned': 0,
        'total': 0,
        'matched': 0,
        'items': [],
        'completed': previous.get('completed') or [],
        'error': '',
        'next_offset': start,
        'complete': False,
        'started_at': datetime.now(timezone.utc).isoformat(),
    }
    state.artist_image_scan_task = asyncio.create_task(
        _run_artist_image_scan(limit, start)
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


def _with_artist_image_preview(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **item,
            'preview_url': item.get('preview_url') or _artist_image_preview_url(item),
        }
        for item in items
    ]


@router.get('/api/metadata/artist-images/preview')
def artist_image_preview(
    file: str = Query(...),
    artist_id: str = Query(...),
    artist: str = Query(...),
) -> Response:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    try:
        path = metadata_repair.safe_library_path(
            state.downloader.download_dir,
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
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Invalid JSON') from exc
    file = str(payload.get('file') or '').strip()
    artist = {
        'id': str(payload.get('artist_id') or '').strip(),
        'name': str(payload.get('artist') or '').strip(),
    }
    if not file or not artist['id'] or not artist['name']:
        raise HTTPException(
            status_code=400,
            detail='file, artist_id and artist are required',
        )
    try:
        result = metadata_repair.repair_artist_image(
            state.downloader.download_dir,
            file,
            artist,
        )
        completed = list(state.artist_image_scan.get('completed') or [])
        completed.append(result)
        state.artist_image_scan = {
            **state.artist_image_scan,
            'completed': completed,
        }
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail='File not found') from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception('Artist image repair failed for {}', file)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post('/api/metadata/apply')
async def apply_metadata(request: Request) -> dict[str, Any]:
    if state.downloader is None:
        raise HTTPException(status_code=500, detail='Downloader not ready')
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Invalid JSON') from exc
    file = str(payload.get('file') or '').strip()
    if not file:
        raise HTTPException(status_code=400, detail='file is required')
    try:
        result = metadata_repair.repair_file(
            state.downloader.download_dir, file
        )
        completed = list(state.metadata_scan.get('completed') or [])
        completed.append(result)
        state.metadata_scan = {
            **state.metadata_scan,
            'completed': completed,
        }
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail='File not found') from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception('Metadata repair failed for {}', file)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get('/api/album/youtube')
def youtube_album_endpoint(browse_id: str = Query(...)) -> list[dict[str, Any]]:
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
def youtube_preview_endpoint(song: dict[str, Any] = Body(...)) -> dict[str, Any]:
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
            playlist_subdir = m3u.sanitize_playlist_name(playlist_name)
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
        await asyncio.to_thread(
            m3u.write_m3u,
            state.downloader.download_dir,
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
    playlist_subdir = m3u.sanitize_playlist_name(playlist_name)
    organize = bool(state.downloader and state.downloader.organize_by_artist)
    target, kept = m3u.write_m3u(
        state.downloader.download_dir,
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
        headers = {'X-MediaBrowser-Token': jellyfin_api_key}
        
        # Try fetching CollectionFolders
        response = requests.get(
            f'{url}/Items',
            headers=headers,
            params={'Recursive': False},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            'raw_response': data,
            'items_count': len(data.get('Items', [])),
            'items': [
                {
                    'name': item.get('Name'),
                    'id': item.get('Id'),
                    'collectionType': item.get('CollectionType'),
                    'type': item.get('Type'),
                }
                for item in data.get('Items', [])
            ]
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

        # Fetch all top-level items (libraries/folders)
        headers = {'X-MediaBrowser-Token': jellyfin_api_key}
        logger.info(f'Fetching Jellyfin libraries from {url}/Items')

        response = requests.get(
            f'{url}/Items',
            headers=headers,
            params={'Recursive': False},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        logger.info(f'Jellyfin response items count: {len(data.get("Items", []))}')

        libraries = []
        seen_ids = set()  # Track IDs to avoid duplicates
        seen_names = set()  # Jellyfin can return duplicate views with different IDs

        if 'Items' in data:
            for item in data['Items']:
                # Get all folders as potential libraries
                name = str(item.get('Name') or '')
                item_id = item.get('Id')
                item_type = item.get('Type', '')
                is_folder = item.get('IsFolder', False)

                logger.info(f'Item: {name} - Type: {item_type}, IsFolder: {is_folder}')

                # Include folders that might contain music (including "Music" library)
                # Skip duplicate IDs and duplicate names because settings store names.
                name_key = _normalized_jellyfin_library_name(name)
                is_library_folder = is_folder and item_type in {'Folder', 'CollectionFolder'}
                if (
                    is_library_folder
                    and item_id not in seen_ids
                    and name_key not in seen_names
                ):
                    seen_ids.add(item_id)
                    seen_names.add(name_key)
                    libraries.append(
                        {
                            'id': item_id,
                            'name': name,
                            'type': item_type,
                        }
                    )
                elif is_library_folder:
                    logger.info(
                        f'Skipping duplicate Jellyfin library candidate: {name} '
                        f'(id: {item_id})'
                    )

        return {'success': True, 'libraries': libraries}
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504, detail='Jellyfin server timeout - server took too long to respond'
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
                status_code=401, detail='Jellyfin API key is invalid or expired'
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f'Jellyfin error: {e.response.reason}',
        )
    except Exception as e:
        logger.error(f'Error fetching Jellyfin libraries: {e}')
        raise HTTPException(
            status_code=500, detail=f'Failed to fetch Jellyfin libraries: {str(e)}'
        )


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
