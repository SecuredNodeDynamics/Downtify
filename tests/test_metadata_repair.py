from __future__ import annotations

import pytest

from downtify import artist_art, metadata_repair


def test_artists_reads_multi_value_tags():
    artists = metadata_repair._artists({
        'artist': [
            'Alexandre Desplat',
            'Lang Lang',
            'Prague Symphony Orchestra',
        ]
    })

    assert artists == [
        'Alexandre Desplat',
        'Lang Lang',
        'Prague Symphony Orchestra',
    ]


def test_artists_ignores_invalid_tag_keys():
    class BrokenTags(dict):
        def get(self, key, default=None):
            if key == '\xa9ART':
                raise ValueError('missing vorbis tag')
            return super().get(key, default)

    artists = metadata_repair._artists(
        BrokenTags({'artist': 'Fallback Artist'})
    )

    assert artists == ['Fallback Artist']


def test_apply_text_tags_falls_back_to_format_class_for_m4a(
    tmp_path,
    monkeypatch,
):
    # An m4a whose container makes MutagenFile's quick sniff return None must
    # still be tagged via the format-specific class instead of raising
    # "Unsupported audio file" (the failure seen on the embedded Android build).
    track = tmp_path / 'song.m4a'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(metadata_repair, 'MutagenFile', lambda *_a, **_k: None)

    written: dict[str, object] = {}

    class FakeEasyMP4(dict):
        def __init__(self, _path):
            super().__init__()
            self.tags = self

        def save(self):
            written['saved'] = dict(self)

    import mutagen.easymp4

    monkeypatch.setattr(mutagen.easymp4, 'EasyMP4', FakeEasyMP4)

    metadata_repair.apply_text_tags(
        track,
        {'name': 'Song', 'artists': ['Ariana Grande', 'Nicki Minaj']},
    )

    assert written['saved']['title'] == ['Song']
    assert written['saved']['artist'] == ['Ariana Grande', 'Nicki Minaj']


def test_apply_text_tags_rejects_truly_unparseable_file(tmp_path, monkeypatch):
    track = tmp_path / 'broken.m4a'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(metadata_repair, 'MutagenFile', lambda *_a, **_k: None)

    import mutagen.easymp4

    def explode(_path):
        raise ValueError('cannot parse')

    monkeypatch.setattr(mutagen.easymp4, 'EasyMP4', explode)

    with pytest.raises(ValueError, match='Unsupported audio file'):
        metadata_repair.apply_text_tags(track, {'name': 'Song'})


def test_safe_library_path_rejects_traversal(tmp_path):
    with pytest.raises(ValueError, match='Invalid library path'):
        metadata_repair.safe_library_path(tmp_path, '../outside.mp3')


def test_safe_library_path_rejects_non_audio(tmp_path):
    with pytest.raises(ValueError, match='Unsupported audio file'):
        metadata_repair.safe_library_path(tmp_path, 'notes.txt')


def test_expand_artist_names_splits_featured_artists():
    names = metadata_repair.expand_artist_names(
        ['Lana Del Rey feat. A$AP Rocky', 'Katy Perry, 21 Savage']
    )

    assert names == ['Lana Del Rey', 'A$AP Rocky', 'Katy Perry', '21 Savage']


def test_scan_grouped_artists_reports_compound_artist_tag(
    tmp_path,
    monkeypatch,
):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {
            'name': 'Song',
            'artists': ['Artist One feat. Artist Two'],
            'album_name': 'Album',
        },
    )

    result = metadata_repair.scan_grouped_artists(tmp_path)

    assert result['matched'] == 1
    assert result['items'][0]['current']['artists'] == [
        'Artist One feat. Artist Two'
    ]
    assert result['items'][0]['candidate']['artists'] == [
        'Artist One',
        'Artist Two',
    ]


def test_scan_grouped_artists_reports_grouped_folder_with_split_tags(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Artist One & Artist Two' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {
            'name': 'Song',
            'artists': ['Artist One', 'Artist Two'],
            'album_name': 'Album',
        },
    )

    result = metadata_repair.scan_grouped_artists(tmp_path)

    assert result['matched'] == 1
    assert result['items'][0]['changes'] == [
        {
            'field': 'artist_folder',
            'label': 'Artist folder',
            'before': 'Artist One & Artist Two',
            'after': 'Artist One, Artist Two',
        }
    ]


