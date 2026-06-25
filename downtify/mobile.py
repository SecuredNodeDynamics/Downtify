"""Embedded server bootstrap for the Android (Chaquopy) build.

This module lets the APK run the *entire* Downtify FastAPI backend in-process
on ``127.0.0.1`` so the app can search, download, transcode and tag audio
fully on-device — no external server required.

The Android host (``MainActivity``) starts the Python interpreter through
Chaquopy and calls :func:`run_server` on a background thread. The Capacitor
WebView then talks to the local server exactly like it would talk to a remote
one.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

DEFAULT_PORT = 8765
DEFAULT_HOST = '127.0.0.1'


def prepare_ffmpeg(
    native_lib_dir: str, files_dir: str
) -> Optional[str]:
    """Expose the bundled ffmpeg/ffprobe to yt-dlp on Android.

    Modern Android only allows executing binaries from the app's native
    library directory, and only files named ``lib*.so`` are extracted there.
    We therefore ship ffmpeg as ``libffmpeg.so`` (and optionally
    ``libffprobe.so``) under ``jniLibs/<abi>/`` and create correctly named
    symlinks in a private ``bin`` directory that point back at the executable
    real files, so yt-dlp can discover them by name.

    Returns the directory to pass as ``ffmpeg_location`` (yt-dlp accepts a
    directory) or ``None`` if no bundled binary is present.
    """

    native = Path(native_lib_dir)
    bin_dir = Path(files_dir) / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)

    mapping = {
        'ffmpeg': 'libffmpeg.so',
        'ffprobe': 'libffprobe.so',
    }
    linked_any = False
    for tool, lib_name in mapping.items():
        source = native / lib_name
        if not source.exists():
            continue
        target = bin_dir / tool
        try:
            if target.is_symlink() or target.exists():
                target.unlink()
            target.symlink_to(source)
            linked_any = True
        except OSError:
            # Some devices disallow symlinks in app storage; fall back to
            # pointing yt-dlp straight at the native lib directory instead.
            return native_lib_dir if (native / 'libffmpeg.so').exists() else None

    return str(bin_dir) if linked_any else None


def configure_environment(
    *,
    data_dir: str,
    download_dir: str,
    ffmpeg_location: Optional[str] = None,
    port: int = DEFAULT_PORT,
    host: str = DEFAULT_HOST,
) -> None:
    """Point the backend at app-writable directories before it imports.

    ``main.py`` reads these locations from the environment at import time, so
    they must be set *before* the app module is imported.
    """

    os.environ['DOWNTIFY_PORT'] = str(port)
    os.environ['HOST'] = host
    os.environ['DATABASE_DIR'] = data_dir
    os.environ['DOWNLOAD_DIR'] = download_dir
    # The UI is served from the app's bundled assets, not by this server.
    os.environ['DOWNTIFY_SERVE_SPA'] = '0'
    if ffmpeg_location:
        os.environ['DOWNTIFY_FFMPEG_LOCATION'] = ffmpeg_location

    Path(data_dir).mkdir(parents=True, exist_ok=True)
    Path(download_dir).mkdir(parents=True, exist_ok=True)


_server = None


def run_server(
    *,
    data_dir: str,
    download_dir: str,
    ffmpeg_location: Optional[str] = None,
    native_lib_dir: Optional[str] = None,
    port: int = DEFAULT_PORT,
    host: str = DEFAULT_HOST,
    log_level: str = 'info',
) -> None:
    """Start the embedded server (blocking).

    Call this from a dedicated background thread on the Android side.
    """

    if not ffmpeg_location and native_lib_dir:
        ffmpeg_location = prepare_ffmpeg(native_lib_dir, data_dir)

    configure_environment(
        data_dir=data_dir,
        download_dir=download_dir,
        ffmpeg_location=ffmpeg_location,
        port=port,
        host=host,
    )

    import asyncio

    from uvicorn import Config, Server

    # Imported lazily so configure_environment() runs first — main.py reads
    # DOWNLOAD_DIR / DATABASE_DIR at import time.
    import main as downtify_main

    downtify_main._setup_logging(log_level)
    downtify_main._fix_mime_types()
    app = downtify_main.build_app()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    config = Config(
        app=app,
        host=host,
        port=int(os.environ.get('DOWNTIFY_PORT', port)),
        loop=loop,
        log_level=log_level.lower(),
        log_config=None,
        workers=1,
    )
    global _server
    _server = Server(config)
    loop.run_until_complete(_server.serve())


def stop_server() -> None:
    """Ask the running server to shut down, if any."""

    if _server is not None:
        _server.should_exit = True
