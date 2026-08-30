#!/usr/bin/env python3
"""Build desktop installers: Linux .deb and Windows Inno Setup .exe."""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import tomllib
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PAYLOAD = ROOT / 'dist' / 'desktop' / 'payload'
ICONS = ROOT / 'dist' / 'desktop' / 'icons'
WORK = ROOT / 'build' / 'desktop'
CACHE = ROOT / 'dist' / 'desktop' / 'cache'
WIN_FFMPEG_ZIP = (
    'https://github.com/BtbN/FFmpeg-Builds/releases/download/'
    'latest/ffmpeg-master-latest-win64-gpl.zip'
)
WIN_PYTHON_URL = (
    'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe'
)
WINE_PYTHON = Path.home() / '.wine' / 'drive_c' / 'Python312' / 'python.exe'
WINE_ISCC = (
    Path.home()
    / '.wine'
    / 'drive_c'
    / 'Program Files (x86)'
    / 'Inno Setup 6'
    / 'ISCC.exe'
)
APP_ICON_SOURCES = (
    ROOT / 'frontend' / 'src' / 'assets' / 'downtify-app-icon.png',
    ROOT / 'frontend' / 'public' / 'android-chrome-512x512.png',
    ROOT
    / 'frontend'
    / 'android'
    / 'app'
    / 'src'
    / 'main'
    / 'res'
    / 'mipmap-xxxhdpi'
    / 'ic_launcher.png',
)
LINUX_ICON_SIZES = (48, 128, 256, 512)
ICON_PNG_SIZE = 256
ICO_SIZES = ((16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256))


def version() -> str:
    text = (ROOT / 'downtify' / '__init__.py').read_text(encoding='utf-8')
    for line in text.splitlines():
        if line.startswith('__version__'):
            return line.split('=', 1)[1].strip().strip('\'"')
    raise RuntimeError('Could not read downtify.__version__')


def wine_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault('WINEDEBUG', '-all')
    env.setdefault('WINEDLLOVERRIDES', 'winemenubuilder.exe=d')
    return env


def run(cmd: list[str], **kwargs) -> None:
    print('+', ' '.join(str(part) for part in cmd), flush=True)
    subprocess.check_call(cmd, cwd=kwargs.pop('cwd', ROOT), **kwargs)


def to_wine_path(path: Path) -> str:
    resolved = path.resolve()
    return 'Z:' + str(resolved).replace('/', '\\')


def project_deps() -> list[str]:
    data = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    return list(data['project']['dependencies'])


def ensure_frontend() -> None:
    index = ROOT / 'frontend' / 'dist' / 'index.html'
    if index.is_file():
        return
    run(['npm', 'run', 'build', '--prefix', 'frontend'])


def load_app_icon() -> Image.Image:
    for path in APP_ICON_SOURCES:
        if path.is_file():
            print(f'Using app logo {path}', flush=True)
            return Image.open(path).convert('RGBA')
    raise RuntimeError('No Downtify app logo PNG was found')


def square_icon(image: Image.Image, size: int) -> Image.Image:
    canvas = Image.new('RGBA', (size, size), (4, 0, 0, 255))
    fitted = image.copy()
    fitted.thumbnail((size, size), Image.Resampling.LANCZOS)
    x = (size - fitted.width) // 2
    y = (size - fitted.height) // 2
    canvas.paste(fitted, (x, y), fitted)
    return canvas


def write_icons() -> tuple[Path, Path]:
    ICONS.mkdir(parents=True, exist_ok=True)
    source = load_app_icon()
    png_path = ICONS / 'downtify.png'
    ico_path = ICONS / 'downtify.ico'
    for size in LINUX_ICON_SIZES:
        sized = square_icon(source, size)
        sized.save(ICONS / f'downtify-{size}.png')
        if size == ICON_PNG_SIZE:
            sized.save(png_path)
    square_icon(source, ICON_PNG_SIZE).save(ico_path, sizes=list(ICO_SIZES))
    return png_path, ico_path


def pyinstaller_args(icon: Path, *, windows: bool, wine: bool) -> list[str]:
    def loc(path: Path) -> str:
        return to_wine_path(path) if wine else str(path)

    sep = ';' if windows else ':'
    frontend_dist = ROOT / 'frontend' / 'dist'
    add_data = f'{loc(frontend_dist)}{sep}frontend/dist'
    cmd = [
        '-m',
        'PyInstaller',
        '--noconfirm',
        '--clean',
        '--windowed',
        '--name',
        'Downtify',
        '--distpath',
        loc(PAYLOAD),
        '--workpath',
        loc(WORK),
        '--specpath',
        loc(WORK),
        f'--paths={loc(ROOT)}',
        f'--icon={loc(icon)}',
        f'--add-data={add_data}',
        '--collect-all',
        'fastapi',
        '--collect-all',
        'starlette',
        '--collect-all',
        'uvicorn',
        '--collect-all',
        'anyio',
        '--collect-all',
        'yt_dlp',
        '--collect-all',
        'ytmusicapi',
        '--collect-submodules',
        'downtify',
        '--copy-metadata',
        'yt-dlp',
        '--copy-metadata',
        'ytmusicapi',
        '--hidden-import',
        'main',
        '--hidden-import',
        'uvicorn.logging',
        '--hidden-import',
        'uvicorn.loops.auto',
        '--hidden-import',
        'uvicorn.protocols.http.auto',
        '--hidden-import',
        'uvicorn.protocols.websockets.auto',
        loc(ROOT / 'downtify' / 'desktop_app.py'),
    ]
    if windows:
        cmd[-1:-1] = [
            '--collect-all',
            'webview',
            '--hidden-import',
            'webview.platforms.edgechromium',
        ]
    return cmd