def test_scan_grouped_artists_does_not_return_unrelated_clean_tracks(
    tmp_path,
    monkeypatch,
):
    track = tmp_path / 'Artist One' / 'Album' / 'song.mp3'
    track.parent.mkdir(parents=True)
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {
            'name': 'Song',
            'artists': ['Artist One'],
            'album_name': 'Album',
        },
    )

    result = metadata_repair.scan_grouped_artists(tmp_path)

    assert result['matched'] == 0
    assert result['items'] == []
    assert result['clean'] == []


def test_repair_grouped_artists_writes_split_artist_tags(
    tmp_path,
    monkeypatch,
):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')
    reads = iter([
        {'name': 'Song', 'artists': ['Artist One, Artist Two']},
        {'name': 'Song', 'artists': ['Artist One', 'Artist Two']},
        {'name': 'Song', 'artists': ['Artist One', 'Artist Two']},
    ])
    written = {}

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: next(reads),
    )

    def fake_apply(path, artists):
        written['path'] = path
        written['artists'] = artists

    monkeypatch.setattr(metadata_repair, 'apply_artist_tags', fake_apply)

    result = metadata_repair.repair_grouped_artists(tmp_path, 'song.mp3')

    assert written == {
        'path': track.resolve(),
        'artists': ['Artist One', 'Artist Two'],
    }
    assert result['changes'] == []
    assert result['current']['artists'] == ['Artist One', 'Artist Two']
    assert result['folder_verification']['folder_verified'] is True


def test_repair_grouped_artists_moves_file_and_removes_empty_group_folder(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Artist One, Artist Two' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')
    reads = iter([
        {'name': 'Song', 'artists': ['Artist One, Artist Two']},
        {'name': 'Song', 'artists': ['Artist One', 'Artist Two']},
        {'name': 'Song', 'artists': ['Artist One', 'Artist Two']},
    ])

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: next(reads),
    )
    monkeypatch.setattr(metadata_repair, 'apply_artist_tags', lambda *_args: None)

    result = metadata_repair.repair_grouped_artists(
        tmp_path,
        'Artist One, Artist Two/Album/song.mp3',
    )

    assert result['file'] == 'Artist One/Album/song.mp3'
    assert (tmp_path / 'Artist One' / 'Album' / 'song.mp3').is_file()
    assert (tmp_path / 'Artist Two').is_dir()
    assert not (tmp_path / 'Artist One, Artist Two').exists()
    assert result['folder_verification']['created_folders'] == [
        'Artist One',
        'Artist Two',
    ]
    assert result['folder_verification']['removed_folders'] == [
        'Artist One, Artist Two'
    ]
    assert result['folder_verification']['old_folders_remaining'] == []


def test_repair_grouped_artists_repairs_folder_when_tags_are_split(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Artist One & Artist Two' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')
    reads = iter([
        {'name': 'Song', 'artists': ['Artist One', 'Artist Two']},
        {'name': 'Song', 'artists': ['Artist One', 'Artist Two']},
        {'name': 'Song', 'artists': ['Artist One', 'Artist Two']},
    ])

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: next(reads),
    )
    monkeypatch.setattr(
        metadata_repair,
        'apply_artist_tags',
        lambda *_args: pytest.fail('tags are already split'),
    )

    result = metadata_repair.repair_grouped_artists(
        tmp_path,
        'Artist One & Artist Two/Album/song.mp3',
    )

    assert result['file'] == 'Artist One/Album/song.mp3'
    assert (tmp_path / 'Artist One' / 'Album' / 'song.mp3').is_file()
    assert (tmp_path / 'Artist Two').is_dir()
    assert not (tmp_path / 'Artist One & Artist Two').exists()
    assert result['folder_verification']['removed_folders'] == [
        'Artist One & Artist Two'
    ]


