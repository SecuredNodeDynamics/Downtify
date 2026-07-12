from __future__ import annotations

from downtify.downloader import Downloader
from downtify.library_index import (
    album_in_library,
    media_in_library,
    media_item_key,
)


def test_media_item_key_prefers_song_and_browse_ids():
    assert media_item_key({'song_id': 'track:1', 'browse_id': 'album:1'}) == 'track:1'
    assert media_item_key({'browse_id': 'album:1'}) == 'album:1'


def test_album_in_library_matches_artist_and_album_name():
    album = {
        'media_type': 'album',
        'name': 'Classic 50s Jazz',
        'artists': ['1950s Jazz'],
        'browse_id': 'album:1',
    }
    library_items = [
        {
            'file': '1950s Jazz/Classic 50s Jazz/01.flac',
            'artist': '1950s Jazz',
            'album': 'Classic 50s Jazz',
            'title': 'Track',
            'genre': 'Swing',
            'browse_genre': 'Jazz',
        }
    ]

    assert album_in_library(album, library_items) is True
    assert (
        album_in_library(
            {**album, 'artists': ['Different Artist']},
            library_items,
        )
        is False
    )


def test_album_in_library_matches_any_listed_artist():
    album = {
        'media_type': 'album',
        'name': 'Swing',
        'artists': ['Connor Price', 'Nic D', '4Korners'],
        'browse_id': 'album:1',
    }
    library_items = [
        {
            'file': 'Connor Price/Swing/01.flac',
            'artist': 'Connor Price',
            'album': 'Swing',
            'title': 'Swing',
        }
    ]

    assert album_in_library(album, library_items) is True


def test_album_in_library_requires_expected_track_count_when_known():
    album = {
        'media_type': 'album',
        'name': 'Live in Israel',
        'artists': ['Uriel Vega'],
        'track_count': 3,
        'browse_id': 'album:1',
    }
    partial_library = [
        {
            'file': 'Uriel Vega/Live in Israel/01.flac',
            'artist': 'Uriel Vega',
            'album': 'Live in Israel',
            'title': 'Intro',
        }
    ]
    complete_library = [
        *partial_library,
        {
            'file': 'Uriel Vega/Live in Israel/02.flac',
            'artist': 'Uriel Vega',
            'album': 'Live in Israel',
            'title': 'Second',
        },
        {
            'file': 'Uriel Vega/Live in Israel/03.flac',
            'artist': 'Uriel Vega',
            'album': 'Live in Israel',
            'title': 'Third',
        },
    ]

    assert album_in_library(album, partial_library) is False
    assert album_in_library(album, complete_library) is True


def test_track_in_library_from_metadata_matches_title_and_artist():
    from downtify.library_index import track_in_library_from_metadata

    track = {
        'media_type': 'track',
        'name': 'Swing',
        'artists': ['Connor Price', 'Nic D'],
        'song_id': 'track:1',
    }
    library_items = [
        {
            'file': 'Connor Price/Swing/Swing.flac',
            'artist': 'Connor Price',
            'album': 'Swing',
            'title': 'Swing',
        }
    ]

    assert track_in_library_from_metadata(track, library_items) is True


def test_track_in_library_from_metadata_matches_secondary_tagged_artist():
    from downtify.library_index import track_in_library_from_metadata

    track = {
        'media_type': 'track',
        'name': 'Swing',
        'artists': ['Nic D'],
        'song_id': 'track:1',
    }
    library_items = [
        {
            'file': 'Connor Price/Swing/Swing.flac',
            'artist': 'Connor Price',
            'artists': ['Connor Price', 'Nic D', '4Korners'],
            'album': 'Swing',
            'title': 'Swing',
        }
    ]

    assert track_in_library_from_metadata(track, library_items) is True


def test_media_in_library_uses_duplicate_detection_for_tracks(tmp_path):
    downloader = Downloader(tmp_path, output_template='{artists} - {title}')
    track = {
        'media_type': 'track',
        'name': 'Good Song',
        'artists': ['Good Artist'],
        'song_id': 'track:1',
    }
    (tmp_path / 'Good Artist - Good Song.mp3').write_text('audio', encoding='utf-8')

    assert (
        media_in_library(
            track,
            downloader=downloader,
            library_items=[],
        )
        is True
    )
