from __future__ import annotations

from downtify import api
from downtify.api import (
    _command_version,
    _directory_summary,
    _download_directory_summary,
    _mount_source_for,
    get_health,
)
from downtify.downloader import Downloader
from downtify.history import DownloadHistoryDB


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


def test_mount_source_detects_download_bind_source(tmp_path):
    downloads = tmp_path / 'downloads'
    downloads.mkdir()
    escaped_downloads = str(downloads).replace(' ', '\\040')
    mountinfo = tmp_path / 'mountinfo'
    mountinfo.write_text(
        f'1 2 8:1 /mnt/media/Music {escaped_downloads} rw,relatime - ext4 /dev/sda1 rw\n',
        encoding='utf-8',
    )

    assert _mount_source_for(downloads, mountinfo) == '/mnt/media/Music'


def test_mount_source_ignores_root_mounts(tmp_path):
    downloads = tmp_path / 'downloads'
    downloads.mkdir()
    mountinfo = tmp_path / 'mountinfo'
    mountinfo.write_text(
        f'1 2 8:1 / {downloads} rw,relatime - ext4 /dev/sda1 rw\n',
        encoding='utf-8',
    )

    assert _mount_source_for(downloads, mountinfo) is None


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


def test_health_payload_prefers_saved_server_media_location(
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
            '/env/location',
        )
        api.state.downloader = Downloader(tmp_path / 'downloads')
        api.state.settings_path = tmp_path / 'data' / 'settings.json'
        api.state.settings_path.parent.mkdir()
        api.state.version = '1.2.3'
        media = tmp_path / 'media' / 'Music'
        api.state.settings = {'server_media_location': str(media)}
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

    assert payload['downloads']['external_path'] == str(media)


def test_health_retargets_downloader_to_saved_server_media_location(tmp_path):
    old_downloader = api.state.downloader
    old_settings_path = api.state.settings_path
    old_version = api.state.version
    old_settings = api.state.settings
    old_jobs = api.state.download_jobs
    old_history = api.state.history_db
    old_default = api.state.default_download_dir
    media = tmp_path / 'media' / 'Music'
    try:
        api.state.downloader = Downloader(tmp_path / 'downloads')
        api.state.default_download_dir = tmp_path / 'downloads'
        api.state.settings_path = tmp_path / 'data' / 'settings.json'
        api.state.settings_path.parent.mkdir()
        api.state.version = '1.2.3'
        api.state.settings = {'server_media_location': str(media)}
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
        api.state.default_download_dir = old_default

    assert api.state.downloader is old_downloader
    assert payload['downloads']['path'] == str(media)
    assert payload['downloads']['container_path'] == str(media)
    assert payload['downloads']['external_path'] == str(media)
    assert media.exists()


def test_download_summary_measures_existing_external_path(tmp_path):
    media = tmp_path / 'media'
    media.mkdir()
    (media / 'song.flac').write_text('audio', encoding='utf-8')

    old_settings = api.state.settings
    try:
        api.state.settings = {'server_media_location': str(media)}

        summary = _download_directory_summary(media)
    finally:
        api.state.settings = old_settings

    assert summary['external_path'] == str(media)
    assert summary['container_path'] == str(media)
    assert summary['storage_path'] == str(media)
    assert summary['storage_path_matches_display'] is True
    assert summary['audio_count'] == 1


def test_health_counts_container_mount_when_saved_location_is_compose_host_path(
    tmp_path,
    monkeypatch,
):
    old_downloader = api.state.downloader
    old_settings_path = api.state.settings_path
    old_version = api.state.version
    old_settings = api.state.settings
    old_jobs = api.state.download_jobs
    old_history = api.state.history_db
    old_default = api.state.default_download_dir
    downloads = tmp_path / 'downloads'
    media = tmp_path / 'media' / 'Music'
    try:
        downloads.mkdir()
        (downloads / 'song.flac').write_text('audio', encoding='utf-8')
        monkeypatch.setenv('DOWNTIFY_MEDIA_SAVE_LOCATION', str(media))
        api.state.downloader = Downloader(downloads)
        api.state.default_download_dir = downloads
        api.state.settings_path = tmp_path / 'data' / 'settings.json'
        api.state.settings_path.parent.mkdir()
        api.state.version = '1.2.3'
        api.state.settings = {'server_media_location': str(media)}
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
        api.state.default_download_dir = old_default

    assert payload['downloads']['external_path'] == str(media)
    assert payload['downloads']['container_path'] == str(downloads)
    assert payload['downloads']['storage_path'] == str(downloads)
    assert payload['downloads']['storage_path_matches_display'] is False
    assert payload['downloads']['audio_count'] == 1


def test_download_summary_marks_unmounted_external_path(tmp_path):
    downloads = tmp_path / 'downloads'
    downloads.mkdir()
    (downloads / 'song.mp3').write_text('audio', encoding='utf-8')
    missing_media = tmp_path / 'missing-media'

    old_settings = api.state.settings
    try:
        api.state.settings = {'server_media_location': str(missing_media)}

        summary = _download_directory_summary(downloads)
    finally:
        api.state.settings = old_settings

    assert summary['external_path'] == str(missing_media)
    assert summary['container_path'] == str(downloads)
    assert summary['storage_path'] == str(downloads)
    assert summary['storage_path_matches_display'] is False
    assert summary['audio_count'] == 1


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
        api.state.download_jobs = {
            'a': {'status': 'done'},
            'b': {'status': 'queued'},
        }
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
    assert payload['queue']['all_total'] == 2
    assert 'ffmpeg' in payload['tools']
    assert 'yt_dlp' in payload['tools']


def test_health_payload_counts_completed_last_24h(tmp_path):
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
        api.state.settings = {}
        api.state.download_jobs = {}
        api.state.history_db = DownloadHistoryDB(tmp_path / 'history.db')
        history_id = api.state.history_db.create(
            {'name': 'Done'},
            status='downloading',
        )
        api.state.history_db.mark_done(history_id, 'Done.mp3')

        payload = get_health()
    finally:
        api.state.downloader = old_downloader
        api.state.settings_path = old_settings_path
        api.state.version = old_version
        api.state.settings = old_settings
        api.state.download_jobs = old_jobs
        api.state.history_db = old_history

    assert payload['history']['completed_24h'] == 1
