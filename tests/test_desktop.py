from __future__ import annotations

import os
from pathlib import Path

from downtify.desktop import (
    apply_defaults,
    default_download_dir,
)


def test_apply_defaults_is_noop_without_desktop_flag(monkeypatch) -> None:
    monkeypatch.delenv('DOWNTIFY_DESKTOP', raising=False)
    monkeypatch.delenv('DATABASE_DIR', raising=False)
    monkeypatch.delenv('DOWNLOAD_DIR', raising=False)
    apply_defaults()
    assert os.getenv('DATABASE_DIR') is None
    assert os.getenv('DOWNLOAD_DIR') is None


def test_apply_defaults_uses_user_dirs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv('DOWNTIFY_DESKTOP', '1')
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg'))
    monkeypatch.delenv('DATABASE_DIR', raising=False)
    monkeypatch.delenv('DOWNLOAD_DIR', raising=False)
    monkeypatch.delenv('HOST', raising=False)
    monkeypatch.delenv('DOWNTIFY_PORT', raising=False)
    monkeypatch.setattr(
        'downtify.desktop.default_download_dir',
        lambda: tmp_path / 'Music' / 'Downtify',
    )
    apply_defaults()
    assert Path(os.environ['DATABASE_DIR']) == tmp_path / 'xdg' / 'downtify'
    assert Path(os.environ['DOWNLOAD_DIR']) == tmp_path / 'Music' / 'Downtify'
    assert os.environ['HOST'] == '127.0.0.1'
    assert os.environ['DOWNTIFY_PORT'] == '8765'
    assert (tmp_path / 'xdg' / 'downtify').is_dir()


def test_default_download_dir_is_music_folder() -> None:
    assert default_download_dir() == Path.home() / 'Music' / 'Downtify'


def test_choose_free_port_skips_busy_port() -> None:
    import socket

    from downtify.desktop import choose_free_port, port_in_use

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('127.0.0.1', 0))
    busy = int(sock.getsockname()[1])
    try:
        assert port_in_use('127.0.0.1', busy)
        chosen = choose_free_port('127.0.0.1', busy)
        assert chosen != busy
        assert not port_in_use('127.0.0.1', chosen)
    finally:
        sock.close()
