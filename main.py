"""Downtify entry point.

Boots the FastAPI app that powers the web UI. The previous incarnation
relied on the Spotify Web API (via ``spotdl`` + ``spotipy``); since that
path now requires a Spotify Premium account, this version resolves
metadata directly from the public ``open.spotify.com/embed`` endpoints
and pulls the audio from YouTube via ``yt-dlp``.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import mimetypes
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from load_dotenv import load_dotenv
from loguru import logger
from uvicorn import Config, Server

from downtify import __version__, api, cover_art, library_index
from downtify.downloader import Downloader
from downtify.history import DownloadHistoryDB
from downtify.monitor import PlaylistMonitorDB, monitor_loop
from downtify.versioning import read_runtime_version, runtime_version_path

load_dotenv()


class _InterceptHandler(logging.Handler):
    """Redirect all stdlib logging records into loguru."""

    @staticmethod
    def emit(record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _setup_logging(level: str) -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | '
            '<level>{level: <8}</level> | '
            '<cyan>{name}</cyan> - '
            '<level>{message}</level>'
        ),
        level=level.upper(),
        colorize=None,
    )
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    # Explicitly override uvicorn's loggers before it starts — uvicorn will
    # still write to these logger names, and we want them flowing through
    # loguru rather than being printed raw by uvicorn's default handler.
    for _name in ('uvicorn', 'uvicorn.error', 'uvicorn.access', 'fastapi'):
        _log = logging.getLogger(_name)
        _log.handlers = [_InterceptHandler()]
        _log.propagate = False


DOWNLOAD_DIR = Path(os.getenv('DOWNLOAD_DIR', '/downloads'))
DATABASE_DIR = Path(os.getenv('DATABASE_DIR', '/data'))
WEB_GUI_LOCATION = os.getenv('WEB_GUI_LOCATION', 'frontend/dist')
DEFAULT_HOST = os.getenv('HOST', '0.0.0.0')
DEFAULT_PORT = int(os.getenv('DOWNTIFY_PORT', os.getenv('PORT', '8000')))
VERSION_FILE = runtime_version_path(DATABASE_DIR / 'app-version')


class SPAStaticFiles(StaticFiles):
    """Serve ``index.html`` for unknown paths so SPA routing works."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            return await super().get_response('index.html', scope)


def _is_api_document_navigation(request: Request) -> bool:
    path = request.url.path
    if not (path == '/list' or path.startswith('/api/')):
        return False
    if request.method.upper() != 'GET':
        return False

    fetch_dest = request.headers.get('sec-fetch-dest', '').lower()
    if fetch_dest == 'document':
        return True

    accept = request.headers.get('accept', '').lower()
    requested_with = request.headers.get('x-requested-with', '').lower()
    return 'text/html' in accept and requested_with != 'xmlhttprequest'


def _fix_mime_types() -> None:
    mimetypes.add_type('application/javascript', '.js')
    mimetypes.add_type('application/javascript', '.mjs')
    mimetypes.add_type('text/css', '.css')


