from __future__ import annotations

import pytest

from downtify import metadata_repair


def test_safe_library_path_rejects_traversal(tmp_path):
    with pytest.raises(ValueError, match='Invalid library path'):
        metadata_repair.safe_library_path(tmp_path, '../outside.mp3')


def test_safe_library_path_rejects_non_audio(tmp_path):
    with pytest.raises(ValueError, match='Unsupported audio file'):
        metadata_repair.safe_library_path(tmp_path, 'notes.txt')


def test_scan_library_reports_musicbrainz_match(tmp_path, monkeypatch):
    media = tmp_path / 'Artist' / 'Album'
    media.mkdir(parents=True)
    track = media / 'Artist - Song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {
            'name': 'Song',
            'artists': ['Artist'],
            'album_name': 'Album',
        },
    )
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda song: {
            **song,
            'name': 'Song',
            'release_date': '2020-01-01',
            'musicbrainz_recording_id': 'mbid-recording',
        },
    )

    result = metadata_repair.scan_library(tmp_path)

    assert result['total'] == 1
    assert result['matched'] == 1
    assert result['items'][0]['file'] == 'Artist/Album/Artist - Song.mp3'
    assert result['items'][0]['matched'] is True


def test_repair_file_applies_high_confidence_metadata(tmp_path, monkeypatch):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')
    applied = {}

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {'name': 'Song', 'artists': ['Artist']},
    )
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda song: {
            **song,
            'name': 'Fixed Song',
            'musicbrainz_recording_id': 'mbid-recording',
        },
    )

    def fake_apply(path, metadata):
        applied['path'] = path
        applied['metadata'] = metadata

    monkeypatch.setattr(metadata_repair, 'apply_text_tags', fake_apply)

    result = metadata_repair.repair_file(tmp_path, 'song.mp3')

    assert applied['path'] == track.resolve()
    assert applied['metadata']['name'] == 'Fixed Song'
    assert result['matched'] is True
