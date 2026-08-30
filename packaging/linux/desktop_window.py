#!/usr/bin/env python3
"""GTK + WebKit window for the Linux desktop package.

The frozen backend stays in the background; this process owns the app window
so Downtify opens like other desktop apps instead of a browser tab.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

INSTALL_DIR = Path(__file__).resolve().parent
BACKEND = INSTALL_DIR / 'Downtify'
DEFAULT_PORT = 8765
LOG_DIR = Path.home() / '.local' / 'share' / 'downtify'
ICON_CANDIDATES = (
    Path('/usr/share/icons/hicolor/256x256/apps/downtify.png'),
    INSTALL_DIR / 'downtify.png',
)


def disable_http_proxy() -> None:
    os.environ['NO_PROXY'] = '127.0.0.1,localhost,::1'
    os.environ['no_proxy'] = os.environ['NO_PROXY']
    for name in (
        'http_proxy',
        'https_proxy',
        'HTTP_PROXY',
        'HTTPS_PROXY',
        'all_proxy',
        'ALL_PROXY',
    ):
        os.environ.pop(name, None)


def urlopen_local(url: str, timeout: float = 0.6):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(url, timeout=timeout)


def backend_port() -> int:
    return int(os.environ.get('DOWNTIFY_PORT', str(DEFAULT_PORT)))


def backend_url(port: int) -> str:
    return f'http://127.0.0.1:{port}'


def server_ready(port: int) -> bool:
    try:
        health = backend_url(port) + '/'
        with urlopen_local(health, timeout=0.6) as resp:
            return 200 <= int(resp.status) < 500
    except (OSError, urllib.error.URLError):
        return False


def wait_for_server(port: int, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if server_ready(port):
            return True
        time.sleep(0.2)
    return False


def start_backend(port: int) -> subprocess.Popen[bytes] | None:
    if server_ready(port):
        return None
    env = os.environ.copy()
    env['DOWNTIFY_DESKTOP'] = '1'
    env['DOWNTIFY_NO_BROWSER'] = '1'
    env['DOWNTIFY_PORT'] = str(port)
    env['DOWNTIFY_BACKEND_ONLY'] = '1'
    if not BACKEND.is_file():
        raise FileNotFoundError(f'Missing backend: {BACKEND}')
    args = [
        str(BACKEND),
        '--no-browser',
        '--host',
        '127.0.0.1',
        '--port',
        str(port),
    ]
    return subprocess.Popen(
        args,
        cwd=str(INSTALL_DIR),
        env=env,
        start_new_session=True,
    )


def stop_backend(proc: subprocess.Popen[bytes] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except OSError:
        proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            proc.kill()


def load_gtk():
    import gi

    gi.require_version('Gtk', '3.0')
    webkit_version = None
    for version in ('4.1', '4.0'):
        try:
            gi.require_version('WebKit2', version)
            webkit_version = version
            break
        except ValueError:
            continue
    if webkit_version is None:
        raise RuntimeError('WebKit2 GTK bindings are not installed')
    from gi.repository import GLib, Gtk, WebKit2

    return GLib, Gtk, WebKit2


def open_window(port: int) -> None:
    GLib, Gtk, WebKit2 = load_gtk()
    GLib.set_prgname('Downtify')
    GLib.set_application_name('Downtify')

    window = Gtk.Window()
    window.set_title('Downtify')
    window.set_default_size(1280, 840)
    window.set_role('Downtify')
    for icon in ICON_CANDIDATES:
        if icon.is_file():
            window.set_icon_from_file(str(icon))
            break

    view = WebKit2.WebView()
    settings = view.get_settings()
    settings.set_enable_javascript(True)
    settings.set_allow_file_access_from_file_urls(True)
    window.add(view)
    view.load_uri(backend_url(port))
    window.connect('destroy', Gtk.main_quit)
    window.show_all()
    Gtk.main()


def write_error(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log = LOG_DIR / 'desktop-window.log'
    log.write_text(message + '\n', encoding='utf-8')
    print(message, file=sys.stderr)


def main() -> int:
    disable_http_proxy()
    os.environ.setdefault('DOWNTIFY_DESKTOP', '1')
    os.environ.setdefault('DOWNTIFY_NO_BROWSER', '1')
    port = backend_port()
    proc = None
    try:
        proc = start_backend(port)
        if not wait_for_server(port):
            write_error(
                'Downtify backend did not start. '
                'See ~/.local/share/downtify/downtify.log'
            )
            return 1
        open_window(port)
        return 0
    except Exception as exc:
        write_error(f'Downtify window failed: {exc}\n{traceback.format_exc()}')
        return 1
    finally:
        stop_backend(proc)


if __name__ == '__main__':
    raise SystemExit(main())
