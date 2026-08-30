"""Desktop-app defaults for frozen Linux/Windows installs."""

from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

_TRUTHY = {'1', 'true', 'yes'}
DESKTOP_PORT = 8765
_PORT_SCAN = 24


def is_frozen() -> bool:
    return bool(getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'))


def is_desktop() -> bool:
    if is_frozen():
        return True
    return os.getenv('DOWNTIFY_DESKTOP', '').strip().lower() in _TRUTHY


def resource_root() -> Path:
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def install_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return resource_root()


def user_data_dir() -> Path:
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA') or str(
            Path.home() / 'AppData' / 'Local'
        )
        return Path(base) / 'Downtify'
    xdg = os.environ.get('XDG_DATA_HOME', '').strip()
    if xdg:
        return Path(xdg) / 'downtify'
    return Path.home() / '.local' / 'share' / 'downtify'


def default_download_dir() -> Path:
    return Path.home() / 'Music' / 'Downtify'


def bundled_ffmpeg_dir() -> Path | None:
    for candidate in (
        install_dir() / 'ffmpeg',
        resource_root() / 'ffmpeg',
        install_dir(),
    ):
        ffmpeg = candidate / 'ffmpeg.exe'
        ffmpeg_unix = candidate / 'ffmpeg'
        if ffmpeg.is_file() or ffmpeg_unix.is_file():
            return candidate
    return None


def web_assets_dir() -> Path:
    bundled = resource_root() / 'frontend' / 'dist'
    if bundled.is_dir():
        return bundled
    return Path('frontend/dist')


def apply_defaults() -> None:
    """Fill desktop paths when env vars are unset.

    Docker and local ``python main.py`` keep ``/data`` and ``/downloads``
    unless ``DOWNTIFY_DESKTOP=1`` or the process is a frozen installer build.
    """

    if not is_desktop():
        return

    data_dir = user_data_dir()
    music_dir = default_download_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    music_dir.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault('DATABASE_DIR', str(data_dir))
    os.environ.setdefault('DOWNLOAD_DIR', str(music_dir))
    os.environ.setdefault('HOST', '127.0.0.1')
    os.environ.setdefault('DOWNTIFY_PORT', str(DESKTOP_PORT))
    os.environ.setdefault('WEB_GUI_LOCATION', str(web_assets_dir()))

    ffmpeg_dir = bundled_ffmpeg_dir()
    if ffmpeg_dir is not None:
        os.environ.setdefault('DOWNTIFY_FFMPEG_LOCATION', str(ffmpeg_dir))
        path = os.environ.get('PATH', '')
        extra = str(ffmpeg_dir)
        if extra not in path.split(os.pathsep):
            os.environ['PATH'] = extra + os.pathsep + path


def should_open_browser() -> bool:
    if not is_desktop():
        return False
    return os.getenv('DOWNTIFY_NO_BROWSER', '').strip().lower() not in _TRUTHY


def display_host(host: str) -> str:
    return '127.0.0.1' if host in {'0.0.0.0', '::'} else host


def port_in_use(host: str, port: int) -> bool:
    probe = display_host(host)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((probe, port))
    except OSError:
        return True
    finally:
        sock.close()
    return False


def urlopen_local(url: str, timeout: float = 0.8):
    """Fetch a loopback URL without using an HTTP proxy."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(url, timeout=timeout)


def is_our_server(host: str, port: int) -> bool:
    probe = display_host(host)
    url = f'http://{probe}:{port}/api/version'
    try:
        with urlopen_local(url, timeout=0.8) as resp:
            payload = json.loads(resp.read().decode('utf-8', errors='replace'))
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError):
        return False
    if isinstance(payload, dict):
        return 'version' in payload or 'downtify' in str(payload).lower()
    return isinstance(payload, str) and bool(payload.strip())


def choose_free_port(host: str, preferred: int) -> int:
    for port in range(preferred, preferred + _PORT_SCAN):
        if not port_in_use(host, port):
            return port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((display_host(host), 0))
    port = int(sock.getsockname()[1])
    sock.close()
    return port


def open_app_in_browser(host: str, port: int) -> None:
    if not should_open_browser():
        return
    webbrowser.open(f'http://{display_host(host)}:{port}')
