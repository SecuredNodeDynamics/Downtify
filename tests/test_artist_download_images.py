from __future__ import annotations

from pathlib import Path

from downtify.artist_art import save_artist_images_for_track

# Minimal JPEG header so _extension_for_image() picks ``.jpg``.
_JPEG = b'\xff\xd8\xff\xe0' + b'\x00' * 32


def _make_track(root: Path) -> Path:
    track = root / 'Some Artist - Song.m4a'
    track.write_bytes(b'audio')
    return track


def test_saves_artist_photo_into_planned_folder(tmp_path):
    track = _make_track(tmp_path)
    artists = [{'name': 'Some Artist', 'id': ''}]

    saved = save_artist_images_for_track(
        tmp_path,
        track,
        artists,
        lambda _artist: (_JPEG, 'Test'),
    )

    target = tmp_path / 'Some Artist' / 'Some Artist.jpg'
    assert target.is_file()
    assert target.read_bytes() == _JPEG
    assert any('Some Artist' in entry for entry in saved)


def test_skips_when_artist_image_already_exists(tmp_path):
    track = _make_track(tmp_path)
    artists = [{'name': 'Some Artist', 'id': ''}]

    first = save_artist_images_for_track(
        tmp_path, track, artists, lambda _artist: (_JPEG, 'Test')
    )
    assert first

    calls = {'n': 0}

    def fetch(_artist):
        calls['n'] += 1
        return _JPEG, 'Test'

    second = save_artist_images_for_track(tmp_path, track, artists, fetch)

    assert second == []
    assert calls['n'] == 0


def test_no_write_when_fetcher_returns_nothing(tmp_path):
    track = _make_track(tmp_path)
    artists = [{'name': 'Nobody', 'id': ''}]

    saved = save_artist_images_for_track(
        tmp_path, track, artists, lambda _artist: (None, '')
    )

    assert saved == []
    assert not (tmp_path / 'Nobody').exists()


def test_fetcher_exception_is_non_fatal(tmp_path):
    track = _make_track(tmp_path)
    artists = [{'name': 'Boom', 'id': ''}]

    def fetch(_artist):
        raise RuntimeError('network down')

    saved = save_artist_images_for_track(tmp_path, track, artists, fetch)

    assert saved == []


def test_primary_only_policy_limits_to_first_artist(tmp_path):
    track = _make_track(tmp_path)
    artists = [
        {'name': 'Lead', 'id': ''},
        {'name': 'Feature', 'id': ''},
    ]

    save_artist_images_for_track(
        tmp_path,
        track,
        artists,
        lambda _artist: (_JPEG, 'Test'),
        artist_folder_policy='primary_only',
    )

    assert (tmp_path / 'Lead' / 'Lead.jpg').is_file()
    assert not (tmp_path / 'Feature').exists()