def test_artist_image_paths_prefers_named_artist_image(tmp_path):
    folder = tmp_path / 'Ariana Grande'
    folder.mkdir()
    (folder / 'folder.jpg').write_bytes(b'old-generic')
    named = folder / 'Ariana Grande.jpg'
    named.write_bytes(b'new-named')

    paths = artist_art.artist_image_paths(folder)

    assert paths[0] == named


def test_prune_stale_artist_sidecars_removes_generic_files(tmp_path):
    folder = tmp_path / 'Ariana Grande'
    folder.mkdir()
    named = folder / 'Ariana Grande.jpg'
    named.write_bytes(b'new-named')
    thumb = folder / 'thumb.jpg'
    thumb.write_bytes(b'old-thumb')

    removed = artist_art.prune_stale_artist_sidecars(
        folder,
        artist_name='Ariana Grande',
        keep=named,
    )

    assert 'thumb.jpg' in removed
    assert not thumb.exists()
    assert named.exists()


def test_repair_artist_image_bytes_removes_stale_generic_sidecars(tmp_path):
    folder = tmp_path / 'Ariana Grande'
    folder.mkdir()
    (folder / 'folder.jpg').write_bytes(b'old-generic')

    metadata_repair.repair_artist_image_bytes(
        tmp_path,
        '',
        {'id': '', 'name': 'Ariana Grande'},
        b'replacement-image',
        target_folder='Ariana Grande',
    )

    assert not (folder / 'folder.jpg').exists()
    assert (folder / 'Ariana Grande.jpg').read_bytes() == b'replacement-image'
    assert artist_art.artist_image_paths(folder)[0].name == 'Ariana Grande.jpg'


def test_ensure_named_artist_image_migrates_legacy_folder_sidecar(tmp_path):
    folder = tmp_path / 'Nas'
    folder.mkdir()
    (folder / 'folder.jpg').write_bytes(b'image-bytes')

    migrated = artist_art.ensure_named_artist_image(folder, tmp_path)

    assert migrated == ['Nas/Nas.jpg']
    assert (folder / 'Nas.jpg').read_bytes() == b'image-bytes'
    assert not (folder / 'folder.jpg').exists()
    assert artist_art.has_named_artist_image(folder) is True


def test_has_named_artist_image_accepts_artist_filename(tmp_path):
    artist = tmp_path / 'Aaron Copland'
    artist.mkdir()
    (artist / 'Aaron Copland.jpg').write_bytes(b'image')

    assert artist_art.has_named_artist_image(artist) is True
    assert artist_art.has_artist_image(artist) is True


def test_artist_image_target_uses_artist_folder_name(tmp_path):
    folder = tmp_path / 'Artist Name'
    folder.mkdir()
    target = artist_art.artist_image_target_path(
        folder,
        b'\x89PNG\r\n\x1a\nimage',
    )

    assert target.name == 'Artist Name.png'


def test_missing_artist_image_items_include_named_target(
    tmp_path, monkeypatch
):
    album = tmp_path / 'Artist' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        artist_art,
        'artist_or_fallback_image',
        lambda *_args: (b'image', 'Album cover fallback'),
    )

    items = artist_art.missing_artist_image_items(
        tmp_path,
        track,
        [{'id': 'artist-mbid', 'name': 'Artist'}],
    )

    assert items[0]['target'] == 'Artist/Artist.jpg'


def test_missing_artist_image_items_include_missing_artist_folder(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Primary Artist' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        artist_art,
        'artist_or_fallback_image',
        lambda *_args: (b'image', 'Album cover fallback'),
    )

    items = artist_art.missing_artist_image_items(
        tmp_path,
        track,
        [{'id': 'guest-mbid', 'name': 'Guest Artist'}],
    )

    assert items[0]['folder'] == 'Guest Artist'
    assert items[0]['target'] == 'Guest Artist/Guest Artist.jpg'
    assert not (tmp_path / 'Guest Artist').exists()


