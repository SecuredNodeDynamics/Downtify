"""Tests for local accounts, sessions, and per-user monitors."""

from __future__ import annotations

from pathlib import Path

import pytest

from downtify.auth import AuthDB, hash_secret, verify_secret
from downtify.monitor import PlaylistMonitorDB


def test_password_hash_roundtrip() -> None:
    stored = hash_secret('correct horse')
    assert verify_secret('correct horse', stored)
    assert not verify_secret('wrong', stored)


def test_first_user_is_admin_and_owns_legacy_monitors(tmp_path: Path) -> None:
    auth = AuthDB(tmp_path / 'auth.db')
    monitor = PlaylistMonitorDB(tmp_path / 'monitor.db')
    monitor.add_playlist(
        'pl-legacy',
        'Family Mix',
        'https://open.spotify.com/playlist/pl-legacy',
    )

    admin = auth.create_user('admin', password='secret123')
    assigned = monitor.assign_unowned(admin['id'])

    assert admin['is_admin'] is True
    assert assigned == 1
    assert monitor.list_playlists(admin['id'])[0].spotify_id == 'pl-legacy'
    assert monitor.list_playlists(0) == []


def test_second_profile_can_watch_the_same_playlist(tmp_path: Path) -> None:
    monitor = PlaylistMonitorDB(tmp_path / 'monitor.db')
    first = monitor.add_playlist(
        'pl-shared',
        'Hits',
        'https://open.spotify.com/playlist/pl-shared',
        user_id=1,
    )
    second = monitor.add_playlist(
        'pl-shared',
        'Hits',
        'https://open.spotify.com/playlist/pl-shared',
        user_id=2,
    )

    assert first.id != second.id
    assert {item.user_id for item in monitor.list_playlists()} == {1, 2}
    assert monitor.get_by_spotify_id('pl-shared', 'playlist', 1) is not None
    assert monitor.get_by_spotify_id('pl-shared', 'playlist', 2) is not None


def test_pin_login_and_session(tmp_path: Path) -> None:
    auth = AuthDB(tmp_path / 'auth.db')
    auth.create_user('admin', password='secret123')
    kid = auth.create_user('kid', pin='24680', display_name='Kid')

    assert kid['has_pin'] is True
    assert kid['has_password'] is False
    assert auth.authenticate('kid', pin='24680')['id'] == kid['id']
    assert auth.authenticate('kid', password='secret123') is None

    token = auth.create_session(kid['id'])
    assert auth.user_for_token(token)['username'] == 'kid'
    auth.delete_session(token)
    assert auth.user_for_token(token) is None


def test_cannot_delete_last_admin(tmp_path: Path) -> None:
    auth = AuthDB(tmp_path / 'auth.db')
    admin = auth.create_user('admin', password='secret123')
    with pytest.raises(ValueError, match='last admin'):
        auth.delete_user(admin['id'])
