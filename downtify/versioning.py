"""Runtime version helpers for Downtify."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

SEMVER_PARTS = 3


def parse_version(version: str) -> tuple[int, int, int] | None:
    parts = version.strip().split('.')
    if len(parts) != SEMVER_PARTS or not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def format_version(version: tuple[int, int, int]) -> str:
    return '.'.join(str(part) for part in version)


def bump_patch(version: str) -> str:
    parsed = parse_version(version)
    if parsed is None:
        raise ValueError(f'Invalid semver: {version}')
    major, minor, patch = parsed
    return f'{major}.{minor}.{patch + 1}'


def highest_version(*versions: str) -> str:
    valid = [parsed for version in versions if (parsed := parse_version(version))]
    if not valid:
        raise ValueError('No valid semver versions were provided')
    return format_version(max(valid))


def read_runtime_version(base_version: str, version_file: Path) -> str:
    try:
        saved = version_file.read_text(encoding='utf-8').strip()
    except FileNotFoundError:
        return base_version
    except Exception:
        return base_version

    if parse_version(saved) is None:
        return base_version
    return highest_version(base_version, saved)


def bump_runtime_version(base_version: str, version_file: Path) -> str:
    current = read_runtime_version(base_version, version_file)
    bumped = bump_patch(current)
    version_file.parent.mkdir(parents=True, exist_ok=True)
    version_file.write_text(f'{bumped}\n', encoding='utf-8')
    return bumped


def runtime_version_path(default: Path) -> Path:
    return Path(os.getenv('DOWNTIFY_VERSION_FILE', str(default)))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='python -m downtify.versioning')
    parser.add_argument('--base', required=True)
    parser.add_argument('--file', required=True, type=Path)
    parser.add_argument('--bump', action='store_true')
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.bump:
        print(bump_runtime_version(args.base, args.file))
    else:
        print(read_runtime_version(args.base, args.file))


if __name__ == '__main__':
    main()
