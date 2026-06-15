from __future__ import annotations

import asyncio
from pathlib import Path

from downtify import api


class FakeDownloader:
    def __init__(self, download_dir: Path):
        self.download_dir = download_dir


def test_metadata_scan_keeps_items_from_previous_batch(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    old_scan = dict(api.state.metadata_scan)
    api.state.downloader = FakeDownloader(tmp_path)
    api.state.metadata_scan = {
        **old_scan,
        'items': [{'file': 'A/one.mp3'}],
        'clean': [{'file': 'A/clean.mp3'}],
        'next_offset': 1,
    }

    def fake_scan_library(_root, _limit, _start, progress_cb):
        result = {
            'scanned': 2,
            'batch_scanned': 1,
            'total': 2,
            'matched': 1,
            'items': [{'file': 'B/two.mp3'}],
            'clean': [{'file': 'B/clean.mp3'}],
            'errors': [],
            'next_offset': 2,
            'complete': True,
        }
        progress_cb(result)
        return result

    monkeypatch.setattr(api.metadata_repair, 'scan_library', fake_scan_library)
    try:
        asyncio.run(api._run_metadata_scan(1, 1))
        assert [item['file'] for item in api.state.metadata_scan['items']] == [
            'A/one.mp3',
            'B/two.mp3',
        ]
        assert [item['file'] for item in api.state.metadata_scan['clean']] == [
            'A/clean.mp3',
            'B/clean.mp3',
        ]
        assert api.state.metadata_scan['matched'] == 2
    finally:
        api.state.downloader = old_downloader
        api.state.metadata_scan = old_scan


def test_artist_image_scan_keeps_items_from_previous_batch(tmp_path, monkeypatch):
    old_downloader = api.state.downloader
    old_scan = dict(api.state.artist_image_scan)
    api.state.downloader = FakeDownloader(tmp_path)
    api.state.artist_image_scan = {
        **old_scan,
        'items': [
            {
                'artist_id': 'artist-one',
                'artist': 'Artist One',
                'folder': 'Artist One',
                'file': 'Artist One/song.mp3',
            }
        ],
        'next_offset': 1,
    }

    def fake_scan_artist_images(_root, _limit, _start, progress_cb):
        result = {
            'scanned': 2,
            'batch_scanned': 1,
            'total': 2,
            'matched': 1,
            'items': [
                {
                    'artist_id': 'artist-two',
                    'artist': 'Artist Two',
                    'folder': 'Artist Two',
                    'file': 'Artist Two/song.mp3',
                }
            ],
            'next_offset': 2,
            'complete': True,
        }
        progress_cb(result)
        return result

    monkeypatch.setattr(
        api.metadata_repair,
        'scan_artist_images',
        fake_scan_artist_images,
    )
    try:
        asyncio.run(api._run_artist_image_scan(1, 1))
        assert [
            item['artist_id'] for item in api.state.artist_image_scan['items']
        ] == ['artist-one', 'artist-two']
        assert api.state.artist_image_scan['matched'] == 2
    finally:
        api.state.downloader = old_downloader
        api.state.artist_image_scan = old_scan
