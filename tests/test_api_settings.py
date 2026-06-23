"""Tests for the settings pipeline: DEFAULT_SETTINGS, _load_settings and
_effective_lyrics_providers."""

from __future__ import annotations

import asyncio
import json
import time

import requests

from downtify import api
from downtify.api import (
    DEFAULT_SETTINGS,
    _apply_download_dir_from_settings,
    _clean_version,
    _download_playlist_subdir,
    _effective_download_dir,
    _effective_lyrics_providers,
    _is_newer_version,
    _load_settings,
    _normalized_jellyfin_library_name,
    _start_docker_self_update,
    check_update,
    jellyfin_libraries_endpoint,
    update_settings_endpoint,
)
from downtify.downloader import Downloader


class FakeRequest:
    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        return self.payload


def test_default_settings_has_required_keys():
    required = {
        'audio_providers',
        'lyrics_providers',
        'download_lyrics',
        'format',
        'bitrate',
        'output',
        'generate_m3u',
        'enhance_metadata',
        'organize_by_artist',
        'organize_by_album',
        'server_media_location',
        'jellyfin_url',
        'jellyfin_api_key',
        'jellyfin_music_library',
        'enable_jellyfin_tools',
        'artist_folder_policy',
    }
    assert required <= set(DEFAULT_SETTINGS)


def test_default_organize_by_artist_is_false():
    assert DEFAULT_SETTINGS['organize_by_artist'] is False


def test_default_organize_by_album_is_false():
    assert DEFAULT_SETTINGS['organize_by_album'] is False


def test_default_generate_m3u_is_true():
    assert DEFAULT_SETTINGS['generate_m3u'] is True


def test_default_download_lyrics_is_true():
    assert DEFAULT_SETTINGS['download_lyrics'] is True


def test_default_enhance_metadata_is_true():
    assert DEFAULT_SETTINGS['enhance_metadata'] is True


def test_default_artist_folder_policy_creates_available_artwork_folders():
    assert DEFAULT_SETTINGS['artist_folder_policy'] == 'artwork_available'


def test_default_jellyfin_tools_are_enabled():
    assert DEFAULT_SETTINGS['enable_jellyfin_tools'] is True


def test_default_format_is_mp3():
    assert DEFAULT_SETTINGS['format'] == 'mp3'


# ── _load_settings ────────────────────────────────────────────────────────────


def test_load_settings_returns_defaults_for_missing_file(tmp_path):
    result = _load_settings(tmp_path / 'nonexistent.json')
    assert result == DEFAULT_SETTINGS


