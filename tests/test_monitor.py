"""Tests for playlist/artist monitor database helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from downtify import api
from downtify.downloader import Downloader
from downtify.monitor import PlaylistMonitorDB, check_monitored


def test_monitor_db_stores_kind(tmp_path: Path) -> None:
    db = PlaylistMonitorDB(tmp_path / 'monitor.db')
    playlist = db.add_playlist(
        'pl123',
        'Test Playlist',
        'https://open.spotify.com/playlist/pl123',
        interval_minutes=30,
        kind='playlist',
    )
    artist = db.add_playlist(
        'ar456',
        'Test Artist',
        'https://open.spotify.com/artist/ar456',
        interval_minutes=60,
        kind='artist',
    )

    assert playlist.kind == 'playlist'
    assert artist.kind == 'artist'

    listed = db.list_playlists()
    assert {item.spotify_id: item.kind for item in listed} == {
        'pl123': 'playlist',
        'ar456': 'artist',
    }

    assert db.get_by_spotify_id('pl123', 'playlist') is not None
    assert db.get_by_spotify_id('pl123', 'artist') is None
    assert db.get_by_spotify_id('ar456', 'artist') is not None


def test_monitor_db_stores_image_url(tmp_path: Path) -> None:
    db = PlaylistMonitorDB(tmp_path / 'monitor.db')
    playlist = db.add_playlist(
        'pl999',
        'Cover Test',
        'https://open.spotify.com/playlist/pl999',
        image_url='https://example.test/cover.jpg',
    )

    assert playlist.image_url == 'https://example.test/cover.jpg'
    assert db.list_playlists()[0].to_dict()['image_url'] == (
        'https://example.test/cover.jpg'
    )


@pytest.mark.asyncio
async def test_list_monitor_playlists_does_not_block_on_spotify_images(
    tmp_path: Path,
) -> None:
    old_monitor_db = api.state.monitor_db
    old_cache = dict(api._MONITOR_IMAGE_CACHE)
    try:
        db = PlaylistMonitorDB(tmp_path / 'monitor.db')
        db.add_playlist(
            'pl123',
            'Test Playlist',
            'https://open.spotify.com/playlist/pl123',
            interval_minutes=30,
            kind='playlist',
        )
        api.state.monitor_db = db
        api._MONITOR_IMAGE_CACHE.clear()

        with patch(
            'downtify.api.spotify.embed_image_url',
            side_effect=AssertionError('list should not fetch Spotify covers'),
        ):
            payload = await api.list_monitor_playlists()

        assert len(payload) == 1
        assert payload[0]['name'] == 'Test Playlist'
        assert payload[0]['kind'] == 'playlist'
        assert payload[0]['image_url'] == ''
    finally:
        api.state.monitor_db = old_monitor_db
        api._MONITOR_IMAGE_CACHE.clear()
        api._MONITOR_IMAGE_CACHE.update(old_cache)


@pytest.mark.asyncio
async def test_list_monitor_playlists_uses_cached_image_without_spotify_fetch(
    tmp_path: Path,
) -> None:
    old_monitor_db = api.state.monitor_db
    old_cache = dict(api._MONITOR_IMAGE_CACHE)
    try:
        db = PlaylistMonitorDB(tmp_path / 'monitor.db')
        db.add_playlist(
            'ar123',
            'Test Artist',
            'https://open.spotify.com/artist/ar123',
            interval_minutes=30,
            kind='artist',
        )
        api.state.monitor_db = db
        api._MONITOR_IMAGE_CACHE.clear()
        api._MONITOR_IMAGE_CACHE['artist:ar123'] = (
            'https://example.test/artist.jpg'
        )

        with patch(
            'downtify.api.spotify.embed_image_url',
            side_effect=AssertionError('list should not fetch Spotify covers'),
        ):
            payload = await api.list_monitor_playlists()

        assert len(payload) == 1
        assert payload[0]['name'] == 'Test Artist'
        assert payload[0]['kind'] == 'artist'
        assert payload[0]['image_url'] == 'https://example.test/artist.jpg'
    finally:
        api.state.monitor_db = old_monitor_db
        api._MONITOR_IMAGE_CACHE.clear()
        api._MONITOR_IMAGE_CACHE.update(old_cache)


@pytest.mark.asyncio
async def test_check_monitored_adopts_existing_file_instead_of_redownloading(
    tmp_path: Path,
) -> None:
    """A monitored track already on disk must not be re-downloaded.

    Reproduces the APK bug where adding an already-downloaded artist to the
    monitor caused every track to be re-fetched (and repeatedly fail) on each
    check because the monitor only consulted its own bookkeeping.
    """

    db = PlaylistMonitorDB(tmp_path / 'monitor.db')
    artist = db.add_playlist(
        'ar456',
        'Test Artist',
        'https://open.spotify.com/artist/ar456',
        kind='artist',
    )

    downloader = Downloader(tmp_path / 'downloads', audio_format='m4a')
    song = {'song_id': 'trk1', 'name': 'Song', 'artists': ['Test Artist']}

    # Simulate a manual download: the file exists on disk but the monitor has
    # never recorded it.
    expected = downloader.existing_filename_for(song)
    assert expected is None
    basename = downloader._format_basename(song)
    (downloader.download_dir / f'{basename}.m4a').write_bytes(b'audio')

    loop = pytest.importorskip('asyncio').get_running_loop()

    with (
        patch(
            'downtify.monitor._fetch_monitored_tracks',
            new=AsyncMock(return_value=[song]),
        ),
        patch.object(
            downloader,
            'download',
            side_effect=AssertionError('existing track must not re-download'),
        ),
    ):
        downloaded = await check_monitored(
            artist,
            db,
            downloader,
            broadcast=AsyncMock(),
            loop=loop,
        )

    assert downloaded == 0
    known = db.get_track_filenames(artist.id)
    assert known.get('trk1') == f'{basename}.m4a'


@pytest.mark.asyncio
async def test_check_monitored_does_not_repeat_terminal_download_failure(
    tmp_path: Path,
) -> None:
    db = PlaylistMonitorDB(tmp_path / 'monitor.db')
    artist = db.add_playlist(
        'ar789',
        'Test Artist',
        'https://open.spotify.com/artist/ar789',
        kind='artist',
    )
    downloader = Downloader(tmp_path / 'downloads', audio_format='m4a')
    song = {'song_id': 'trk-fail', 'name': 'Missing', 'artists': ['Artist']}
    loop = pytest.importorskip('asyncio').get_running_loop()

    with (
        patch(
            'downtify.monitor._fetch_monitored_tracks',
            new=AsyncMock(return_value=[song]),
        ),
        patch('downtify.monitor.spotify.track_from_id', return_value={}),
        patch.object(
            downloader,
            'download',
            side_effect=RuntimeError('both providers failed'),
        ) as download,
    ):
        assert (
            await check_monitored(
                artist, db, downloader, broadcast=AsyncMock(), loop=loop
            )
            == 0
        )
        assert (
            await check_monitored(
                artist, db, downloader, broadcast=AsyncMock(), loop=loop
            )
            == 0
        )

    download.assert_called_once()
    assert db.get_track_filenames(artist.id) == {'trk-fail': None}
