from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Any

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


def test_metadata_scan_resets_offset_when_download_root_changes(
    tmp_path, monkeypatch
):
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


def test_artist_image_scan_keeps_items_from_previous_batch(
    tmp_path, monkeypatch
):
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
        assert [
            item['file'] for item in api.state.artist_image_scan['clean']
        ] == [
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


def test_apply_artist_image_allows_folder_without_file(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    old_scan = dict(api.state.artist_image_scan)
    old_repair_log = list(api.state.repair_log)
    api.state.downloader = FakeDownloader(tmp_path)
    api.state.artist_image_scan = {**old_scan, 'completed': [], 'items': [], 'matched': 0}

    captured = {}

    def fake_repair(root, file, artist, **_kwargs):
        captured['file'] = file
        captured['artist'] = artist
        return {
            'artist': artist['name'],
            'artist_id': artist['id'],
            'file': '',
            'saved': ['Guest Artist/Guest Artist.jpg'],
            'verified': ['Guest Artist/Guest Artist.jpg'],
        }

    monkeypatch.setattr(
        api.metadata_repair, 'repair_artist_image', fake_repair
    )
    monkeypatch.setattr(
        api,
        '_sync_artist_image_to_jellyfin',
        lambda *_args, **_kwargs: {'synced': False},
    )
    try:
        result = asyncio.run(
            api.apply_artist_image(
                FakeRequest({
                    'artist': 'Guest Artist',
                    'folder': 'Guest Artist',
                })
            )
        )

        assert captured['file'] == ''
        assert captured['artist'] == {
            'id': '',
            'name': 'Guest Artist',
            'jellyfin_artist_id': '',
        }
        assert result['verified'] == ['Guest Artist/Guest Artist.jpg']
    finally:
        api.state.downloader = old_downloader
        api.state.artist_image_scan = old_scan
        api.state.repair_log = old_repair_log


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

    monkeypatch.setattr(
        api.metadata_repair, 'repair_artist_image', fake_repair
    )
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

        assert captured['artist'] == {
            'id': '',
            'name': 'Guest Artist',
            'jellyfin_artist_id': '',
        }
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


def test_apply_metadata_uses_mapped_server_media_location(
    tmp_path, monkeypatch
):
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
            'saved': ['Local Folder/Local Folder.jpg'],
            'verified': ['Local Folder/Local Folder.jpg'],
        }

    monkeypatch.setattr(
        api.metadata_repair, 'repair_artist_image', fake_repair
    )
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
        assert result['verified'] == ['Local Folder/Local Folder.jpg']
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
    assert (
        inventory['folder_files']['artist one'] == 'Artist One/Album/song.mp3'
    )
    assert inventory['tags']['guest artist'] == 'Guest Artist'
    assert inventory['tag_files']['guest artist'] == 'guest.mp3'


def test_local_artist_inventory_uses_folder_audio_when_tags_do_not_match(
    tmp_path,
    monkeypatch,
):
    album = tmp_path / 'Folder Artist' / 'Album'
    album.mkdir(parents=True)
    track = album / 'song.mp3'
    track.write_bytes(b'audio')
    monkeypatch.setattr(
        api.metadata_repair,
        '_song_from_file',
        lambda _path: {'artists': ['Different Tagged Artist']},
    )

    inventory = api._local_artist_inventory(tmp_path)

    assert inventory['folder_files']['folder artist'] == (
        'Folder Artist/Album/song.mp3'
    )


def test_local_artist_inventory_counts_named_artist_jpg(tmp_path):
    artist_dir = tmp_path / 'Named Sidecar'
    artist_dir.mkdir()
    (artist_dir / 'Named Sidecar.jpg').write_bytes(b'image')

    inventory = api._local_artist_inventory(tmp_path)

    assert inventory['folder_images']['named sidecar'] is True


def test_jellyfin_reconcile_detects_existing_folder_by_jellyfin_name(tmp_path):
    artist_dir = tmp_path / 'Jellyfin Match'
    artist_dir.mkdir()
    (artist_dir / 'Jellyfin Match.jpg').write_bytes(b'image')

    payload = api._build_jellyfin_reconcile_payload(
        {'name': 'Music'},
        {'jellyfin match': 'Jellyfin Match'},
        {
            'folders': {},
            'folder_images': {},
            'folder_files': {},
            'tags': {},
            'tag_files': {},
        },
        root=tmp_path,
    )

    assert payload['counts']['missing_local_images'] == 0
    assert payload['missing_images'] == []


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
    assert (
        '/api/metadata/artist-images/candidate-preview?'
        in by_name['Guest Artist']['preview_url']
    )


def test_named_items_include_jellyfin_candidate_preview():
    result = api._named_items(
        {'jane murdoch': 'Jane Murdoch'},
        propose_folder_from_name=True,
        jellyfin_ids={'jane murdoch': 'jf-artist-id'},
    )

    item = result[0]
    assert item['jellyfin_artist_id'] == 'jf-artist-id'
    assert 'jellyfin-preview' in item['preview_url']
    assert 'jellyfin_artist_id=jf-artist-id' in item['preview_url']


def test_artist_image_options_list_returns_source_previews(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    api.state.downloader = FakeDownloader(tmp_path)
    monkeypatch.setattr(
        api.artist_image_options,
        'collect_artist_image_options',
        lambda *_args, **_kwargs: [
            {
                'id': 'spotify:abc',
                'source': 'Spotify',
                'label': 'Jane Murdoch',
                'subtitle': '95% name match',
                'image_url': 'https://i.scdn.co/image/abc.jpg',
                'jellyfin_artist_id': '',
            }
        ],
    )
    try:
        payload = api.artist_image_options_list(
            artist='Jane Murdoch',
            folder='Jane Murdoch',
        )
    finally:
        api.state.downloader = old_downloader

    assert payload['artist'] == 'Jane Murdoch'
    assert payload['options'][0]['preview_url'].startswith(
        '/api/metadata/artist-images/remote-preview?'
    )


def test_remote_preview_rejects_untrusted_host(tmp_path):
    old_downloader = api.state.downloader
    api.state.downloader = FakeDownloader(tmp_path)
    try:
        import pytest
        from fastapi import HTTPException

        with pytest.raises(HTTPException, match='not allowed'):
            api.artist_remote_image_preview(
                url='https://evil.example.test/image.jpg',
            )
    finally:
        api.state.downloader = old_downloader


def test_apply_artist_image_accepts_selected_image_url(
    tmp_path,
    monkeypatch,
):
    old_downloader = api.state.downloader
    old_scan = dict(api.state.artist_image_scan)
    old_repair_log = list(api.state.repair_log)
    api.state.downloader = FakeDownloader(tmp_path)
    api.state.artist_image_scan = {**old_scan, 'completed': [], 'items': [], 'matched': 0}

    captured = {}

    def fake_repair_bytes(root, file, artist, image, **kwargs):
        captured['image'] = image
        folder = tmp_path / 'Guest Artist'
        folder.mkdir(exist_ok=True)
        target = folder / 'Guest Artist.jpg'
        target.write_bytes(image)
        return {
            'artist': artist['name'],
            'artist_id': artist['id'],
            'file': file,
            'saved': ['Guest Artist/Guest Artist.jpg'],
            'verified': ['Guest Artist/Guest Artist.jpg'],
            'verified_on_disk': True,
            'folder': 'Guest Artist',
        }

    monkeypatch.setattr(
        api.metadata_repair,
        'repair_artist_image_bytes',
        fake_repair_bytes,
    )
    monkeypatch.setattr(
        api,
        '_resolve_manual_artist_image_bytes',
        lambda *_args, **_kwargs: (b'selected-image', 'Selected image'),
    )
    monkeypatch.setattr(
        api,
        '_sync_artist_image_to_jellyfin',
        lambda *_args, **_kwargs: {'synced': False},
    )
    try:
        result = asyncio.run(
            api.apply_artist_image(
                FakeRequest({
                    'artist': 'Guest Artist',
                    'folder': 'Guest Artist',
                    'image_url': 'https://i.scdn.co/image/abc.jpg',
                    'selected_option_id': 'spotify:abc',
                })
            )
        )
    finally:
        api.state.downloader = old_downloader
        api.state.artist_image_scan = old_scan
        api.state.repair_log = old_repair_log

    assert captured['image'] == b'selected-image'
    assert result['saved'] == ['Guest Artist/Guest Artist.jpg']


def test_candidate_preview_uses_jellyfin_image(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    api.state.downloader = FakeDownloader(tmp_path)
    image = b'\x89PNG\r\n\x1a\nimage'

    monkeypatch.setattr(
        api,
        '_fetch_jellyfin_artist_image_bytes',
        lambda *_args, **_kwargs: image,
    )

    try:
        response = api.artist_candidate_image_preview(
            artist='Jane Murdoch',
            jellyfin_artist_id='jf-artist-id',
        )
    finally:
        api.state.downloader = old_downloader

    assert response.body == image
    assert response.media_type == 'image/png'


def test_clean_artist_image_items_include_existing_art_preview():
    result = api._with_clean_artist_image_preview([
        {
            'file': 'Artist/Album/song.mp3',
            'artist': 'Artist',
            'folder': 'Artist',
        },
        {'file': 'loose-song.mp3', 'artist': 'Loose Artist', 'folder': ''},
    ])

    assert result[0]['preview_url'].endswith('folder=Artist')
    assert '/api/metadata/artist-images/preview?' in result[1]['preview_url']


def test_sync_artist_image_to_jellyfin_posts_base64(monkeypatch):
    image = b'\x89PNG\r\n\x1a\nimage'
    captured: dict[str, Any] = {}

    class FakeResponse:
        @staticmethod
        def raise_for_status():
            return None

    def fake_post(url, headers=None, params=None, data=None, timeout=0):
        captured['url'] = url
        captured['headers'] = headers
        captured['params'] = params
        captured['data'] = data
        return FakeResponse()

    monkeypatch.setattr(
        api,
        '_configured_jellyfin',
        lambda: ('http://jellyfin.test', {'X-Emby-Token': 'secret'}),
    )
    monkeypatch.setattr(
        api,
        '_jellyfin_artist_id_for_name',
        lambda *_args, **_kwargs: 'artist-id',
    )
    monkeypatch.setattr(api.requests, 'post', fake_post)

    result = api._sync_artist_image_to_jellyfin('Nas', image)

    assert result == {'synced': True, 'artist_id': 'artist-id'}
    assert captured['url'] == 'http://jellyfin.test/Items/artist-id/Images/Primary'
    assert captured['headers']['Content-Type'] == 'image/png'
    assert captured['data'] == base64.b64encode(image)
    assert captured['params'] == {'Replace': 'true'}


def test_resolve_artist_image_repair_paths_uses_local_inventory(tmp_path, monkeypatch):
    root = tmp_path / 'downloads'
    artist_dir = root / 'Nas'
    artist_dir.mkdir(parents=True)
    track = artist_dir / 'song.mp3'
    track.write_bytes(b'audio')

    monkeypatch.setattr(api, '_active_download_dir', lambda: root)

    file, folder = api._resolve_artist_image_repair_paths(
        root,
        'Nas',
        '',
        '',
    )

    assert file == 'Nas/song.mp3'
    assert folder == 'Nas'


def test_fetch_jellyfin_artist_image_bytes_downloads_primary(monkeypatch):
    captured: dict[str, Any] = {}

    class FakeResponse:
        status_code = 200
        content = b'\xff\xd8\xffimage'
        headers = {'content-type': 'image/jpeg'}

        @staticmethod
        def raise_for_status():
            return None

    def fake_get(url, headers=None, params=None, timeout=0):
        captured['url'] = url
        captured['params'] = params
        return FakeResponse()

    monkeypatch.setattr(
        api,
        '_configured_jellyfin',
        lambda: ('http://jellyfin.test', {'X-Emby-Token': 'secret'}),
    )
    monkeypatch.setattr(
        api,
        '_jellyfin_artist_id_for_name',
        lambda *_args, **_kwargs: 'artist-id',
    )
    monkeypatch.setattr(api.requests, 'get', fake_get)

    image = api._fetch_jellyfin_artist_image_bytes('Nas')

    assert image == b'\xff\xd8\xffimage'
    assert captured['url'] == 'http://jellyfin.test/Items/artist-id/Images/Primary'
    assert captured['params'] == {'MaxWidth': 2000}