def build_app() -> FastAPI:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    runtime_version = read_runtime_version(__version__, VERSION_FILE)

    app = FastAPI(
        title='Downtify',
        description=(
            'Download your Spotify playlists and songs along with album '
            'art and metadata in a self-hosted way via Docker.'
        ),
        version=runtime_version,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    @app.middleware('http')
    async def _redirect_api_document_navigations(request, call_next):
        if _is_api_document_navigation(request):
            return RedirectResponse('/', status_code=303)
        return await call_next(request)

    settings_path = DATABASE_DIR / 'settings.json'
    api.state.settings_path = settings_path
    api.state.settings = api._load_settings(settings_path)
    api.state.default_download_dir = DOWNLOAD_DIR
    api.state.history_db = DownloadHistoryDB(
        DATABASE_DIR / 'download_history.db'
    )

    api.state.version = runtime_version
    active_download_dir = api._effective_download_dir(DOWNLOAD_DIR)
    active_download_dir.mkdir(parents=True, exist_ok=True)
    api.state.downloader = Downloader(
        active_download_dir,
        audio_format=api.state.settings['format'],
        audio_bitrate=api.state.settings.get('bitrate', '320'),
        output_template=api.state.settings['output'].replace(
            '.{output-ext}', ''
        ),
        lyrics_providers=api._effective_lyrics_providers(api.state.settings),
        organize_by_artist=bool(
            api.state.settings.get('organize_by_artist', False)
        ),
        organize_by_album=bool(
            api.state.settings.get('organize_by_album', False)
        ),
        enhance_metadata=bool(
            api.state.settings.get('enhance_metadata', True)
        ),
        download_artist_images=bool(
            api.state.settings.get('download_artist_images', True)
        ),
        artist_folder_policy=str(
            api.state.settings.get('artist_folder_policy')
            or 'artwork_available'
        ),
        discogs_token=str(api.state.settings.get('discogs_token') or ''),
    )
    app.include_router(api.router)

    def _on_library_changed() -> None:
        api.invalidate_library_files_cache()
        api.invalidate_local_artist_inventory_cache()
        api.schedule_library_files_cache_refresh()
        api.schedule_library_genre_refresh()

    library_index.register_library_changed_callback(_on_library_changed)

    @app.on_event('startup')
    async def _startup() -> None:
        loop = asyncio.get_running_loop()
        api.state.loop = loop
        api.state.download_semaphore = asyncio.Semaphore(
            max(1, int(api.state.settings.get('max_parallel_downloads', 3)))
        )
        db_path = DATABASE_DIR / 'downtify_monitor.db'
        api.state.monitor_db = PlaylistMonitorDB(db_path)
        asyncio.create_task(
            monitor_loop(
                db=api.state.monitor_db,
                get_downloader=lambda: api.state.downloader,
                broadcast=api.state.connections.broadcast,
                loop=loop,
                settings=api.state.settings,
                get_history_db=lambda: api.state.history_db,
                history_changed=api._broadcast_history_changed,
            )
        )
        asyncio.create_task(api.reconcile_history_on_startup())
        asyncio.create_task(api.backfill_monitor_images_on_startup())
        asyncio.create_task(api.start_genre_warmup())
        asyncio.create_task(api.warm_library_files_cache())

    @app.get('/list')
    def list_downloads() -> list[str]:
        audio_exts = {'.mp3', '.m4a', '.flac', '.ogg', '.wav', '.aac', '.opus'}
        base = api._active_download_dir().resolve()
        if not base.exists():
            return []
        files: list[str] = []
        # Walk recursively so per-playlist sub-folders show up alongside
        # loose downloads in the library view.
        for path in base.rglob('*'):
            if not path.is_file():
                continue
            if path.suffix.lower() not in audio_exts:
                continue
            files.append(path.relative_to(base).as_posix())
        files.sort()
        return files

    @app.delete('/delete')
    def delete_download(file: str) -> dict:
        # Resolve and confine to the active download directory.
        base = api._active_download_dir().resolve()
        try:
            full = (base / file).resolve()
            full.relative_to(base)
        except (ValueError, RuntimeError):
            return {'deleted': False, 'error': 'Invalid path'}
        if not full.is_file():
            return {'deleted': False, 'error': 'File not found'}
        try:
            full.unlink()
        except Exception as exc:
            return {'deleted': False, 'error': str(exc)}
        library_index.notify_library_changed()
        return {'deleted': True}

    def _cover_response(file: str, size: int = 0):
        return cover_art.cover_response_for_file(
            api._active_download_dir(), file, size
        )

    @app.get('/cover')
    def get_cover(file: str, size: int = 0):
        return _cover_response(file, size)

    @app.get('/cover/{file_path:path}')
    def get_cover_path(file_path: str, size: int = 0):
        return _cover_response(file_path, size)

    @app.get('/downloads/{file_path:path}')
    def get_download(file_path: str):
        base = api._active_download_dir().resolve()
        try:
            full = (base / file_path).resolve()
            full.relative_to(base)
        except (ValueError, RuntimeError):
            raise HTTPException(status_code=400, detail='Invalid path')
        if not full.is_file():
            raise HTTPException(status_code=404, detail='File not found')
        return FileResponse(full)

    # The embedded mobile build serves the UI from the app's own bundled
    # assets and only needs the API, so the SPA mount is skipped when the
    # web assets are unavailable (or explicitly disabled).
    serve_spa = os.getenv('DOWNTIFY_SERVE_SPA', '1').strip().lower() not in {
        '0',
        'false',
        'no',
    }
    if serve_spa and Path(WEB_GUI_LOCATION).is_dir():
        app.mount(
            '/',
            SPAStaticFiles(directory=WEB_GUI_LOCATION, html=True),
            name='static',
        )
    return app


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='downtify')
    # The legacy entrypoint passed ``web`` as the subcommand plus a few
    # spotdl-only flags. We accept and ignore the unsupported ones so
    # existing Docker images keep starting cleanly.
    parser.add_argument('mode', nargs='?', default='web')
    parser.add_argument('--host', default=DEFAULT_HOST)
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--log-level', default='info')
    parser.add_argument('--keep-alive', action='store_true')
    parser.add_argument('--keep-sessions', action='store_true')
    parser.add_argument('--web-use-output-dir', action='store_true')
    args, _ = parser.parse_known_args()
    return args


def main() -> None:
    args = _parse_args()
    _setup_logging(args.log_level)

    _fix_mime_types()
    app = build_app()

    loop = (
        asyncio.new_event_loop()
        if sys.platform != 'win32'
        else asyncio.ProactorEventLoop()  # type: ignore[attr-defined]
    )
    config = Config(
        app=app,
        host=args.host,
        port=args.port,
        loop=loop,  # type: ignore[arg-type]
        log_level=args.log_level.lower(),
        log_config=None,
        workers=1,
    )
    server = Server(config)

    logger.info(
        'Starting Downtify {} on http://{}:{}',
        api.state.version,
        args.host,
        args.port,
    )
    logger.info('Application log level (Loguru): {}', args.log_level.upper())
    loop.run_until_complete(server.serve())


if __name__ == '__main__':
    main()
