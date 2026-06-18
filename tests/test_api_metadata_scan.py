from __future__ import annotations

import asyncio
from pathlib import Path

from downtify import api
from downtify.api import artist_folder_image_preview


class FakeDownloader:
    def __init__(self, download_dir: Path):
        self.download_dir = download_dir


class FakeRequest:
    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        return self.payload


def test_metadata_scan_keeps_items_from_previous_batch(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    old_scan = dict(api.state.metadata_scan)
    api.state.downloader = FakeDownloader(tmp_path)
    api.state.metadata_scan = {
        **old_scan,
        'items': [{'file': 'A/one.mp3'}],
        'clean': [{'file': 'A/clean.mp3'}],
        'next_offset': 1,
    }

    def fake_scan_library(_root, _limit, _start, progress_cb):
        result = {
            'scanned': 2,
            'batch_scanned': 1,
            'total': 2,
            'matched': 1,
            'items': [{'file': 'B/two.mp3'}],
            'clean': [{'file': 'B/clean.mp3'}],
            'errors': [],
            'next_offset': 2,
            'complete': True,
        }
        progress_cb(result)
        return result

    monkeypatch.setattr(api.metadata_repair, 'scan_library', fake_scan_library)
    try:
        asyncio.run(api._run_metadata_scan(1, 1))
        assert [item['file'] for item in api.state.metadata_scan['items']] == [
            'A/one.mp3',
            'B/two.mp3',
        ]
        assert [item['file'] for item in api.state.metadata_scan['clean']] == [
            'A/clean.mp3',
            'B/clean.mp3',
        ]
        assert api.state.metadata_scan['matched'] == 2
    finally:
        api.state.downloader = old_downloader
        api.state.metadata_scan = old_scan


def test_metadata_scan_resets_offset_when_download_root_changes(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    old_scan = dict(api.state.metadata_scan)
    old_settings = api.state.settings
    old_default = api.state.default_download_dir
    old_task = api.state.metadata_scan_task
    new_root = tmp_path / 'new-media'
    api.state.downloader = FakeDownloader(tmp_path / 'old-media')
    api.state.settings = {'server_media_location': str(new_root)}
    api.state.default_download_dir = tmp_path / 'fallback'
    api.state.metadata_scan_task = None
    api.state.metadata_scan = {
        **old_scan,
        'root': str((tmp_path / 'old-media').resolve()),
        'next_offset': 50,
        'total': 100,
        'items': [{'file': 'old.mp3'}],
        'clean': [{'file': 'old-clean.mp3'}],
    }

    captured = {}

    def fake_create_task(coro):
        captured['coro'] = coro
        return None

    monkeypatch.setattr(asyncio, 'create_task', fake_create_task)
    try:
        result = asyncio.run(
            api.start_metadata_scan(FakeRequest({'limit': 25}))
        )

        assert result['next_offset'] == 0
        assert result['items'] == []
        assert result['clean'] == []
        assert result['root'] == str(new_root.resolve())
        assert api.state.downloader.download_dir == new_root
    finally:
        if captured.get('coro') is not None:
            captured['coro'].close()
        api.state.downloader = old_downloader
        api.state.metadata_scan = old_scan
        api.state.settings = old_settings
        api.state.default_download_dir = old_default
        api.state.metadata_scan_task = old_task


def test_artist_image_scan_keeps_items_from_previous_batch(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    old_scan = dict(api.state.artist_image_scan)
    api.state.downloader = FakeDownloader(tmp_path)
    api.state.artist_image_scan = {
        **old_scan,
        'items': [
            {
                'artist_id': 'artist-one',
                'artist': 'Artist One',
                'folder': 'Artist One',
                'file': 'Artist One/song.mp3',
            }
        ],
        'clean': [{'file': 'Artist One/clean.mp3'}],
        'next_offset': 1,
    }

    def fake_scan_artist_images(
        _root,
        _limit,
        _start,
        progress_cb,
        _artist_folder_policy='artwork_available',
    ):
        result = {
            'scanned': 2,
            'batch_scanned': 1,
            'total': 2,
            'matched': 1,
            'items': [
                {
                    'artist_id': 'artist-two',
                    'artist': 'Artist Two',
                    'folder': 'Artist Two',
                    'file': 'Artist Two/song.mp3',
                }
            ],
            'clean': [{'file': 'Artist Two/clean.mp3'}],
            'next_offset': 2,
            'complete': True,
        }
        progress_cb(result)
        return result

    monkeypatch.setattr(
        api.metadata_repair,
        'scan_artist_images',
        fake_scan_artist_images,
    )
    try:
        asyncio.run(api._run_artist_image_scan(1, 1))
        assert [
            item['artist_id'] for item in api.state.artist_image_scan['items']
        ] == ['artist-one', 'artist-two']
        assert [item['file'] for item in api.state.artist_image_scan['clean']] == [
            'Artist One/clean.mp3',
            'Artist Two/clean.mp3',
        ]
        assert api.state.artist_image_scan['matched'] == 2
    finally:
        api.state.downloader = old_downloader
        api.state.artist_image_scan = old_scan


def test_artist_image_scan_resets_offset_when_download_root_changes(
    tmp_path,
    monkeypatch,
):
    old_downloader = api.state.downloader
    old_scan = dict(api.state.artist_image_scan)
    old_settings = api.state.settings
    old_default = api.state.default_download_dir
    old_task = api.state.artist_image_scan_task
    new_root = tmp_path / 'new-media'
    api.state.downloader = FakeDownloader(tmp_path / 'old-media')
    api.state.settings = {'server_media_location': str(new_root)}
    api.state.default_download_dir = tmp_path / 'fallback'
    api.state.artist_image_scan_task = None
    api.state.artist_image_scan = {
        **old_scan,
        'root': str((tmp_path / 'old-media').resolve()),
        'next_offset': 50,
        'total': 100,
        'items': [{'artist': 'Old', 'artist_id': '', 'folder': 'Old'}],
        'clean': [{'file': 'old-clean.mp3'}],
    }

    captured = {}

    def fake_create_task(coro):
        captured['coro'] = coro
        return None

    monkeypatch.setattr(asyncio, 'create_task', fake_create_task)
    try:
        result = asyncio.run(
            api.scan_artist_images(FakeRequest({'limit': 25}))
        )

        assert result['next_offset'] == 0
        assert result['items'] == []
        assert result['clean'] == []
        assert result['root'] == str(new_root.resolve())
        assert api.state.downloader.download_dir == new_root
    finally:
        if captured.get('coro') is not None:
            captured['coro'].close()
        api.state.downloader = old_downloader
        api.state.artist_image_scan = old_scan
        api.state.settings = old_settings
        api.state.default_download_dir = old_default
        api.state.artist_image_scan_task = old_task


def test_apply_artist_image_allows_name_only_artist(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    old_scan = dict(api.state.artist_image_scan)
    old_repair_log = list(api.state.repair_log)
    api.state.downloader = FakeDownloader(tmp_path)
    api.state.artist_image_scan = {
        **old_scan,
        'completed': [],
        'items': [
            {
                'artist': 'Guest Artist',
                'artist_id': '',
                'folder': 'Guest Artist',
                'file': 'song.mp3',
            }
        ],
        'matched': 1,
    }

    captured = {}

    def fake_repair(root, file, artist, **_kwargs):
        captured['root'] = root
        captured['file'] = file
        captured['artist'] = artist
        return {
            'artist': artist['name'],
            'artist_id': artist['id'],
            'file': file,
            'saved': ['Guest Artist/Guest Artist.jpg'],
        }

    monkeypatch.setattr(api.metadata_repair, 'repair_artist_image', fake_repair)
    try:
        result = asyncio.run(
            api.apply_artist_image(
                FakeRequest({
                    'file': 'song.mp3',
                    'artist': 'Guest Artist',
                    'artist_id': '',
                })
            )
        )

        assert captured['artist'] == {'id': '', 'name': 'Guest Artist'}
        assert result['saved'] == ['Guest Artist/Guest Artist.jpg']
        assert api.state.artist_image_scan['completed'][0] == result
        assert api.state.artist_image_scan['items'] == []
        assert api.state.artist_image_scan['matched'] == 0
        assert api.state.repair_log[0]['kind'] == 'artist_image'
        assert api.state.repair_log[0]['status'] == 'success'
    finally:
        api.state.downloader = old_downloader
        api.state.artist_image_scan = old_scan
        api.state.repair_log = old_repair_log


def test_apply_metadata_uses_mapped_server_media_location(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    old_settings = api.state.settings
    old_default = api.state.default_download_dir
    old_scan = dict(api.state.metadata_scan)
    old_repair_log = list(api.state.repair_log)
    host_media = tmp_path / 'host' / 'Music'
    container_media = tmp_path / 'container' / 'downloads'
    api.state.downloader = FakeDownloader(container_media)
    api.state.default_download_dir = container_media
    api.state.settings = {'server_media_location': str(host_media)}
    api.state.metadata_scan = {**old_scan, 'completed': [], 'items': []}

    captured = {}

    def fake_repair(root, file, **_kwargs):
        captured['root'] = root
        captured['file'] = file
        return {
            'file': file,
            'current': {},
            'candidate': {},
            'matched': True,
            'changes': [],
        }

    monkeypatch.setenv('DOWNTIFY_MEDIA_SAVE_LOCATION', str(host_media))
    monkeypatch.setattr(api.metadata_repair, 'repair_file', fake_repair)
    try:
        asyncio.run(api.apply_metadata(FakeRequest({'file': 'song.mp3'})))

        assert captured == {
            'root': container_media,
            'file': 'song.mp3',
        }
    finally:
        api.state.downloader = old_downloader
        api.state.settings = old_settings
        api.state.default_download_dir = old_default
        api.state.metadata_scan = old_scan
        api.state.repair_log = old_repair_log


def test_apply_artist_image_passes_requested_folder(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    old_scan = dict(api.state.artist_image_scan)
    old_repair_log = list(api.state.repair_log)
    api.state.downloader = FakeDownloader(tmp_path)
    api.state.artist_image_scan = {
        **old_scan,
        'completed': [],
        'items': [],
        'matched': 0,
    }

    captured = {}

    def fake_repair(root, file, artist, **kwargs):
        captured['root'] = root
        captured['file'] = file
        captured['artist'] = artist
        captured['target_folder'] = kwargs.get('target_folder')
        return {
            'artist': artist['name'],
            'artist_id': artist['id'],
            'file': file,
            'saved': ['Local Folder/Jellyfin Artist.jpg'],
            'verified': ['Local Folder/Jellyfin Artist.jpg'],
        }

    monkeypatch.setattr(api.metadata_repair, 'repair_artist_image', fake_repair)
    try:
        result = asyncio.run(
            api.apply_artist_image(
                FakeRequest({
                    'file': 'song.mp3',
                    'artist': 'Jellyfin Artist',
                    'artist_id': '',
                    'folder': 'Local Folder',
                })
            )
        )

        assert captured['target_folder'] == 'Local Folder'
        assert result['verified'] == ['Local Folder/Jellyfin Artist.jpg']
    finally:
        api.state.downloader = old_downloader
        api.state.artist_image_scan = old_scan
        api.state.repair_log = old_repair_log


def test_artist_folder_image_preview_serves_local_artist_art(tmp_path):
    old_downloader = api.state.downloader
    old_settings = api.state.settings
    old_default = api.state.default_download_dir
    try:
        artist_dir = tmp_path / 'Artist One'
        artist_dir.mkdir()
        image = b'\xff\xd8\xff\xe0image'
        (artist_dir / 'Artist One.jpg').write_bytes(image)
        api.state.downloader = FakeDownloader(tmp_path)
        api.state.settings = {'server_media_location': str(tmp_path)}
        api.state.default_download_dir = tmp_path

        response = artist_folder_image_preview('Artist One')

        assert response.body == image
        assert response.media_type == 'image/jpeg'
    finally:
        api.state.downloader = old_downloader
        api.state.settings = old_settings
        api.state.default_download_dir = old_default


def test_local_artist_inventory_tracks_folder_images_and_tag_files(
    tmp_path,
    monkeypatch,
):
    artist_dir = tmp_path / 'Artist One'
    album_dir = artist_dir / 'Album'
    album_dir.mkdir(parents=True)
    track = album_dir / 'song.mp3'
    track.write_bytes(b'audio')
    (artist_dir / 'Artist One.jpg').write_bytes(b'image')

    guest_track = tmp_path / 'guest.mp3'
    guest_track.write_bytes(b'audio')

    def fake_song(path):
        if path == track:
            return {'artists': ['Artist One']}
        return {'artists': ['Guest Artist']}

    monkeypatch.setattr(api.metadata_repair, '_song_from_file', fake_song)

    inventory = api._local_artist_inventory(tmp_path)

    assert inventory['folders']['artist one'] == 'Artist One'
    assert inventory['folder_images']['artist one'] is True
    assert inventory['tags']['guest artist'] == 'Guest Artist'
    assert inventory['tag_files']['guest artist'] == 'guest.mp3'


def test_named_items_include_image_state_and_repair_file():
    result = api._named_items(
        {'artist one': 'Artist One', 'guest artist': 'Guest Artist'},
        folders={'artist one': 'Artist One'},
        folder_images={'artist one': True},
        files={
            'artist one': 'Artist One/Album/song.mp3',
            'guest artist': 'guest.mp3',
        },
    )

    by_name = {item['name']: item for item in result}

    assert by_name['Artist One']['has_image'] is True
    assert by_name['Artist One']['missing_image'] is False
    assert by_name['Artist One']['preview_url'].endswith('folder=Artist%20One')
    assert by_name['Artist One']['file'] == 'Artist One/Album/song.mp3'
    assert by_name['Guest Artist']['has_image'] is False
    assert by_name['Guest Artist']['missing_image'] is True
    assert by_name['Guest Artist']['file'] == 'guest.mp3'
