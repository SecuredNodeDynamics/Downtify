"""Tests for the settings pipeline: DEFAULT_SETTINGS, _load_settings and
_effective_lyrics_providers."""

from __future__ import annotations

import json

import requests

from downtify.api import (
    DEFAULT_SETTINGS,
    _effective_lyrics_providers,
    _load_settings,
    _normalized_jellyfin_library_name,
    jellyfin_libraries_endpoint,
)


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


def test_jellyfin_libraries_dedupes_by_name(monkeypatch):
    class FakeVirtualFoldersResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return [
                {'ItemId': 'music-view', 'Name': 'Music', 'CollectionType': 'music'},
                {'ItemId': 'music-copy', 'Name': '\ufeff Music\u200b ', 'CollectionType': 'music'},
                {'ItemId': 'misic-copy', 'Name': 'Misic', 'CollectionType': 'music'},
                {'ItemId': 'tv-view', 'Name': 'TV', 'CollectionType': 'tvshows'},
                {'ItemId': 'movie-view', 'Name': 'Movies', 'CollectionType': 'movies'},
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
            },
        ],
    }


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
            },
            {
                'id': 'tv-view',
                'name': 'TV',
                'type': 'VirtualFolder',
                'collection_type': '',
            },
        ],
    }


def test_normalized_jellyfin_library_name_removes_hidden_characters():
    assert _normalized_jellyfin_library_name('\ufeff Music\u200b ') == 'music'
