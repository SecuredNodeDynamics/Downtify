from __future__ import annotations

import pytest

from downtify import metadata_repair


def test_artists_reads_multi_value_tags():
    artists = metadata_repair._artists({
        'artist': ['Alexandre Desplat', 'Lang Lang', 'Prague Symphony Orchestra']
    })

    assert artists == [
        'Alexandre Desplat',
        'Lang Lang',
        'Prague Symphony Orchestra',
    ]


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


def test_scan_library_hides_matches_without_changes(tmp_path, monkeypatch):
    track = tmp_path / 'Artist - Song.mp3'
    track.write_bytes(b'not really audio')
    song = {
        'name': 'Song',
        'artists': ['Artist'],
        'album_name': 'Album',
    }

    monkeypatch.setattr(metadata_repair, '_song_from_file', lambda _path: song)
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda value: {
            **value,
            'musicbrainz_recording_id': 'mbid-recording',
        },
    )

    result = metadata_repair.scan_library(tmp_path)

    assert result['scanned'] == 1
    assert result['matched'] == 0
    assert result['items'] == []
    assert len(result['clean']) == 1


def test_scan_library_scans_batch_and_returns_only_fixable_items(
    tmp_path,
    monkeypatch,
):
    for index in range(3):
        (tmp_path / f'{index}.mp3').write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda path: {'name': path.stem, 'artists': ['Artist']},
    )
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda song: {
            **song,
            'name': f"{song['name']} fixed",
            'musicbrainz_recording_id': f"mbid-{song['name']}",
        },
    )

    result = metadata_repair.scan_library(tmp_path, limit=2)

    assert result['scanned'] == 2
    assert result['batch_scanned'] == 2
    assert result['matched'] == 2
    assert len(result['items']) == 2
    assert result['next_offset'] == 2
    assert result['complete'] is False


def test_scan_library_uses_start_offset_for_next_batch(tmp_path, monkeypatch):
    for index in range(4):
        (tmp_path / f'{index}.mp3').write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda path: {'name': path.stem, 'artists': ['Artist']},
    )
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda song: {
            **song,
            'name': f"{song['name']} fixed",
            'musicbrainz_recording_id': f"mbid-{song['name']}",
        },
    )

    result = metadata_repair.scan_library(tmp_path, limit=2, start=2)

    assert result['scanned'] == 4
    assert result['batch_scanned'] == 2
    assert [item['file'] for item in result['items']] == ['2.mp3', '3.mp3']
    assert result['complete'] is True


def test_scan_library_reports_progress(tmp_path, monkeypatch):
    for index in range(3):
        (tmp_path / f'{index}.mp3').write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda path: {'name': path.stem, 'artists': ['Artist']},
    )
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda song: {
            **song,
            'name': f"{song['name']} fixed",
            'musicbrainz_recording_id': f"mbid-{song['name']}",
        },
    )
    updates = []

    metadata_repair.scan_library(tmp_path, limit=2, progress_cb=updates.append)

    assert [update['scanned'] for update in updates] == [1, 2]
    assert updates[-1]['total'] == 3
    assert updates[-1]['matched'] == 2
    assert len(updates[-1]['items']) == 2
    assert updates[-1]['clean'] == []


def test_scan_library_treats_year_derived_from_release_date_as_fixed(
    tmp_path,
    monkeypatch,
):
    track = tmp_path / 'Artist - Song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {
            'name': 'Song',
            'artists': ['Artist'],
            'album_name': 'Album',
            'release_date': '2020-01-01',
            'year': '2020',
        },
    )
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda value: {
            **value,
            'release_date': '2020-01-01',
            'year': '2020',
            'musicbrainz_recording_id': 'mbid-recording',
        },
    )

    result = metadata_repair.scan_library(tmp_path)

    assert result['matched'] == 0
    assert result['items'] == []


def test_repair_file_applies_high_confidence_metadata(tmp_path, monkeypatch):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')
    applied = {}

    reads = iter([
        {'name': 'Song', 'artists': ['Artist']},
        {
            'name': 'Fixed Song',
            'artists': ['Artist'],
            'year': '2020',
            'release_date': '2020-01-01',
        },
    ])
    monkeypatch.setattr(metadata_repair, '_song_from_file', lambda _path: next(reads))
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda song: {
            **song,
            'name': 'Fixed Song',
            'year': '2020',
            'release_date': '2020-01-01',
            'musicbrainz_recording_id': 'mbid-recording',
        },
    )

    def fake_apply(path, metadata):
        applied['path'] = path
        applied['metadata'] = metadata

    monkeypatch.setattr(metadata_repair, 'apply_text_tags', fake_apply)
    monkeypatch.setattr(
        metadata_repair,
        'save_missing_artist_images',
        lambda *_args: [],
    )

    result = metadata_repair.repair_file(tmp_path, 'song.mp3')

    assert applied['path'] == track.resolve()
    assert applied['metadata']['name'] == 'Fixed Song'
    assert result['matched'] is True
    assert result['changes'] == []


