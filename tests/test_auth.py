"""Tests for local accounts, sessions, and per-user monitors."""

from __future__ import annotations

from pathlib import Path

import pytest

from downtify.auth import (
    AuthDB,
    hash_secret,
    is_admin_api_path,
    verify_secret,
)
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


def test_profile_key_is_stable_and_adoptable(tmp_path: Path) -> None:
    auth = AuthDB(tmp_path / 'auth.db')
    shared = '11111111-1111-4111-8111-111111111111'
    first = auth.create_user('admin', password='secret123', profile_key=shared)
    assert first['profile_key'] == shared
    kept = auth.adopt_profile_key(
        first['id'], '22222222-2222-4222-8222-222222222222'
    )
    assert kept['profile_key'] == shared

    other = auth.create_user('kid', pin='24680')
    with auth._connect() as conn:
        conn.execute(
            "UPDATE users SET profile_key = '' WHERE id = ?", (other['id'],)
        )
    fresh = '33333333-3333-4333-8333-333333333333'
    filled = auth.adopt_profile_key(other['id'], fresh)
    assert filled['profile_key'] == fresh


def test_monitor_upsert_merges_by_spotify_id(tmp_path: Path) -> None:
    db = PlaylistMonitorDB(tmp_path / 'monitor.db')
    created_action, created = db.upsert_synced_item(
        1,
        spotify_id='pl1',
        name='Hits',
        url='https://open.spotify.com/playlist/pl1',
        kind='playlist',
        interval_minutes=60,
        enabled=True,
        image_url='',
    )
    updated_action, updated = db.upsert_synced_item(
        1,
        spotify_id='pl1',
        name='Hits Weekly',
        url='https://open.spotify.com/playlist/pl1',
        kind='playlist',
        interval_minutes=30,
        enabled=True,
        image_url='https://example.test/cover.jpg',
    )
    other_user, _item = db.upsert_synced_item(
        2,
        spotify_id='pl1',
        name='Hits',
        url='https://open.spotify.com/playlist/pl1',
        kind='playlist',
    )

    assert created_action == 'created'
    assert updated_action == 'updated'
    assert other_user == 'created'
    assert updated.name == 'Hits Weekly'
    assert updated.interval_minutes == 30
    assert len(db.list_playlists(1)) == 1
    assert created.id == updated.id


def test_cannot_delete_last_admin(tmp_path: Path) -> None:
    auth = AuthDB(tmp_path / 'auth.db')
    admin = auth.create_user('admin', password='secret123')
    with pytest.raises(ValueError, match='last admin'):
        auth.delete_user(admin['id'])


def test_admin_can_reset_family_pin_and_password(tmp_path: Path) -> None:
    auth = AuthDB(tmp_path / 'auth.db')
    auth.create_user('admin', password='secret123')
    kid = auth.create_user('kid', pin='24680', display_name='Kid')
    token = auth.create_session(kid['id'])

    updated = auth.set_credentials(kid['id'], pin='13579', password='newpass1')
    auth.delete_user_sessions(kid['id'])

    assert updated['has_pin'] is True
    assert updated['has_password'] is True
    assert auth.authenticate('kid', pin='24680') is None
    assert auth.authenticate('kid', pin='13579')['id'] == kid['id']
    assert auth.authenticate('kid', password='newpass1')['id'] == kid['id']
    assert auth.user_for_token(token) is None


def test_admin_api_paths() -> None:
    assert is_admin_api_path('/api/metadata/scan')
    assert is_admin_api_path('/api/metadata/artist-images/status')
    assert is_admin_api_path('/api/summary')
    assert is_admin_api_path('/api/settings/update')
    assert is_admin_api_path('/api/jellyfin/libraries')
    assert is_admin_api_path('/api/jellyfin/refresh')
    assert is_admin_api_path('/api/library/genres/refresh')
    assert is_admin_api_path('/api/library/genres/cancel')
    assert not is_admin_api_path('/api/library/genres/status')
    assert not is_admin_api_path('/api/settings')
    assert not is_admin_api_path('/api/health')
    assert not is_admin_api_path('/api/update')
    assert not is_admin_api_path('/api/library/files')
    assert not is_admin_api_path('/api/library/artist-cover')
    assert not is_admin_api_path(
        '/api/metadata/artist-images/folder-preview'
    )
    assert is_admin_api_path('/api/auth/users')
    assert is_admin_api_path('/api/auth/users/3')
    assert not is_admin_api_path('/api/auth/me')