def test_load_settings_merges_saved_settings(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(
        json.dumps({'format': 'flac', 'bitrate': '128'}), encoding='utf-8'
    )
    result = _load_settings(path)
    assert result['format'] == 'flac'
    assert result['bitrate'] == '128'
    assert result['generate_m3u'] == DEFAULT_SETTINGS['generate_m3u']


def test_load_settings_ignores_unknown_keys(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(
        json.dumps({'format': 'mp3', 'unknown_key': 'value'}), encoding='utf-8'
    )
    result = _load_settings(path)
    assert 'unknown_key' not in result


def test_load_settings_handles_invalid_json(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text('not valid json {{ }}', encoding='utf-8')
    result = _load_settings(path)
    assert result == DEFAULT_SETTINGS


def test_load_settings_handles_non_dict_json(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps([1, 2, 3]), encoding='utf-8')
    result = _load_settings(path)
    assert result == DEFAULT_SETTINGS


def test_load_settings_preserves_organize_by_artist(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(json.dumps({'organize_by_artist': True}), encoding='utf-8')
    result = _load_settings(path)
    assert result['organize_by_artist'] is True


def test_load_settings_preserves_organize_by_album(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text(
        json.dumps({'organize_by_artist': True, 'organize_by_album': True}),
        encoding='utf-8',
    )
    result = _load_settings(path)
    assert result['organize_by_artist'] is True
    assert result['organize_by_album'] is True


def test_effective_download_dir_prefers_saved_server_media_location(tmp_path):
    old_settings = api.state.settings
    try:
        media = tmp_path / 'media'
        api.state.settings = {'server_media_location': str(media)}

        assert _effective_download_dir(tmp_path / 'downloads') == media
    finally:
        api.state.settings = old_settings


def test_effective_download_dir_prefers_saved_path_even_when_env_matches(
    tmp_path,
    monkeypatch,
):
    old_settings = api.state.settings
    old_default = api.state.default_download_dir
    try:
        media = tmp_path / 'media'
        downloads = tmp_path / 'downloads'
        media.mkdir()
        monkeypatch.setenv('DOWNTIFY_MEDIA_SAVE_LOCATION', str(media))
        api.state.settings = {'server_media_location': str(media)}
        api.state.default_download_dir = downloads

        assert _effective_download_dir(tmp_path / 'fallback') == media
    finally:
        api.state.settings = old_settings
        api.state.default_download_dir = old_default


def test_effective_download_dir_maps_env_host_path_to_container_mount(
    tmp_path,
    monkeypatch,
):
    old_settings = api.state.settings
    old_default = api.state.default_download_dir
    try:
        host_media = tmp_path / 'host' / 'Music'
        container_media = tmp_path / 'container' / 'downloads'
        monkeypatch.setenv('DOWNTIFY_MEDIA_SAVE_LOCATION', str(host_media))
        api.state.settings = {'server_media_location': str(host_media)}
        api.state.default_download_dir = container_media

        assert _effective_download_dir() == container_media
    finally:
        api.state.settings = old_settings
        api.state.default_download_dir = old_default


def test_effective_download_dir_maps_nested_env_host_path_to_container_mount(
    tmp_path,
    monkeypatch,
):
    old_settings = api.state.settings
    old_default = api.state.default_download_dir
    try:
        host_media = tmp_path / 'host' / 'Music'
        container_media = tmp_path / 'container' / 'downloads'
        monkeypatch.setenv('DOWNTIFY_MEDIA_SAVE_LOCATION', str(host_media))
        api.state.settings = {
            'server_media_location': str(host_media / 'Playlists')
        }
        api.state.default_download_dir = container_media

        assert _effective_download_dir() == container_media / 'Playlists'
    finally:
        api.state.settings = old_settings
        api.state.default_download_dir = old_default


def test_apply_download_dir_from_settings_updates_downloader(tmp_path):
    old_settings = api.state.settings
    old_downloader = api.state.downloader
    old_default = api.state.default_download_dir
    try:
        media = tmp_path / 'media'
        api.state.settings = {'server_media_location': str(media)}
        api.state.default_download_dir = tmp_path / 'downloads'
        api.state.downloader = Downloader(tmp_path / 'downloads')

        result = _apply_download_dir_from_settings()

        assert result == media
        assert api.state.downloader.download_dir == media
        assert media.exists()
    finally:
        api.state.settings = old_settings
        api.state.downloader = old_downloader
        api.state.default_download_dir = old_default


def test_apply_download_dir_from_settings_does_not_compound_mapped_host_path(
    tmp_path,
    monkeypatch,
):
    old_settings = api.state.settings
    old_downloader = api.state.downloader
    old_default = api.state.default_download_dir
    try:
        host_media = tmp_path / 'media' / 'Music'
        container_media = tmp_path / 'container' / 'downloads'
        monkeypatch.setenv('DOWNTIFY_MEDIA_SAVE_LOCATION', str(host_media))
        api.state.settings = {
            'server_media_location': str(host_media / 'test') + '/'
        }
        api.state.default_download_dir = container_media
        api.state.downloader = Downloader(container_media)

        first = _apply_download_dir_from_settings()
        second = _apply_download_dir_from_settings()

        assert first == container_media / 'test'
        assert second == container_media / 'test'
        assert api.state.downloader.download_dir == container_media / 'test'
    finally:
        api.state.settings = old_settings
        api.state.downloader = old_downloader
        api.state.default_download_dir = old_default


def test_download_playlist_subdir_skips_active_root_name(tmp_path):
    old_settings = api.state.settings
    old_downloader = api.state.downloader
    old_default = api.state.default_download_dir
    try:
        download_root = tmp_path / 'downloads' / 'test'
        api.state.settings = {}
        api.state.default_download_dir = download_root
        api.state.downloader = Downloader(download_root)

        assert _download_playlist_subdir('test') is None
        assert _download_playlist_subdir('My Playlist') == 'My Playlist'
    finally:
        api.state.settings = old_settings
        api.state.downloader = old_downloader
        api.state.default_download_dir = old_default


def test_update_settings_server_media_location_retargets_downloader(tmp_path):
    old_settings = api.state.settings
    old_downloader = api.state.downloader
    old_settings_path = api.state.settings_path
    old_default = api.state.default_download_dir
    try:
        media = tmp_path / 'media'
        api.state.settings = dict(DEFAULT_SETTINGS)
        api.state.default_download_dir = tmp_path / 'downloads'
        api.state.downloader = Downloader(tmp_path / 'downloads')
        api.state.settings_path = None

        asyncio.run(
            update_settings_endpoint(
                FakeRequest({'server_media_location': str(media)})
            )
        )

        assert api.state.settings['server_media_location'] == str(media)
        assert api.state.downloader.download_dir == media
        assert media.exists()
    finally:
        api.state.settings = old_settings
        api.state.downloader = old_downloader
        api.state.settings_path = old_settings_path
        api.state.default_download_dir = old_default


def test_clean_version_accepts_v_prefixed_semver():
    assert _clean_version('v2.10.1') == '2.10.1'


def test_clean_version_rejects_invalid_values():
    assert _clean_version('latest') is None


def test_is_newer_version_compares_semver():
    assert _is_newer_version('2.10.0', '2.9.9') is True
    assert _is_newer_version('2.9.0', '2.9.0') is False


def test_latest_version_from_release_redirect(monkeypatch):
    class FakeResponse:
        status_code = 302
        headers = {
            'Location': (
                'https://github.com/SecuredNodeDynamics/Downtify/releases/tag/v2.10.46'
            ),
        }

    monkeypatch.setattr(
        'downtify.api.requests.get',
        lambda *_args, **_kwargs: FakeResponse(),
    )

    result = api._latest_version_from_release_redirect()

    assert result['latest_version'] == '2.10.46'
    assert result['source'] == 'redirect'


def test_latest_github_version_falls_back_to_release_redirect(monkeypatch, tmp_path):
    api._UPDATE_CACHE.clear()
    api._UPDATE_CACHE_AT = 0.0

    def fail_api(*_args, **_kwargs):
        return {}

    def redirect_ok(*_args, **kwargs):
        if kwargs.get('allow_redirects') is False:
            class FakeResponse:
                status_code = 302
                headers = {
                    'Location': (
                        'https://github.com/SecuredNodeDynamics/Downtify/'
                        'releases/tag/v2.10.46'
                    ),
                }

            return FakeResponse()
        raise requests.exceptions.HTTPError('rate limit')

    monkeypatch.setattr(api, '_latest_release_from_github_api', fail_api)
    monkeypatch.setattr(api, '_latest_tag_from_github_api', fail_api)
    monkeypatch.setattr('downtify.api.requests.get', redirect_ok)
    monkeypatch.setattr(
        api,
        '_update_cache_path',
        lambda: tmp_path / 'update_check_cache.json',
    )

    result = api._latest_github_version()

    assert result['latest_version'] == '2.10.46'
    assert result['source'] == 'redirect'


def test_load_update_cache_from_disk_respects_ttl(monkeypatch, tmp_path):
    cache_path = tmp_path / 'update_check_cache.json'
    monkeypatch.setattr(api, '_update_cache_path', lambda: cache_path)
    cache_path.write_text(
        json.dumps(
            {
                'latest_version': '2.10.47',
                'cached_at': time.time() - api._UPDATE_CACHE_TTL_SECONDS - 1,
            }
        ),
        encoding='utf-8',
    )

    assert api._load_update_cache_from_disk() == {}


def test_latest_github_version_refresh_bypasses_disk_cache(monkeypatch, tmp_path):
    api._UPDATE_CACHE.clear()
    api._UPDATE_CACHE_AT = 0.0
    cache_path = tmp_path / 'update_check_cache.json'
    cache_path.write_text(
        json.dumps({'latest_version': '2.10.47', 'cached_at': time.time()}),
        encoding='utf-8',
    )
    monkeypatch.setattr(api, '_update_cache_path', lambda: cache_path)
    monkeypatch.setattr(
        api,
        '_latest_release_from_github_api',
        lambda *_args, **_kwargs: {
            'latest_version': '2.10.49',
            'release_url': 'https://github.com/example/release',
            'source': 'release',
            'name': 'v2.10.49',
            'published_at': None,
            'error': '',
        },
    )

    cached = api._latest_github_version()
    refreshed = api._latest_github_version(refresh=True)

    assert cached['latest_version'] == '2.10.47'
    assert refreshed['latest_version'] == '2.10.49'


def test_check_update_refresh_forces_github_lookup(monkeypatch):
    calls = {'count': 0}

    def fake_latest(*_args, refresh=False, **_kwargs):
        calls['count'] += 1
        if refresh:
            return {'latest_version': '2.10.49', 'release_url': '', 'source': 'release'}
        return {'latest_version': '2.10.47', 'release_url': '', 'source': 'release'}

    monkeypatch.setattr(api, '_latest_github_version', fake_latest)

    check_update()
    result = check_update(refresh=True)

    assert calls['count'] == 2
    assert result['latest_version'] == '2.10.49'


def test_check_update_reports_available_update(monkeypatch):
    old_version = api.state.version
    try:
        api.state.version = '2.9.0'
        monkeypatch.setattr(
            api,
            '_latest_github_version',
            lambda: {
                'latest_version': '2.10.0',
                'release_url': 'https://github.com/example/release',
                'source': 'release',
                'name': 'v2.10.0',
                'published_at': None,
                'error': '',
            },
        )

        result = check_update()

        assert result['current_version'] == '2.9.0'
        assert result['latest_version'] == '2.10.0'
        assert result['update_available'] is True
    finally:
        api.state.version = old_version


def test_docker_self_update_reports_missing_capabilities(monkeypatch):
    monkeypatch.setattr(api.shutil, 'which', lambda _name: None)
    monkeypatch.setattr(api.Path, 'exists', lambda _self: False)

    result = _start_docker_self_update()

    assert result['success'] is False
    assert result['requires_manual'] is True
    assert result['commands'][0].startswith('docker pull ')
    assert 'docker run --rm' in result['commands'][1]


def test_docker_self_update_pulls_image_and_starts_watchtower_helper(
    monkeypatch,
):
    captured = {'commands': []}

    class FakeResult:
        def __init__(self, stdout=''):
            self.stdout = stdout

        returncode = 0
        stderr = ''

    def fake_run(command, **_kwargs):
        captured['commands'].append(command)
        if command[1:3] == ['inspect', '--format']:
            return FakeResult('ghcr.io/securednodedynamics/downtify:latest\n')
        if command[1] == 'pull':
            return FakeResult(
                'latest: Pulling from securednodedynamics/downtify\n'
            )
        return FakeResult('helper-container-id\n')

    monkeypatch.setattr(api.shutil, 'which', lambda _name: '/usr/bin/docker')
    monkeypatch.setattr(api.Path, 'exists', lambda _self: True)
    monkeypatch.setenv('DOWNTIFY_SELF_UPDATE_CONTAINER', 'downtify')
    monkeypatch.setattr(api, '_run_docker_command', fake_run)

    result = _start_docker_self_update()

    assert result['success'] is True
    assert result['updated'] is True
    assert result['requires_restart'] is False
    assert result['requires_manual'] is False
    assert result['restart_scheduled'] is True
    assert result['helper_container'] == 'helper-container-id'
    assert (
        result['target_image'] == 'ghcr.io/securednodedynamics/downtify:latest'
    )
    assert (
        'container restart/recreate is scheduled' in result['terminal_output']
    )
    assert captured['commands'][0] == [
        '/usr/bin/docker',
        'inspect',
        '--format',
        '{{.Config.Image}}',
        'downtify',
    ]
    assert captured['commands'][1] == [
        '/usr/bin/docker',
        'pull',
        'ghcr.io/securednodedynamics/downtify:latest',
    ]
    assert captured['commands'][2][:4] == [
        '/usr/bin/docker',
        'run',
        '-d',
        '--name',
    ]
    assert 'containrrr/watchtower:latest' in captured['commands'][2]
    assert 'DOCKER_API_VERSION=1.44' in captured['commands'][2]
    assert '--include-restarting' in captured['commands'][2]
    assert captured['commands'][2][-1] == 'downtify'


def test_docker_self_update_fails_when_image_pull_fails(monkeypatch):
    class FakeResult:
        stderr = ''

        def __init__(self, returncode=0, stdout=''):
            self.returncode = returncode
            self.stdout = stdout

    def fake_run(command, **_kwargs):
        if command[1:3] == ['inspect', '--format']:
            return FakeResult(
                stdout='ghcr.io/securednodedynamics/downtify:latest\n'
            )
        if command[1] == 'pull':
            return FakeResult(returncode=1, stdout='manifest unknown\n')
        return FakeResult(stdout='helper-container-id\n')

    monkeypatch.setattr(api.shutil, 'which', lambda _name: '/usr/bin/docker')
    monkeypatch.setattr(api.Path, 'exists', lambda _self: True)
    monkeypatch.setenv('DOWNTIFY_SELF_UPDATE_CONTAINER', 'downtify')
    monkeypatch.setattr(api, '_run_docker_command', fake_run)

    result = _start_docker_self_update()

    assert result['success'] is False
    assert result['updated'] is False
    assert result['requires_manual'] is True
    assert (
        result['message'] == 'Could not pull the latest Downtify Docker image.'
    )
    assert result['pull_output'] == 'manifest unknown'


def test_docker_self_update_rejects_version_pinned_container(monkeypatch):
    class FakeResult:
        returncode = 0
        stderr = ''

        def __init__(self, stdout=''):
            self.stdout = stdout

    monkeypatch.setattr(api.shutil, 'which', lambda _name: '/usr/bin/docker')
    monkeypatch.setattr(api.Path, 'exists', lambda _self: True)
    monkeypatch.setattr(
        api,
        '_run_docker_command',
        lambda *_args, **_kwargs: FakeResult(
            'ghcr.io/securednodedynamics/downtify:2.10.11\n'
        ),
    )

    result = _start_docker_self_update()

    assert result['success'] is False
    assert result['requires_manual'] is True
    assert 'pinned to' in result['message']
    assert (
        'docker compose up -d --force-recreate downtify' in result['commands']
    )


def test_load_settings_empty_object_returns_defaults(tmp_path):
    path = tmp_path / 'settings.json'
    path.write_text('{}', encoding='utf-8')
    result = _load_settings(path)
    assert result == DEFAULT_SETTINGS


# ── _effective_lyrics_providers ───────────────────────────────────────────────


def test_effective_providers_when_enabled():
    settings = {'download_lyrics': True, 'lyrics_providers': ['lrclib']}
    assert _effective_lyrics_providers(settings) == ['lrclib']


def test_effective_providers_when_disabled():
    settings = {'download_lyrics': False, 'lyrics_providers': ['lrclib']}
    assert _effective_lyrics_providers(settings) == []


def test_effective_providers_filters_empty_strings():
    settings = {
        'download_lyrics': True,
        'lyrics_providers': ['lrclib', '', 'genius'],
    }
    result = _effective_lyrics_providers(settings)
    assert '' not in result
    assert 'lrclib' in result


def test_effective_providers_filters_none_entries():
    settings = {
        'download_lyrics': True,
        'lyrics_providers': ['lrclib', None],
    }
    result = _effective_lyrics_providers(settings)
    assert None not in result


def test_effective_providers_defaults_to_enabled_when_key_missing():
    settings = {'lyrics_providers': ['lrclib']}
    assert _effective_lyrics_providers(settings) == ['lrclib']


def test_effective_providers_empty_list_when_no_providers():
    settings = {'download_lyrics': True, 'lyrics_providers': []}
    assert _effective_lyrics_providers(settings) == []


# ── Jellyfin libraries ────────────────────────────────────────────────────────


def test_jellyfin_libraries_returns_music_libraries_only(monkeypatch):
    class FakeVirtualFoldersResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {
                    'ItemId': 'music-view',
                    'Name': 'Music',
                    'CollectionType': 'music',
                },
                {
                    'ItemId': 'music-copy',
                    'Name': '\ufeff Music\u200b ',
                    'CollectionType': 'music',
                },
                {
                    'ItemId': 'music-playlists-view',
                    'Name': 'Music Playlists',
                    'CollectionType': 'music',
                },
                {
                    'ItemId': 'tv-view',
                    'Name': 'TV',
                    'CollectionType': 'tvshows',
                },
                {
                    'ItemId': 'movie-view',
                    'Name': 'Movies',
                    'CollectionType': 'movies',
                },
            ]

    def fake_get(url, headers=None, params=None, timeout=None):
        assert url == 'http://jellyfin.test/Library/VirtualFolders'
        assert headers == {
            'X-Emby-Token': 'secret',
            'X-MediaBrowser-Token': 'secret',
        }
        assert params is None
        assert timeout == 10
        return FakeVirtualFoldersResponse()

    monkeypatch.setattr('downtify.api.requests.get', fake_get)

    result = jellyfin_libraries_endpoint('jellyfin.test', 'secret')

    assert result == {
        'success': True,
        'source': 'virtual_folders',
        'libraries': [
            {
                'id': 'music-view',
                'name': 'Music',
                'type': 'VirtualFolder',
                'collection_type': 'music',
                'locations': [],
            },
        ],
    }


def test_jellyfin_libraries_excludes_music_playlists_view(monkeypatch):
    class FakeVirtualFoldersResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {
                    'ItemId': 'music-view',
                    'Name': 'Music',
                    'CollectionType': 'music',
                    'Locations': ['/media/music'],
                },
                {
                    'ItemId': 'music-playlists-view',
                    'Name': 'Music Playlists',
                    'CollectionType': 'music',
                    'Locations': [],
                },
            ]

    monkeypatch.setattr(
        'downtify.api.requests.get',
        lambda *args, **kwargs: FakeVirtualFoldersResponse(),
    )

    result = jellyfin_libraries_endpoint('jellyfin.test', 'secret')

    assert [library['name'] for library in result['libraries']] == ['Music']


def test_jellyfin_libraries_falls_back_to_items(monkeypatch):
    class FakeVirtualFoldersResponse:
        status_code = 403

        def raise_for_status(self):
            error = requests.exceptions.HTTPError('forbidden')
            error.response = self
            raise error

        def json(self):
            return {}

    class FakeItemsResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'Items': [
                    {
                        'Id': 'music-view',
                        'Name': 'Music',
                        'Type': 'Folder',
                        'IsFolder': True,
                        'CollectionType': 'music',
                    },
                    {
                        'Id': 'music-folder',
                        'Name': 'Music',
                        'Type': 'Folder',
                        'IsFolder': True,
                        'CollectionType': 'music',
                    },
                    {
                        'Id': 'tv-view',
                        'Name': 'TV',
                        'Type': 'Folder',
                        'IsFolder': True,
                        'CollectionType': 'tvshows',
                    },
                ]
            }

    urls = []

    def fake_get(url, headers=None, params=None, timeout=None):
        urls.append(url)
        if url.endswith('/Library/VirtualFolders'):
            assert params is None
            return FakeVirtualFoldersResponse()
        assert url == 'http://jellyfin.test/Items'
        assert params == {'Recursive': False}
        return FakeItemsResponse()

    monkeypatch.setattr('downtify.api.requests.get', fake_get)

    result = jellyfin_libraries_endpoint('jellyfin.test', 'secret')

    assert urls == [
        'http://jellyfin.test/Library/VirtualFolders',
        'http://jellyfin.test/Items',
    ]
    assert result == {
        'success': True,
        'source': 'items',
        'libraries': [
            {
                'id': 'music-view',
                'name': 'Music',
                'type': 'Folder',
                'collection_type': 'music',
                'locations': [],
            },
        ],
    }


def test_jellyfin_libraries_keeps_untyped_virtual_folders(monkeypatch):
    class FakeVirtualFoldersResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {'ItemId': 'music-view', 'Name': 'Music'},
                {'ItemId': 'tv-view', 'Name': 'TV'},
            ]

    monkeypatch.setattr(
        'downtify.api.requests.get',
        lambda *args, **kwargs: FakeVirtualFoldersResponse(),
    )

    result = jellyfin_libraries_endpoint('jellyfin.test', 'secret')

    assert result == {
        'success': True,
        'source': 'virtual_folders',
        'libraries': [
            {
                'id': 'music-view',
                'name': 'Music',
                'type': 'VirtualFolder',
                'collection_type': '',
                'locations': [],
            },
            {
                'id': 'tv-view',
                'name': 'TV',
                'type': 'VirtualFolder',
                'collection_type': '',
                'locations': [],
            },
        ],
    }


def test_normalized_jellyfin_library_name_removes_hidden_characters():
    assert _normalized_jellyfin_library_name('\ufeff Music\u200b ') == 'music'
