"""PyInstaller entry point for the desktop app."""

from __future__ import annotations

import multiprocessing
import os
import shutil
import sys
from pathlib import Path


def _truthy(name: str) -> bool:
    return os.getenv(name, '').strip().lower() in {'1', 'true', 'yes'}


def _exec_linux_window() -> None:
    if os.name == 'nt' or _truthy('DOWNTIFY_BACKEND_ONLY'):
        return
    helper = Path(sys.executable).resolve().parent / 'desktop_window.py'
    if not helper.is_file():
        return
    python = shutil.which('python3') or '/usr/bin/python3'
    if not Path(python).is_file():
        return
    os.execv(python, [python, str(helper), *sys.argv[1:]])


def run() -> None:
    from downtify.desktop import apply_defaults

    apply_defaults()
    os.environ.setdefault('DOWNTIFY_NO_BROWSER', '1')
    if os.name == 'nt':
        from downtify.native_window import run_desktop_shell

        run_desktop_shell()
        return
    _exec_linux_window()
    from main import main

    main()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    run()
