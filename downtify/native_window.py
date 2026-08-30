"""Native desktop window around the local Downtify server."""

from __future__ import annotations

import os
import threading
import time
import urllib.error

from downtify.desktop import (
    DESKTOP_PORT,
    display_host,
    install_dir,
    urlopen_local,
)


def _url(host: str, port: int) -> str:
    return f'http://{display_host(host)}:{port}'


def wait_for_server(host: str, port: int, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    url = _url(host, port) + '/'
    while time.time() < deadline:
        try:
            with urlopen_local(url, timeout=0.6) as resp:
                if 200 <= int(resp.status) < 500:
                    return True
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)
            continue
        time.sleep(0.2)
    return False


def open_desktop_window(host: str, port: int) -> None:
    import webview

    icon_file = install_dir() / 'downtify.png'
    webview.create_window(
        'Downtify',
        _url(host, port),
        width=1280,
        height=840,
        min_size=(900, 600),
        background_color='#040000',
    )
    start_kwargs = {}
    if icon_file.is_file():
        start_kwargs['icon'] = str(icon_file)
    try:
        webview.start(**start_kwargs)
    except TypeError:
        webview.start()


def run_backend_in_thread() -> None:
    os.environ['DOWNTIFY_NO_BROWSER'] = '1'
    from main import main

    main()


def run_desktop_shell() -> None:
    from downtify.desktop import (
        apply_defaults,
        choose_free_port,
        is_our_server,
        port_in_use,
    )

    apply_defaults()
    os.environ['DOWNTIFY_NO_BROWSER'] = '1'
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('DOWNTIFY_PORT', str(DESKTOP_PORT)))
    already = port_in_use(host, port) and is_our_server(host, port)
    if not already:
        if port_in_use(host, port):
            port = choose_free_port(host, port)
            os.environ['DOWNTIFY_PORT'] = str(port)
        worker = threading.Thread(target=run_backend_in_thread, daemon=True)
        worker.start()
        if not wait_for_server(host, port):
            raise SystemExit('Downtify backend did not start')
    open_desktop_window(host, port)