def test_missing_artist_image_items_can_skip_missing_artist_folders(
    tmp_path,
    monkeypatch,
):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        artist_art,
        'artist_or_fallback_image',
        lambda *_args: (b'image', 'Album cover fallback'),
    )

    items = artist_art.missing_artist_image_items(
        tmp_path,
        track,
        [{'id': 'guest-mbid', 'name': 'Guest Artist'}],
        artist_folder_policy='existing_only',
    )

    assert items == []
    assert not (tmp_path / 'Guest Artist').exists()


def test_missing_artist_image_items_primary_only_policy_limits_side_artists(
    tmp_path,
    monkeypatch,
):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        artist_art,
        'artist_or_fallback_image',
        lambda *_args: (b'image', 'Album cover fallback'),
    )

    items = artist_art.missing_artist_image_items(
        tmp_path,
        track,
        [
            {'id': 'primary-mbid', 'name': 'Primary Artist'},
            {'id': 'guest-mbid', 'name': 'Guest Artist'},
        ],
        artist_folder_policy='primary_only',
    )

    assert [item['artist'] for item in items] == ['Primary Artist']


def test_save_missing_artist_images_creates_missing_artist_folder(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Primary Artist' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        artist_art,
        'artist_or_fallback_image',
        lambda *_args: (b'image', 'Album cover fallback'),
    )

    saved = artist_art.save_missing_artist_images(
        tmp_path,
        track,
        [{'id': 'guest-mbid', 'name': 'Guest Artist'}],
    )

    assert saved == ['Guest Artist/Guest Artist.jpg']
    assert (
        tmp_path / 'Guest Artist' / 'Guest Artist.jpg'
    ).read_bytes() == b'image'


def test_save_missing_artist_images_does_not_create_empty_folder_without_image(
    tmp_path,
    monkeypatch,
):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        artist_art,
        'artist_or_fallback_image',
        lambda *_args: (None, ''),
    )

    saved = artist_art.save_missing_artist_images(
        tmp_path,
        track,
        [{'id': 'guest-mbid', 'name': 'Guest Artist'}],
    )

    assert saved == []
    assert not (tmp_path / 'Guest Artist').exists()


def test_missing_artist_image_items_skip_existing_folder_with_image(
    tmp_path,
    monkeypatch,
):
    artist = tmp_path / 'Artist'
    artist.mkdir()
    (artist / 'thumb.jpg').write_bytes(b'image')
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        artist_art,
        'artist_or_fallback_image',
        lambda *_args: (b'image', 'Album cover fallback'),
    )

    items = artist_art.missing_artist_image_items(
        tmp_path,
        track,
        [{'id': 'artist-mbid', 'name': 'Artist'}],
    )

    assert items == []


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


def test_scan_library_reports_missing_featured_artist_from_musicbrainz(
    tmp_path,
    monkeypatch,
):
    track = tmp_path / 'Primary - Song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {
            'name': 'Song',
            'artists': ['Primary'],
            'album_name': 'Album',
        },
    )
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda song: {
            **song,
            'artists': ['Primary', 'Featured Artist'],
            'artist': 'Primary, Featured Artist',
            'musicbrainz_recording_id': 'recording-mbid',
            'musicbrainz_artist_ids': [
                {'id': 'primary-mbid', 'name': 'Primary'},
                {'id': 'featured-mbid', 'name': 'Featured Artist'},
            ],
        },
    )

    result = metadata_repair.scan_library(tmp_path)

    assert result['matched'] == 1
    artist_change = result['items'][0]['changes'][0]
    assert artist_change['field'] == 'artists'
    assert artist_change['after'] == 'Primary, Featured Artist'


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
            'name': f'{song["name"]} fixed',
            'musicbrainz_recording_id': f'mbid-{song["name"]}',
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
            'name': f'{song["name"]} fixed',
            'musicbrainz_recording_id': f'mbid-{song["name"]}',
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
            'name': f'{song["name"]} fixed',
            'musicbrainz_recording_id': f'mbid-{song["name"]}',
        },
    )
    updates = []

    metadata_repair.scan_library(tmp_path, limit=2, progress_cb=updates.append)

    assert [update['scanned'] for update in updates] == [1, 2]
    assert updates[-1]['total'] == 3
    assert updates[-1]['matched'] == 2
    assert len(updates[-1]['items']) == 2
    assert updates[-1]['clean'] == []


