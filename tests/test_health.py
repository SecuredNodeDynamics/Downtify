from __future__ import annotations

from downtify import api
from downtify.api import _command_version, _directory_summary, get_health
from downtify.downloader import Downloader


def test_directory_summary_counts_audio_files(tmp_path):
    (tmp_path / 'song.mp3').write_text('audio', encoding='utf-8')
    (tmp_path / 'notes.txt').write_text('notes', encoding='utf-8')

    summary = _directory_summary(tmp_path)

    assert summary['exists'] is True
    assert summary['file_count'] == 2
    assert summary['audio_count'] == 1
    assert summary['external_path'] is None
    assert summary['size_bytes'] > 0
    assert summary['disk']['total_bytes'] > 0


def test_directory_summary_includes_external_media_location(
    tmp_path,
):
    summary = _directory_summary(
        tmp_path,
        external_path='/mnt/media/Music',
    )

    assert summary['external_path'] == '/mnt/media/Music'


def test_health_payload_includes_configured_media_location(
    tmp_path,
    monkeypatch,
):
    old_downloader = api.state.downloader
    old_settings_path = api.state.settings_path
    old_version = api.state.version
    old_settings = api.state.settings
    old_jobs = api.state.download_jobs
    old_history = api.state.history_db
    try:
        monkeypatch.setenv(
            'DOWNTIFY_MEDIA_SAVE_LOCATION',
            '/mnt/media/Music',
        )
        api.state.downloader = Downloader(tmp_path / 'downloads')
        api.state.settings_path = tmp_path / 'data' / 'settings.json'
        api.state.settings_path.parent.mkdir()
        api.state.version = '1.2.3'
        api.state.settings = {}
        api.state.download_jobs = {}
        api.state.history_db = None

        payload = get_health()
    finally:
        api.state.downloader = old_downloader
        api.state.settings_path = old_settings_path
        api.state.version = old_version
        api.state.settings = old_settings
        api.state.download_jobs = old_jobs
        api.state.history_db = old_history

    assert payload['downloads']['external_path'] == '/mnt/media/Music'
    assert payload['data']['external_path'] is None


def test_command_version_reports_missing_command():
    result = _command_version(
        'definitely-not-a-real-downtify-command',
        ['--version'],
    )

    assert result == {'available': False, 'path': None, 'version': None}


def test_health_payload_contains_core_sections(tmp_path):
    old_downloader = api.state.downloader
    old_settings_path = api.state.settings_path
    old_version = api.state.version
    old_settings = api.state.settings
    old_jobs = api.state.download_jobs
    old_history = api.state.history_db
    try:
        api.state.downloader = Downloader(tmp_path / 'downloads')
        api.state.settings_path = tmp_path / 'data' / 'settings.json'
        api.state.settings_path.parent.mkdir()
        api.state.version = '1.2.3'
        api.state.settings = {'format': 'mp3', 'max_parallel_downloads': 3}
        api.state.download_jobs = {'a': {'status': 'done'}}
        api.state.history_db = None

        payload = get_health()
    finally:
        api.state.downloader = old_downloader
        api.state.settings_path = old_settings_path
        api.state.version = old_version
        api.state.settings = old_settings
        api.state.download_jobs = old_jobs
        api.state.history_db = old_history

    assert payload['version'] == '1.2.3'
    assert payload['downloads']['exists'] is True
    assert payload['queue']['total'] == 1
    assert 'ffmpeg' in payload['tools']
    assert 'yt_dlp' in payload['tools']
