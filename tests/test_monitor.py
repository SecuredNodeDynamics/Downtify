"""Tests for playlist/artist monitor database helpers."""

from __future__ import annotations

from pathlib import Path

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