def test_scan_album_images_scans_one_representative_per_album(tmp_path, monkeypatch):
    for name in ('01.mp3', '02.mp3'):
        path = tmp_path / 'Artist' / 'Album' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'not really audio')

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
        lambda song: {**song, 'cover_url': 'https://example.test/cover.jpg'},
    )
    monkeypatch.setattr(metadata_repair, 'embedded_cover_bytes', lambda _path: b'')

    result = metadata_repair.scan_album_images(tmp_path)

    assert result['total'] == 1
    assert result['scanned'] == 1
    assert result['matched'] == 1


def test_scan_album_images_reports_progress_before_slow_lookup(tmp_path, monkeypatch):
    track = tmp_path / 'Artist - Song.mp3'
    track.write_bytes(b'not really audio')
    updates = []

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {
            'name': 'Song',
            'artists': ['Artist'],
            'album_name': 'Album',
        },
    )

    def enrich(song):
        assert updates
        return {**song, 'cover_url': 'https://example.test/cover.jpg'}

    monkeypatch.setattr(metadata_repair, 'enrich_song_metadata', enrich)
    monkeypatch.setattr(metadata_repair, 'embedded_cover_bytes', lambda _path: b'')

    metadata_repair.scan_album_images(tmp_path, progress_cb=updates.append)

    assert updates[0]['scanned'] == 1
    assert updates[0]['total'] == 1


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
    monkeypatch.setattr(
        metadata_repair, '_song_from_file', lambda _path: next(reads)
    )
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
        lambda *_args, **_kwargs: [],
    )

    result = metadata_repair.repair_file(tmp_path, 'song.mp3')

    assert applied['path'] == track.resolve()
    assert applied['metadata']['name'] == 'Fixed Song'
    assert result['matched'] is True
    assert result['changes'] == []


def test_repair_file_uses_provided_candidate(tmp_path, monkeypatch):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')
    applied = {}

    reads = iter([
        {'name': 'Song', 'artists': ['Artist']},
        {'name': 'Scanned Fix', 'artists': ['Artist']},
    ])
    monkeypatch.setattr(
        metadata_repair, '_song_from_file', lambda _path: next(reads)
    )
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda _song: pytest.fail('repair_file should use provided candidate'),
    )

    candidate = {
        'name': 'Scanned Fix',
        'artists': ['Artist'],
        'musicbrainz_recording_id': 'mbid-recording',
    }

    def fake_apply(path, metadata):
        applied['path'] = path
        applied['metadata'] = metadata

    monkeypatch.setattr(metadata_repair, 'apply_text_tags', fake_apply)
    monkeypatch.setattr(
        metadata_repair,
        'save_missing_artist_images',
        lambda *_args, **_kwargs: [],
    )

    result = metadata_repair.repair_file(
        tmp_path,
        'song.mp3',
        candidate=candidate,
    )

    assert applied['path'] == track.resolve()
    assert applied['metadata'] == candidate
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
    monkeypatch.setattr(
        metadata_repair, '_song_from_file', lambda _path: next(reads)
    )
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
    monkeypatch.setattr(
        metadata_repair, 'apply_text_tags', lambda *_args: None
    )

    saved = {}

    def fake_save(root, path, artists, **_kwargs):
        saved['root'] = root
        saved['path'] = path
        saved['artists'] = artists
        return ['Artist/Artist.jpg']

    monkeypatch.setattr(
        metadata_repair, 'save_missing_artist_images', fake_save
    )

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
        lambda root, path, artists, **_kwargs: [
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


def test_scan_artist_images_reports_clean_items(tmp_path, monkeypatch):
    track = tmp_path / 'Artist - Song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {'name': 'Song', 'artists': ['Artist']},
    )
    monkeypatch.setattr(
        metadata_repair,
        '_artist_image_scan_candidates',
        lambda *_args: [],
    )

    result = metadata_repair.scan_artist_images(tmp_path, limit=10)

    assert result['items'] == []
    assert result['clean'] == [
        {
            'file': 'Artist - Song.mp3',
            'artist': 'Artist',
            'folder': '',
        }
    ]