def test_repair_file_saves_missing_artist_images(tmp_path, monkeypatch):
    artist = tmp_path / 'Artist'
    album = artist / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

    reads = iter([
        {'name': 'Song', 'artists': ['Artist']},
        {
            'name': 'Fixed Song',
            'artists': ['Artist'],
            'musicbrainz_artist_ids': [
                {'id': 'artist-mbid', 'name': 'Artist'},
            ],
        },
    ])
    monkeypatch.setattr(metadata_repair, '_song_from_file', lambda _path: next(reads))
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda song: {
            **song,
            'name': 'Fixed Song',
            'musicbrainz_recording_id': 'mbid-recording',
            'musicbrainz_artist_ids': [
                {'id': 'artist-mbid', 'name': 'Artist'},
            ],
        },
    )
    monkeypatch.setattr(metadata_repair, 'apply_text_tags', lambda *_args: None)

    saved = {}

    def fake_save(root, path, artists):
        saved['root'] = root
        saved['path'] = path
        saved['artists'] = artists
        return ['Artist/folder.jpg']

    monkeypatch.setattr(metadata_repair, 'save_missing_artist_images', fake_save)

    metadata_repair.repair_file(tmp_path, 'Artist/Album/song.mp3')

    assert saved['root'] == tmp_path.resolve()
    assert saved['path'] == track.resolve()
    assert saved['artists'] == [{'id': 'artist-mbid', 'name': 'Artist'}]


def test_scan_artist_images_lists_available_missing_art(tmp_path, monkeypatch):
    album = tmp_path / 'Artist' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

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
            'musicbrainz_artist_ids': [
                {'id': 'artist-mbid', 'name': 'Artist'},
            ],
        },
    )
    monkeypatch.setattr(
        metadata_repair,
        'missing_artist_image_items',
        lambda root, path, artists: [
            {
                'artist': artists[0]['name'],
                'artist_id': artists[0]['id'],
                'file': path.relative_to(root).as_posix(),
                'folder': 'Artist',
                'source': 'Wikimedia Commons',
            }
        ],
    )

    result = metadata_repair.scan_artist_images(tmp_path, limit=10)

    assert result['matched'] == 1
    assert result['items'][0]['artist'] == 'Artist'
    assert result['items'][0]['source'] == 'Wikimedia Commons'


def test_scan_artist_images_reports_progress(tmp_path, monkeypatch):
    album = tmp_path / 'Artist' / 'Album'
    album.mkdir(parents=True)
    for index in range(2):
        (album / f'song-{index}.mp3').write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {'name': 'Song', 'artists': ['Artist']},
    )
    monkeypatch.setattr(
        metadata_repair,
        '_artist_image_scan_candidates',
        lambda root, path, _current=None: [
            {
                'artist': 'Artist',
                'artist_id': 'artist-mbid',
                'file': path.relative_to(root).as_posix(),
                'folder': 'Artist',
                'source': 'Album cover fallback',
            }
        ],
    )
    updates = []

    metadata_repair.scan_artist_images(
        tmp_path,
        limit=10,
        progress_cb=updates.append,
    )

    assert updates
    assert updates[-1]['scanned'] == 2
    assert updates[-1]['matched'] == 1


def test_repair_artist_image_writes_for_requested_artist(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Artist' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

    saved = {}

    def fake_save(root, path, artists):
        saved['root'] = root
        saved['path'] = path
        saved['artists'] = artists
        return ['Artist/folder.jpg']

    monkeypatch.setattr(metadata_repair, 'save_missing_artist_images', fake_save)

    result = metadata_repair.repair_artist_image(
        tmp_path,
        'Artist/Album/song.mp3',
        {'id': 'artist-mbid', 'name': 'Artist'},
    )

    assert saved['root'] == tmp_path.resolve()
    assert saved['path'] == track.resolve()
    assert saved['artists'] == [{'id': 'artist-mbid', 'name': 'Artist'}]
    assert result['saved'] == ['Artist/folder.jpg']


def test_repair_file_fails_when_metadata_does_not_persist(
    tmp_path,
    monkeypatch,
):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')

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
    monkeypatch.setattr(metadata_repair, 'apply_text_tags', lambda *_args: None)

    with pytest.raises(ValueError, match='Metadata write did not persist'):
        metadata_repair.repair_file(tmp_path, 'song.mp3')
