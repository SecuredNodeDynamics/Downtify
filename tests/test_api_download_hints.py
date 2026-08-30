"""Tests for client hint merge on per-URL downloads."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from downtify import api
from downtify.api import _merge_client_track_hints


def test_merge_applies_track_index_and_dates():
    base: dict = {
        'song_id': 'spotify:id',
        'url': 'https://open.spotify.com/track/x',
    }
    _merge_client_track_hints(
        base,
        {
            'track_number': 4,
            'album_track_total': 14,
            'release_date': '2022-03-01',
            'year': '2022',
            'noise': 'ignored',
        },
    )
    assert base['track_number'] == 4
    assert base['album_track_total'] == 14
    assert base['release_date'] == '2022-03-01'
    assert base['year'] == '2022'
    assert 'noise' not in base


def test_merge_fills_identity_fields_when_refetch_is_sparse():
    base: dict = {'song_id': 'yt123', 'name': '', 'artists': []}
    _merge_client_track_hints(
        base,
        {
            'name': 'Stumblin in (Acoustic Cover)',
            'artists': ['Audrey Stclair'],
            'album_name': 'Euphony',
            'cover_url': 'https://example.com/c.jpg',
        },
    )
    assert base['name'] == 'Stumblin in (Acoustic Cover)'
    assert base['artists'] == ['Audrey Stclair']
    assert base['album_name'] == 'Euphony'
    assert base['cover_url'] == 'https://example.com/c.jpg'


def test_merge_ignores_invalid_track_number():
    base: dict = {'song_id': 'a'}
    _merge_client_track_hints(
        base, {'track_number': 'x', 'album_track_total': 0}
    )
    assert 'track_number' not in base
    assert 'album_track_total' not in base


def test_download_queue_accepts_multiple_album_batches():
    old_jobs = api.state.download_jobs
    api.state.download_jobs = {}
    try:
        api._ensure_download_queue_capacity(80)
        api._ensure_download_queue_capacity(120)
    finally:
        api.state.download_jobs = old_jobs


def test_download_queue_still_rejects_runaway_batches():
    old_jobs = api.state.download_jobs
    api.state.download_jobs = {}
    try:
        with pytest.raises(HTTPException) as exc:
            api._ensure_download_queue_capacity(
                api.MAX_PENDING_DOWNLOAD_JOBS + 1
            )
        assert exc.value.status_code == 429
    finally:
        api.state.download_jobs = old_jobs