def ensure_pyinstaller() -> None:
    if importlib.util.find_spec('PyInstaller') is None:
        run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])


def ensure_windows_python() -> None:
    if WINE_PYTHON.is_file():
        return
    if shutil.which('wine') is None:
        raise RuntimeError('wine is required to build Windows packages here')
    CACHE.mkdir(parents=True, exist_ok=True)
    installer = CACHE / 'python-3.12.10-amd64.exe'
    if not installer.is_file():
        print(f'Downloading Windows Python ({WIN_PYTHON_URL})', flush=True)
        urlretrieve(WIN_PYTHON_URL, installer)
    print('Installing Windows Python into the Wine prefix…', flush=True)
    run(
        [
            'wine',
            str(installer),
            '/quiet',
            'InstallAllUsers=0',
            'PrependPath=0',
            'Include_doc=0',
            'Include_test=0',
            'Include_pip=1',
            'TargetDir=C:\\Python312',
        ],
        env=wine_env(),
    )
    if not WINE_PYTHON.is_file():
        raise RuntimeError(
            f'Windows Python did not install at {WINE_PYTHON}'
        )


def ensure_windows_pyinstaller() -> None:
    ensure_windows_python()
    run(
        [
            'wine',
            r'C:\Python312\python.exe',
            '-m',
            'pip',
            'install',
            '--upgrade',
            'pip',
            'pyinstaller',
            'pywebview',
            *project_deps(),
        ],
        env=wine_env(),
    )


def build_payload(icon: Path, *, windows: bool) -> Path:
    if PAYLOAD.exists():
        shutil.rmtree(PAYLOAD)
    wine = windows and os.name != 'nt'
    if wine:
        ensure_windows_pyinstaller()
        run(
            [
                'wine',
                r'C:\Python312\python.exe',
                *pyinstaller_args(icon, windows=True, wine=True),
            ],
            env=wine_env(),
        )
    else:
        ensure_pyinstaller()
        run(
            [
                sys.executable,
                *pyinstaller_args(
                    icon, windows=windows, wine=False
                ),
            ]
        )
    app_dir = PAYLOAD / 'Downtify'
    if not app_dir.is_dir():
        raise RuntimeError(f'PyInstaller output missing: {app_dir}')
    exe = app_dir / ('Downtify.exe' if windows else 'Downtify')
    if windows and not exe.is_file():
        raise RuntimeError(f'Windows exe missing: {exe}')
    return app_dir


def linux_arch() -> str:
    machine = os.uname().machine
    return {
        'x86_64': 'amd64',
        'amd64': 'amd64',
        'aarch64': 'arm64',
        'arm64': 'arm64',
    }.get(machine, machine)


def build_deb(app_dir: Path, ver: str) -> Path:
    arch = linux_arch()
    root = ROOT / 'dist' / 'desktop' / 'linux' / 'debroot'
    if root.exists():
        shutil.rmtree(root)
    opt = root / 'opt' / 'downtify'
    debian = root / 'DEBIAN'
    applications = root / 'usr' / 'share' / 'applications'
    hicolor = root / 'usr' / 'share' / 'icons' / 'hicolor'
    bindir = root / 'usr' / 'bin'
    for path in (debian, applications, bindir):
        path.mkdir(parents=True, exist_ok=True)
    shutil.copytree(app_dir, opt, dirs_exist_ok=True)
    for size in LINUX_ICON_SIZES:
        dest_dir = hicolor / f'{size}x{size}' / 'apps'
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            ICONS / f'downtify-{size}.png', dest_dir / 'downtify.png'
        )
    shutil.copy2(
        ROOT / 'packaging' / 'linux' / 'downtify.desktop',
        applications / 'downtify.desktop',
    )
    shutil.copy2(
        ROOT / 'packaging' / 'linux' / 'desktop_window.py',
        opt / 'desktop_window.py',
    )
    (opt / 'desktop_window.py').chmod(0o755)
    shutil.copy2(ICONS / 'downtify-256.png', opt / 'downtify.png')
    wrapper = bindir / 'downtify'
    wrapper.write_text(
        '#!/bin/sh\n'
        'export DOWNTIFY_DESKTOP=1\n'
        'export DOWNTIFY_NO_BROWSER=1\n'
        'export NO_PROXY=127.0.0.1,localhost,::1\n'
        'export no_proxy=127.0.0.1,localhost,::1\n'
        'cd /opt/downtify || exit 1\n'
        'exec python3 /opt/downtify/desktop_window.py "$@"\n',
        encoding='utf-8',
    )
    wrapper.chmod(0o755)
    binary = opt / 'Downtify'
    if binary.is_file():
        binary.chmod(0o755)
    installed = sum(
        path.stat().st_size for path in root.rglob('*') if path.is_file()
    )
    control = (
        f'Package: downtify\n'
        f'Version: {ver}\n'
        f'Section: sound\n'
        f'Priority: optional\n'
        f'Architecture: {arch}\n'
        f'Depends: ffmpeg, python3, gir1.2-gtk-3.0,\n'
        f' gir1.2-webkit2-4.1 | gir1.2-webkit2-4.0\n'
        f'Maintainer: SecuredNodeDynamics '
        f'<noreply@securednodedynamics>\n'
        f'Homepage: https://github.com/SecuredNodeDynamics/Downtify\n'
        f'Installed-Size: {max(1, installed // 1024)}\n'
        f'Description: Self-hosted Spotify playlist downloader\n'
        f' Downtify downloads playlists and songs with album art and\n'
        f' metadata through a local web interface.\n'
    )
    (debian / 'control').write_text(control, encoding='utf-8')
    out_dir = ROOT / 'dist' / 'desktop' / 'linux'
    out_dir.mkdir(parents=True, exist_ok=True)
    deb = out_dir / f'downtify_{ver}_{arch}.deb'
    if deb.exists():
        deb.unlink()
    run(['dpkg-deb', '--root-owner-group', '-b', str(root), str(deb)])
    return deb


