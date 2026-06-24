"""Tests for playlist/artist monitor database helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from downtify import api
from downtify.monitor import PlaylistMonitorDB


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


@pytest.mark.asyncio
async def test_list_monitor_playlists_does_not_block_on_spotify_images(
    tmp_path: Path,
) -> None:
    old_monitor_db = api.state.monitor_db
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

        with patch(
            'downtify.api.spotify.embed_image_url',
            side_effect=AssertionError('list should not fetch Spotify covers'),
        ):
            payload = await api.list_monitor_playlists()

        assert len(payload) == 1
        assert payload[0]['name'] == 'Test Playlist'
        assert payload[0]['kind'] == 'playlist'
    finally:
        api.state.monitor_db = old_monitor_db
