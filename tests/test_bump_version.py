"""Tests for version.sh — checks the script exists, validates its flags
and verifies it updates all three version files correctly."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / 'version.sh'


def _script_arg(path: Path) -> str:
    if sys.platform == 'win32':
        return './' + path.name
    return str(path)


def _write_python_shim(cwd: Path) -> None:
    if sys.platform != 'win32':
        return
    shim = cwd / 'python'
    shim.write_text(
        '#!/usr/bin/env bash\npython3 "$@"\n',
        encoding='utf-8',
        newline='\n',
    )
    shim.chmod(shim.stat().st_mode | stat.S_IXUSR)


def _run_script(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = ['bash', _script_arg(SCRIPT if cwd is None else cwd / 'version.sh'), *args]
    run_cwd = cwd or SCRIPT.parent
    if cwd is not None:
        _write_python_shim(run_cwd)
    env = os.environ.copy()
    env['PATH'] = f'.:{Path(sys.executable).parent}:{env.get("PATH", "")}'
    if cwd is not None and sys.platform == 'win32':
        env['PYTHON'] = './python'
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=run_cwd,
        env=env,
        check=False,
    )


def test_script_exists():
    assert SCRIPT.exists(), 'version.sh is missing from repo root'


def test_script_is_executable():
    if sys.platform == 'win32':
        pytest.skip('POSIX executable bits are not meaningful on Windows')
    assert SCRIPT.stat().st_mode & 0o111, 'version.sh is not executable'


def test_current_flag_returns_valid_semver():
    result = _run_script('--current')
    assert result.returncode == 0
    version = result.stdout.strip()
    parts = version.split('.')
    assert len(parts) == 3, f'Not semver: {version!r}'
    assert all(p.isdigit() for p in parts), f'Non-numeric parts in {version!r}'


def test_invalid_semver_rejected():
    result = _run_script('not-semver')
    assert result.returncode != 0


def test_missing_argument_shows_usage():
    result = _run_script()
    assert result.returncode != 0


def _setup_fake_repo(base: Path) -> None:
    """Create minimal stubs of every file that version.sh updates."""
    (base / 'downtify').mkdir()
    (base / 'downtify' / '__init__.py').write_text(
        "__version__ = '1.0.0'\n", encoding='utf-8'
    )
    (base / 'pyproject.toml').write_text(
        '[project]\nversion = "1.0.0"\n', encoding='utf-8'
    )
    (base / 'frontend').mkdir()
    (base / 'frontend' / 'package.json').write_text(
        '{\n  "version": "1.0.0"\n}\n', encoding='utf-8'
    )
    (base / 'frontend' / 'package-lock.json').write_text(
        '{\n  "version": "1.0.0",\n'
        '  "packages": {\n'
        '    "": { "version": "1.0.0" },\n'
        '    "node_modules/example": { "version": "1.0.0" }\n'
        '  }\n'
        '}\n',
        encoding='utf-8',
    )
    (base / 'Makefile').write_text(
        'DOWNTIFY_VERSION := 1.0.0\n'
        'TARGET := ghcr.io/securednodedynamics/downtify\n',
        encoding='utf-8',
    )
    (base / 'Dockerfile').write_text(
        'LABEL version="1.0.0"\n'
        '      org.opencontainers.image.version="1.0.0" \\\n',
        encoding='utf-8',
    )


def _copy_script_for_fake_repo(base: Path) -> Path:
    script_copy = base / 'version.sh'
    shutil.copy(SCRIPT, script_copy)
    if sys.platform == 'win32':
        text = script_copy.read_text(encoding='utf-8')
        text = text.replace('"${PYTHON:-python}" - <<PY', './python - <<PY')
        script_copy.write_text(text, encoding='utf-8', newline='\n')
    return script_copy


def test_bump_updates_all_three_files(tmp_path):
    _setup_fake_repo(tmp_path)
    _copy_script_for_fake_repo(tmp_path)

    result = _run_script('2.3.4', cwd=tmp_path)
    assert result.returncode == 0, result.stderr

    assert (
        "__version__ = '2.3.4'"
        in (tmp_path / 'downtify' / '__init__.py').read_text()
    )
    assert 'version = "2.3.4"' in (tmp_path / 'pyproject.toml').read_text()
    assert (
        '"version": "2.3.4"'
        in (tmp_path / 'frontend' / 'package.json').read_text()
    )
    assert (
        '"version": "2.3.4"'
        in (tmp_path / 'frontend' / 'package-lock.json').read_text()
    )
    assert (
        '"node_modules/example": {\n      "version": "1.0.0"'
        in (tmp_path / 'frontend' / 'package-lock.json').read_text()
    )
    assert 'DOWNTIFY_VERSION := 2.3.4' in (tmp_path / 'Makefile').read_text()
    assert (
        'TARGET := ghcr.io/securednodedynamics/downtify'
        in (tmp_path / 'Makefile').read_text()
    )
    dockerfile = (tmp_path / 'Dockerfile').read_text()
    assert 'LABEL version="2.3.4"' in dockerfile
    assert 'org.opencontainers.image.version="2.3.4"' in dockerfile


def test_bump_noop_when_already_at_target(tmp_path):
    _setup_fake_repo(tmp_path)
    _copy_script_for_fake_repo(tmp_path)

    result = _run_script('1.0.0', cwd=tmp_path)
    assert result.returncode == 0
    assert 'nothing to do' in result.stdout.lower()


def test_current_flag_in_fake_repo(tmp_path):
    _setup_fake_repo(tmp_path)
    _copy_script_for_fake_repo(tmp_path)

    result = _run_script('--current', cwd=tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == '1.0.0'
