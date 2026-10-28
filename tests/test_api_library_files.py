from __future__ import annotations

from mutagen.id3 import ID3, TIT2, TPE1

from downtify import api
from downtify.api import get_library_files, get_library_stats, get_summary


def test_get_library_files_returns_artists_list(tmp_path, monkeypatch):
    download_dir = tmp_path / 'downloads'
    album_dir = download_dir / 'Connor Price' / 'Swing'
    album_dir.mkdir(parents=True)
    path = album_dir / '01 - Swing.mp3'
    path.write_bytes(b'audio')
    tags = ID3()
    tags.add(TIT2(encoding=3, text='Swing'))
    tags.add(TPE1(encoding=3, text='Connor Price, Nic D'))
    tags.save(path)

    api.state.default_download_dir = download_dir
    api.state.downloader = None
    api.state.library_files_cache = {
        'root': '',
        'items': [],
        'built_at': 0.0,
        'building': False,
    }

    items = get_library_files()

    assert len(items) == 1
    assert items[0]['artist'] == 'Connor Price'
    assert items[0]['artists'] == ['Connor Price', 'Nic D']


def test_manual_library_refresh_bypasses_stale_file_cache(tmp_path, monkeypatch):
    download_dir = tmp_path / 'downloads'
    download_dir.mkdir()
    old_cache = api.state.library_files_cache
    old_dirty = api.state.library_files_dirty
    old_default_download_dir = api.state.default_download_dir
    old_stats_cache = api.state.library_stats_cache
    old_health_cache = api.state.health_cache
    calls = []

    def fast_scan(root):
        calls.append(root)
        return [{'file': 'Server Artist/track.mp3'}]

    monkeypatch.setattr(api, 'list_library_files_fast', fast_scan)
    try:
        api.state.default_download_dir = download_dir
        api.state.library_files_cache = {
            'root': str(download_dir.resolve()),
            'items': [{'file': 'stale.mp3'}],
            'built_at': 1.0,
            'building': False,
        }
        api.state.library_files_dirty = False
        api.state.library_stats_cache = {'root': 'old', 'stats': {}, 'built_at': 1.0}
        api.state.health_cache = {'payload': {}, 'built_at': 1.0, 'key': 'old'}

        items = get_library_files(refresh=True)
    finally:
        api.state.library_files_cache = old_cache
        api.state.library_files_dirty = old_dirty
        api.state.default_download_dir = old_default_download_dir
        api.state.library_stats_cache = old_stats_cache
        api.state.health_cache = old_health_cache

    assert items == [{'file': 'Server Artist/track.mp3'}]
    assert calls == [download_dir]


def test_library_stats_and_summary_are_lightweight(tmp_path):
    download_dir = tmp_path / 'downloads'
    album_dir = download_dir / 'Connor Price' / 'Swing'
    album_dir.mkdir(parents=True)
    path = album_dir / '01 - Swing.mp3'
    path.write_bytes(b'audio')
    tags = ID3()
    tags.add(TIT2(encoding=3, text='Swing'))
    tags.add(TPE1(encoding=3, text='Connor Price, Nic D'))
    tags.save(path)

    old_state = {
        'default_download_dir': api.state.default_download_dir,
        'downloader': api.state.downloader,
        'settings_path': api.state.settings_path,
        'version': api.state.version,
        'settings': api.state.settings,
        'download_jobs': api.state.download_jobs,
        'history_db': api.state.history_db,
        'library_files_cache': api.state.library_files_cache,
        'library_stats_cache': api.state.library_stats_cache,
        'health_cache': api.state.health_cache,
    }
    try:
        api.state.default_download_dir = download_dir
        api.state.downloader = None
        api.state.settings_path = tmp_path / 'data' / 'settings.json'
        api.state.settings_path.parent.mkdir()
        api.state.version = '1.2.3'
        api.state.settings = {}
        api.state.download_jobs = {}
        api.state.history_db = None
        api.state.library_files_cache = {
            'root': '',
            'items': [],
            'built_at': 0.0,
            'building': False,
        }
        api.state.library_stats_cache = {
            'root': '',
            'stats': None,
            'built_at': 0.0,
        }
        api.state.health_cache = {
            'payload': None,
            'built_at': 0.0,
            'key': None,
        }

        stats = get_library_stats()
        summary = get_summary()
    finally:
        for name, value in old_state.items():
            setattr(api.state, name, value)

    assert stats == {
        'tracks': 1,
        'artists': 2,
        'albums': 1,
        'genres': 0,
    }
    assert summary['counts']['library'] == stats
        # Health no longer blocks on a recursive filesystem walk before the
        # asynchronous library cache has been populated.
        assert summary['storage']['downloads']['audio_count'] == 0
    assert summary['tools']['ffmpeg']['available'] in {True, False}