def download_windows_ffmpeg(app_dir: Path) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    archive = CACHE / 'ffmpeg-win64.zip'
    if not archive.is_file():
        print(f'Downloading ffmpeg ({WIN_FFMPEG_ZIP})', flush=True)
        urlretrieve(WIN_FFMPEG_ZIP, archive)
    extract_dir = CACHE / 'ffmpeg-extract'
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(extract_dir)
    dest = app_dir / 'ffmpeg'
    dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name in ('ffmpeg.exe', 'ffprobe.exe'):
        matches = list(extract_dir.rglob(name))
        if not matches:
            continue
        shutil.copy2(matches[0], dest / name)
        copied += 1
    if copied < 1:
        raise RuntimeError('ffmpeg.exe not found in Windows ffmpeg zip')


def native_iscc() -> str | None:
    found = shutil.which('iscc') or shutil.which('ISCC')
    if found:
        return found
    program_files = os.environ.get('ProgramFiles(x86)') or os.environ.get(
        'ProgramFiles'
    )
    if program_files:
        candidate = Path(program_files) / 'Inno Setup 6' / 'ISCC.exe'
        if candidate.is_file():
            return str(candidate)
    return None


def iscc_command(ver: str, iss: Path) -> list[str]:
    define = f'/DMyAppVersion={ver}'
    if os.name == 'nt':
        iscc = native_iscc()
        if not iscc:
            raise RuntimeError(
                'Inno Setup compiler (iscc) was not found. '
                'Install it with: choco install innosetup -y'
            )
        return [iscc, define, str(iss)]
    if WINE_ISCC.is_file() and shutil.which('wine'):
        return ['wine', str(WINE_ISCC), define, to_wine_path(iss)]
    raise RuntimeError(
        'Inno Setup was not found. On Linux install it in Wine; '
        'on Windows run: choco install innosetup -y'
    )


def build_windows_installer(app_dir: Path, ver: str) -> Path:
    download_windows_ffmpeg(app_dir)
    shutil.copy2(ICONS / 'downtify.png', app_dir / 'downtify.png')
    iss = ROOT / 'packaging' / 'windows' / 'downtify.iss'
    cmd = iscc_command(ver, iss)
    kwargs = {'env': wine_env()} if cmd[0] == 'wine' else {}
    run(cmd, **kwargs)
    installer = (
        ROOT / 'dist' / 'desktop' / 'windows' / f'DowntifySetup-{ver}.exe'
    )
    if not installer.is_file():
        raise RuntimeError(f'Inno Setup did not produce {installer}')
    return installer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'target',
        choices=('linux', 'windows', 'all'),
        help='linux builds a .deb; windows builds an Inno Setup installer',
    )
    args = parser.parse_args()
    targets = ['linux', 'windows'] if args.target == 'all' else [args.target]
    ver = version()
    print(f'Building Downtify {ver} desktop packages', flush=True)
    ensure_frontend()
    png_icon, ico_icon = write_icons()

    built: list[Path] = []
    for target in targets:
        if target == 'linux' and os.name == 'nt':
            print('Skipping Linux .deb on Windows', flush=True)
            continue
        windows = target == 'windows'
        icon = ico_icon if windows else png_icon
        app_dir = build_payload(icon, windows=windows)
        if target == 'linux':
            built.append(build_deb(app_dir, ver))
        else:
            built.append(build_windows_installer(app_dir, ver))

    if not built:
        print('No packages were produced.', flush=True)
        return 1
    print('Built:')
    for path in built:
        print(f'  {path} ({path.stat().st_size} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
