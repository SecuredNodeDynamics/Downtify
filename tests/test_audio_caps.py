from __future__ import annotations

from pathlib import Path

import pytest

from downtify import audio_caps

_ENCODERS_OUTPUT = """Encoders:
 V..... = Video
 A..... = Audio
 S..... = Subtitle
 ------
 A....D aac                  AAC (Advanced Audio Coding)
 A....D flac                 FLAC (Free Lossless Audio Codec)
 A....D libmp3lame           libmp3lame MP3 (MPEG audio layer 3)
 A....D libvorbis            libvorbis
 A....D libopus              libopus Opus
"""

_ENCODERS_NO_MP3 = """Encoders:
 ------
 A....D aac                  AAC (Advanced Audio Coding)
 A....D flac                 FLAC (Free Lossless Audio Codec)
"""


@pytest.fixture(autouse=True)
def _clear_cache():
    audio_caps.clear_capability_cache()
    yield
    audio_caps.clear_capability_cache()


def test_no_ffmpeg_only_native_m4a(monkeypatch):
    monkeypatch.setattr(audio_caps, 'ffmpeg_binary', lambda: None)

    assert audio_caps.ffmpeg_available() is False
    assert audio_caps.available_audio_formats() == ['m4a']


def test_full_ffmpeg_offers_mp3_and_flac(monkeypatch):
    monkeypatch.setattr(audio_caps, 'ffmpeg_binary', lambda: '/usr/bin/ffmpeg')
    monkeypatch.setattr(
        audio_caps,
        '_encoders_for',
        lambda _binary: frozenset(
            {'aac', 'flac', 'libmp3lame', 'libvorbis', 'libopus'}
        ),
    )

    formats = audio_caps.available_audio_formats()

    assert formats == ['mp3', 'flac', 'm4a', 'ogg', 'opus']


def test_ffmpeg_without_lame_hides_mp3(monkeypatch):
    monkeypatch.setattr(audio_caps, 'ffmpeg_binary', lambda: '/usr/bin/ffmpeg')
    monkeypatch.setattr(
        audio_caps, '_encoders_for', lambda _binary: frozenset({'aac', 'flac'})
    )

    formats = audio_caps.available_audio_formats()

    assert 'mp3' not in formats
    assert 'flac' in formats
    assert 'm4a' in formats


def test_encoder_probe_failure_assumes_native_codecs(monkeypatch):
    monkeypatch.setattr(audio_caps, 'ffmpeg_binary', lambda: '/usr/bin/ffmpeg')
    monkeypatch.setattr(audio_caps, '_encoders_for', lambda _binary: frozenset())

    formats = audio_caps.available_audio_formats()

    assert 'flac' in formats
    assert 'm4a' in formats
    assert 'mp3' not in formats


def test_encoder_parsing_extracts_names(monkeypatch):
    class _Proc:
        stdout = _ENCODERS_OUTPUT
        stderr = ''

    monkeypatch.setattr(
        audio_caps.subprocess, 'run', lambda *a, **k: _Proc()
    )

    encoders = audio_caps._encoders_for('/usr/bin/ffmpeg')

    assert 'libmp3lame' in encoders
    assert 'flac' in encoders
    assert 'aac' in encoders
    # The flag legend rows ("= Audio") must not leak in as encoders.
    assert '=' not in encoders


def test_ffmpeg_binary_prefers_explicit_location(monkeypatch, tmp_path):
    exe = tmp_path / 'ffmpeg'
    exe.write_text('#!/bin/sh\n', encoding='utf-8')
    monkeypatch.setenv('DOWNTIFY_FFMPEG_LOCATION', str(tmp_path))

    assert audio_caps.ffmpeg_binary() == str(exe)


def test_ffmpeg_binary_accepts_file_location(monkeypatch, tmp_path):
    exe = tmp_path / 'libffmpeg.so'
    exe.write_text('#!/bin/sh\n', encoding='utf-8')
    monkeypatch.setenv('DOWNTIFY_FFMPEG_LOCATION', str(exe))

    assert audio_caps.ffmpeg_binary() == str(exe)


def test_ffmpeg_binary_falls_back_to_path(monkeypatch):
    monkeypatch.delenv('DOWNTIFY_FFMPEG_LOCATION', raising=False)
    monkeypatch.setattr(
        audio_caps.shutil, 'which', lambda name: '/opt/ffmpeg/ffmpeg'
    )

    assert audio_caps.ffmpeg_binary() == '/opt/ffmpeg/ffmpeg'


def test_missing_location_dir_returns_none(monkeypatch):
    monkeypatch.setenv('DOWNTIFY_FFMPEG_LOCATION', str(Path('/does/not/exist')))
    monkeypatch.setattr(audio_caps.shutil, 'which', lambda name: None)

    assert audio_caps.ffmpeg_binary() is None