def test_artist_image_scan_includes_featured_musicbrainz_artists(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Primary' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {
            'name': 'Song',
            'artists': ['Primary'],
            'musicbrainz_artist_ids': [
                {'id': 'primary-mbid', 'name': 'Primary'},
            ],
        },
    )
    monkeypatch.setattr(
        metadata_repair,
        'enrich_song_metadata',
        lambda song: {
            **song,
            'artists': ['Primary', 'Featured Artist'],
            'musicbrainz_artist_ids': [
                {'id': 'primary-mbid', 'name': 'Primary'},
                {'id': 'featured-mbid', 'name': 'Featured Artist'},
            ],
        },
    )
    seen_artists = []

    def fake_missing(_root, _path, artists, **_kwargs):
        seen_artists.extend(artists)
        return [
            {
                'artist': artist['name'],
                'artist_id': artist['id'],
                'file': 'Primary/Album/song.mp3',
                'folder': artist['name'],
                'source': 'Wikimedia Commons',
            }
            for artist in artists
        ]

    monkeypatch.setattr(
        metadata_repair, 'missing_artist_image_items', fake_missing
    )

    result = metadata_repair.scan_artist_images(tmp_path, limit=10)

    assert [artist['name'] for artist in seen_artists] == [
        'Primary',
        'Featured Artist',
    ]
    assert [item['artist'] for item in result['items']] == [
        'Primary',
        'Featured Artist',
    ]


def test_artist_image_scan_includes_name_only_side_artists(
    tmp_path,
    monkeypatch,
):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda _path: {
            'name': 'Song',
            'artists': ['Primary', 'No Id Guest'],
        },
    )
    monkeypatch.setattr(
        metadata_repair, 'enrich_song_metadata', lambda song: song
    )
    seen_artists = []

    def fake_missing(_root, _path, artists, **_kwargs):
        seen_artists.extend(artists)
        return [
            {
                'artist': artist['name'],
                'artist_id': artist['id'],
                'file': 'song.mp3',
                'folder': artist['name'],
                'source': 'Album cover fallback',
            }
            for artist in artists
        ]

    monkeypatch.setattr(
        metadata_repair, 'missing_artist_image_items', fake_missing
    )

    result = metadata_repair.scan_artist_images(tmp_path, limit=10)

    assert seen_artists == [
        {'id': '', 'name': 'Primary'},
        {'id': '', 'name': 'No Id Guest'},
    ]
    assert [item['artist_id'] for item in result['items']] == ['', '']


def test_artist_image_scan_checks_tracks_with_same_primary_artist(
    tmp_path,
    monkeypatch,
):
    for title in ['one', 'two']:
        (tmp_path / f'{title}.mp3').write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda path: {
            'name': path.stem,
            'artists': ['Primary'],
        },
    )
    monkeypatch.setattr(
        metadata_repair,
        '_artist_image_scan_candidates',
        lambda root, path, _current=None, **_kwargs: [
            {
                'artist': f'Guest {path.stem}',
                'artist_id': f'guest-{path.stem}',
                'file': path.relative_to(root).as_posix(),
                'folder': f'Guest {path.stem}',
                'source': 'Wikimedia Commons',
            }
        ],
    )

    result = metadata_repair.scan_artist_images(tmp_path, limit=10)

    assert [item['artist'] for item in result['items']] == [
        'Guest one',
        'Guest two',
    ]


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
        lambda root, path, _current=None, **_kwargs: [
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


def test_scan_artist_images_scans_selected_batch(tmp_path, monkeypatch):
    album = tmp_path / 'Artist' / 'Album'
    album.mkdir(parents=True)
    for index in range(5):
        (album / f'song-{index}.mp3').write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        '_song_from_file',
        lambda path: {'name': path.stem, 'artists': [path.stem]},
    )
    monkeypatch.setattr(
        metadata_repair,
        '_artist_image_scan_candidates',
        lambda root, path, _current=None, **_kwargs: [
            {
                'artist': path.stem,
                'artist_id': path.stem,
                'file': path.relative_to(root).as_posix(),
                'folder': 'Artist',
                'source': 'Album cover fallback',
            }
        ],
    )

    first = metadata_repair.scan_artist_images(tmp_path, limit=2)
    second = metadata_repair.scan_artist_images(
        tmp_path,
        limit=2,
        start=first['next_offset'],
    )

    assert first['batch_scanned'] == 2
    assert first['next_offset'] == 2
    assert first['complete'] is False
    assert [item['artist'] for item in first['items']] == ['song-0', 'song-1']
    assert second['start'] == 2
    assert [item['artist'] for item in second['items']] == ['song-2', 'song-3']


