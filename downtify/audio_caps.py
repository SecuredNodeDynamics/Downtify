"""Detect on-device audio transcoding capabilities.

Determines which output formats Downtify can actually produce on the current
host, so the UI offers only working choices. This matters most on the embedded
Android (serverless) build, where ffmpeg may be absent or built without certain
encoders (e.g. ``libmp3lame`` for MP3). FLAC is a native ffmpeg encoder, while
MP3 requires the external ``libmp3lame``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

# Formats producible WITHOUT ffmpeg by downloading a native stream directly
# (see downloader._download_native_audio). AAC in an MP4/M4A container is what
# YouTube serves natively, so it is always available.
NATIVE_AUDIO_FORMATS: tuple[str, ...] = ('m4a',)

# Output format -> the ffmpeg encoder required to produce it.
_FORMAT_ENCODER: dict[str, str] = {
    'mp3': 'libmp3lame',
    'flac': 'flac',
    'm4a': 'aac',
    'ogg': 'libvorbis',
    'opus': 'libopus',
}

# Stable order for the formats Downtify exposes in the UI.
_FORMAT_ORDER: tuple[str, ...] = ('mp3', 'flac', 'm4a', 'ogg', 'opus')


def ffmpeg_binary() -> str | None:
    """Return a path to an invocable ffmpeg executable, or ``None``.

    Honors the explicit location used by the Android build
    (``DOWNTIFY_FFMPEG_LOCATION`` — a directory or a file) before falling back
    to ``PATH``.
    """

    location = os.getenv('DOWNTIFY_FFMPEG_LOCATION', '').strip()
    if location:
        candidate = Path(location)
        if candidate.is_dir():
            for name in ('ffmpeg', 'ffmpeg.exe'):
                exe = candidate / name
                if exe.exists():
                    return str(exe)
        elif candidate.exists():
            return str(candidate)
    return shutil.which('ffmpeg')


def ffmpeg_available() -> bool:
    return ffmpeg_binary() is not None


@lru_cache(maxsize=4)
def _encoders_for(binary: str) -> frozenset[str]:
    """Parse ``ffmpeg -encoders`` into a set of encoder names."""

    try:
        proc = subprocess.run(
            [binary, '-hide_banner', '-encoders'],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception:
        return frozenset()

    names: set[str] = set()
    for line in (proc.stdout or '').splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(('-', '=')):
            continue
        parts = stripped.split()
        flags = parts[0]
        # Encoder rows look like: "A....D libmp3lame  MP3 (...)" — a 6-char
        # capability column whose first char is the media type, then the name.
        if len(parts) >= 2 and len(flags) == 6 and flags[0] in 'VAS':
            if parts[1] != '=':
                names.add(parts[1])
    return frozenset(names)


def available_audio_formats() -> list[str]:
    """Output formats producible on this host, in a stable display order."""

    binary = ffmpeg_binary()
    if not binary:
        return [fmt for fmt in _FORMAT_ORDER if fmt in NATIVE_AUDIO_FORMATS]

    encoders = _encoders_for(binary)
    supported: set[str] = set(NATIVE_AUDIO_FORMATS)
    if encoders:
        for fmt, encoder in _FORMAT_ENCODER.items():
            if encoder in encoders:
                supported.add(fmt)
    else:
        # ffmpeg is present but the encoder probe failed; assume the encoders
        # that ship natively with any ffmpeg build are available.
        supported.update({'flac', 'm4a'})
    return [fmt for fmt in _FORMAT_ORDER if fmt in supported]


def clear_capability_cache() -> None:
    _encoders_for.cache_clear()
