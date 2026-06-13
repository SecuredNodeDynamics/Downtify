"""Tests for YouTube Music provider helpers."""

from __future__ import annotations

import pytest

from downtify import providers
from downtify.providers import (
    enrich_from_match,
    youtube_music_track_index_for_match,
)


@pytest.fixture(autouse=True)
def clear_ytm_album_cache():
    """Isolate tests that manipulate the in-memory get_album cache."""

    providers._album_track_cache.clear()
    providers._album_browse_search_cache.clear()
    yield
    providers._album_track_cache.clear()
    providers._album_browse_search_cache.clear()


def test_enrich_from_match_backfills_artists_when_empty():
    song = {
        'name': 'Test Song',
        'artists': [],
        'source': 'spotify',
        'song_id': 'spotifyTrack1',
    }
    match = {
        'videoId': 'yt123',
        'title': 'Test Song',
        'artists': [{'name': 'AliasFromYT'}],
        'thumbnails': [{'url': 'https://example.com/t.jpg'}],
        'duration_seconds': 180,
    }
    out = enrich_from_match(song, match)
    assert out['artists'] == ['AliasFromYT']
    assert out['artist'] == 'AliasFromYT'


def test_enrich_from_match_does_not_replace_existing_artists():
    song = {
        'name': 'Test Song',
        'artists': ['KeepMe'],
        'source': 'spotify',
    }
    match = {
        'videoId': 'yt123',
        'title': 'Test Song',
        'artists': [{'name': 'Other'}],
    }
    out = enrich_from_match(song, match)
    assert out['artists'] == ['KeepMe']


def test_enrich_from_match_sets_track_index_from_album(monkeypatch):
    def fake_cached(browse_id: str):
        assert browse_id == 'MPREb_test'
        return (
            [
                {'videoId': 'aaaaaaaaaaa', 'trackNumber': 1},
                {'videoId': 'bbbbbbbbbbb', 'trackNumber': 2},
            ],
            12,
        )

    monkeypatch.setattr(
        providers, '_cached_album_tracks_and_count', fake_cached
    )
    match = {
        'videoId': 'bbbbbbbbbbb',
        'title': 'B-side',
        'album': {'name': 'Test LP', 'id': 'MPREb_test'},
    }
    out = enrich_from_match({'name': 'B-side', 'source': 'spotify'}, match)
    assert out['track_number'] == 2
    assert out['album_track_total'] == 12


def test_youtube_music_track_number_zero_falls_back_to_list_position(
    monkeypatch,
):
    monkeypatch.setattr(
        providers,
        '_cached_album_tracks_and_count',
        lambda _browse_id: (
            [{'videoId': 'ccccccccccc', 'trackNumber': 0}],
            None,
        ),
    )
    n, total = youtube_music_track_index_for_match(
        {'videoId': 'ccccccccccc', 'album': {'name': '', 'id': 'x'}},
        None,
    )
    assert n == 1
    assert total == 1


def test_youtube_music_no_album_id_returns_no_track(monkeypatch):
    monkeypatch.setattr(
        providers, '_album_browse_id_from_search', lambda *_: ''
    )
    assert youtube_music_track_index_for_match(
        {'videoId': 'solo', 'album': {'name': 'Loose singles only'}},
        None,
    ) == (None, None)


def test_enrich_preserves_preset_track_number(monkeypatch):
    def fake_cached(_browse_id: str):
        return ([{'videoId': 'vin', 'trackNumber': 2}], 9)

    monkeypatch.setattr(
        providers, '_cached_album_tracks_and_count', fake_cached
    )
    monkeypatch.setattr(
        providers, '_album_browse_id', lambda *_args, **_kw: 'any'
    )
    out = enrich_from_match(
        {'track_number': 7, 'album_track_total': 11},
        {'videoId': 'vin', 'album': {'id': 'mbid'}},
    )
    assert out['track_number'] == 7
    assert out['album_track_total'] == 11


def test_search_songs_falls_back_to_broad_search(monkeypatch):
    class FakeYTMusic:
        def search(self, query, filter=None, limit=20):
            if filter == 'songs':
                return []
            assert filter is None
            return [
                {
                    'videoId': 'abc12345678',
                    'title': 'Fallback Song',
                    'artists': [{'name': 'Fallback Artist'}],
                    'duration_seconds': 123,
                }
            ]

    monkeypatch.setattr(providers, '_ytm', lambda: FakeYTMusic())

    results = providers.search_songs('fallback song', limit=1)

    assert results[0]['song_id'] == 'abc12345678'
    assert results[0]['name'] == 'Fallback Song'


def test_search_media_derives_albums_from_song_hits(monkeypatch):
    class FakeYTMusic:
        def search(self, query, filter=None, limit=20):
            if filter == 'albums':
                return []
            if filter == 'songs':
                return [
                    {
                        'videoId': 'abc12345678',
                        'title': 'Track One',
                        'artists': [{'name': 'Artist'}],
                        'album': {'name': 'Album One', 'id': 'MPREb_album'},
                        'thumbnails': [{'url': 'https://img=w60-h60'}],
                    },
                    {
                        'videoId': 'def12345678',
                        'title': 'Track Two',
                        'artists': [{'name': 'Artist'}],
                        'album': {'name': 'Album One', 'id': 'MPREb_album'},
                    },
                ]
            return []

    monkeypatch.setattr(providers, '_ytm', lambda: FakeYTMusic())

    results = providers.search_media('artist album', limit=5)

    derived = [r for r in results if r.get('media_type') == 'album']
    assert derived[0]['name'] == 'Album One'
    assert derived[0]['browse_id'] == 'MPREb_album'
    assert [r['media_type'] for r in results].count('album') == 1


def test_search_media_ranks_exact_track_before_unrelated_album(monkeypatch):
    class FakeYTMusic:
        def search(self, query, filter=None, limit=20):
            if filter == 'songs':
                return [
                    {
                        'videoId': 'perfect12345',
                        'title': 'Perfect',
                        'artists': [{'name': 'Ed Sheeran'}],
                        'album': {'name': 'Divide', 'id': 'album_divide'},
                    }
                ]
            if filter == 'albums':
                return [
                    {
                        'browseId': 'album_ed',
                        'title': 'Loose Album Match',
                        'artists': [{'name': 'Different Artist'}],
                    }
                ]
            return []

    monkeypatch.setattr(providers, '_ytm', lambda: FakeYTMusic())

    results = providers.search_media('Perfect Ed Sheeran', limit=10)

    assert results[0]['media_type'] == 'track'
    assert results[0]['name'] == 'Perfect'


def test_search_media_can_return_more_than_old_six_pages(monkeypatch):
    class FakeYTMusic:
        def search(self, query, filter=None, limit=20):
            if filter == 'songs':
                return [
                    {
                        'videoId': f'video{i:08d}',
                        'title': f'Artist Song {i}',
                        'artists': [{'name': 'Artist'}],
                    }
                    for i in range(limit)
                ]
            if filter == 'albums':
                return []
            return []

    monkeypatch.setattr(providers, '_ytm', lambda: FakeYTMusic())

    results = providers.search_media('Artist', limit=80)

    assert len(results) == 80