def test_repair_artist_image_writes_for_requested_artist(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Artist' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

    saved = {}

    def fake_save(root, path, artists, **_kwargs):
        saved['root'] = root
        saved['path'] = path
        saved['artists'] = artists
        (root / 'Artist' / 'Artist.jpg').write_bytes(b'image')
        return ['Artist/Artist.jpg']

    monkeypatch.setattr(
        metadata_repair, 'save_missing_artist_images', fake_save
    )

    result = metadata_repair.repair_artist_image(
        tmp_path,
        'Artist/Album/song.mp3',
        {'id': 'artist-mbid', 'name': 'Artist'},
    )

    assert saved['root'] == tmp_path.resolve()
    assert saved['path'] == track.resolve()
    assert saved['artists'] == [{'id': 'artist-mbid', 'name': 'Artist'}]
    assert result['saved'] == ['Artist/Artist.jpg']
    assert result['verified'] == ['Artist/Artist.jpg']


def test_repair_artist_image_writes_to_requested_folder(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Compilation' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        'artist_or_fallback_image',
        lambda *_args: (b'image', 'Album cover fallback'),
    )

    result = metadata_repair.repair_artist_image(
        tmp_path,
        'Compilation/Album/song.mp3',
        {'id': '', 'name': 'Jellyfin Artist'},
        target_folder='Local Artist Folder',
    )

    assert result['saved'] == ['Local Artist Folder/Jellyfin Artist.jpg']
    assert result['verified'] == ['Local Artist Folder/Jellyfin Artist.jpg']
    assert (
        tmp_path / 'Local Artist Folder' / 'Jellyfin Artist.jpg'
    ).read_bytes() == b'image'


def test_repair_artist_image_rejects_unsafe_requested_folder(tmp_path):
    track = tmp_path / 'song.mp3'
    track.write_bytes(b'not really audio')

    with pytest.raises(ValueError, match='Invalid artist folder'):
        metadata_repair.repair_artist_image(
            tmp_path,
            'song.mp3',
            {'id': '', 'name': 'Artist'},
            target_folder='../outside',
        )


def test_repair_artist_image_fails_when_image_not_written(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Artist' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'not really audio')

    monkeypatch.setattr(
        metadata_repair,
        'save_missing_artist_images',
        lambda *_args, **_kwargs: ['Artist/Artist.jpg'],
    )

    with pytest.raises(ValueError, match='No artist image source found'):
        metadata_repair.repair_artist_image(
            tmp_path,
            'Artist/Album/song.mp3',
            {'id': 'artist-mbid', 'name': 'Artist'},
        )


def test_repair_artist_image_verifies_only_requested_folder(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Artist' / 'Album'
    album.mkdir(parents=True)
    (album / 'song.mp3').write_bytes(b'not really audio')
    (tmp_path / 'Artist' / 'existing.jpg').write_bytes(b'existing')

    monkeypatch.setattr(
        metadata_repair,
        'artist_or_fallback_image',
        lambda *_args: (None, ''),
    )

    with pytest.raises(ValueError, match='No artist image source found'):
        metadata_repair.repair_artist_image(
            tmp_path,
            'Artist/Album/song.mp3',
            {'id': '', 'name': 'Different Artist'},
            target_folder='Different Artist',
        )


def test_repair_artist_image_uses_custom_image_fetchers(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        metadata_repair,
        'artist_or_fallback_image',
        lambda *_args: (None, ''),
    )

    def fetch(_name: str, _artist: dict[str, str]):
        return b'jellyfin-image', 'Jellyfin'

    result = metadata_repair.repair_artist_image(
        tmp_path,
        '',
        {'id': '', 'name': 'Remote Artist'},
        target_folder='Remote Artist',
        image_fetchers=[fetch],
    )

    assert result['saved'] == ['Remote Artist/Remote Artist.jpg']
    assert (
        tmp_path / 'Remote Artist' / 'Remote Artist.jpg'
    ).read_bytes() == b'jellyfin-image'


def test_repair_artist_image_reuses_existing_named_sidecar(
    tmp_path,
    monkeypatch,
):
    folder = tmp_path / 'Cached Artist'
    folder.mkdir()
    (folder / 'Cached Artist.jpg').write_bytes(b'existing-image')

    def should_not_run(*_args, **_kwargs):
        raise AssertionError('online fetchers should not run for existing art')

    monkeypatch.setattr(
        metadata_repair,
        'artist_or_fallback_image',
        should_not_run,
    )

    result = metadata_repair.repair_artist_image(
        tmp_path,
        '',
        {'id': '', 'name': 'Cached Artist'},
        target_folder='Cached Artist',
        image_fetchers=[should_not_run],
    )

    assert 'Cached Artist/Cached Artist.jpg' in result['saved']
    assert result['verified']


def test_repair_artist_image_bytes_overwrites_existing_named_image(tmp_path):
    folder = tmp_path / 'Cached Artist'
    folder.mkdir()
    existing = folder / 'Cached Artist.jpg'
    existing.write_bytes(b'existing-image')

    result = metadata_repair.repair_artist_image_bytes(
        tmp_path,
        '',
        {'id': '', 'name': 'Cached Artist'},
        b'replacement-image',
        target_folder='Cached Artist',
    )

    assert existing.read_bytes() == b'replacement-image'
    assert 'Cached Artist/Cached Artist.jpg' in result['verified']
    assert result['verified_on_disk'] is True


def test_repair_artist_image_verified_falls_back_to_saved_paths(
    tmp_path,
    monkeypatch,
):
    folder = tmp_path / 'Saved Only'
    folder.mkdir()
    (folder / 'Saved Only.jpg').write_bytes(b'image')

    monkeypatch.setattr(
        metadata_repair,
        '_verified_artist_image_paths',
        lambda *_args, **_kwargs: [],
    )

    result = metadata_repair.repair_artist_image(
        tmp_path,
        '',
        {'id': '', 'name': 'Saved Only'},
        target_folder='Saved Only',
        image_fetchers=[],
    )

    assert result['verified'] == ['Saved Only/Saved Only.jpg']


def test_verify_artist_folder_image_requires_named_artist_file(tmp_path):
    folder = tmp_path / 'Artist'
    folder.mkdir()
    (folder / 'thumb.jpg').write_bytes(b'image')

    check = metadata_repair.verify_artist_folder_image(
        tmp_path,
        {'id': '', 'name': 'Artist'},
        folder,
        saved=['Artist/thumb.jpg'],
        verified=['Artist/thumb.jpg'],
    )

    assert check['verified_on_disk'] is False


def test_finalize_artist_image_repair_result_rejects_missing_named_file(
    tmp_path,
):
    folder = tmp_path / 'Artist'
    folder.mkdir()
    (folder / 'thumb.jpg').write_bytes(b'image')

    with pytest.raises(ValueError, match='not written to the artist folder'):
        metadata_repair._finalize_artist_image_repair_result(
            tmp_path,
            {'id': '', 'name': 'Artist'},
            folder,
            {
                'artist': 'Artist',
                'saved': ['Artist/thumb.jpg'],
                'verified': ['Artist/thumb.jpg'],
            },
        )


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
    monkeypatch.setattr(
        metadata_repair, 'apply_text_tags', lambda *_args: None
    )

    with pytest.raises(ValueError, match='Metadata write did not persist'):
        metadata_repair.repair_file(tmp_path, 'song.mp3')
