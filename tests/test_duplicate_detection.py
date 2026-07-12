from __future__ import annotations

from downtify.downloader import Downloader
from mutagen.id3 import ID3, TALB


def test_duplicate_detection_finds_exact_output_target(tmp_path):
    downloader = Downloader(tmp_path, output_template='{artists} - {title}')
    song = {'name': 'Good Song', 'artists': ['Good Artist']}
    existing = tmp_path / 'Good Artist - Good Song.mp3'
    existing.write_text('audio', encoding='utf-8')

    assert downloader.duplicate_filename_for(song) == existing.name


def test_duplicate_detection_finds_normalized_audio_file_in_subfolder(tmp_path):
    downloader = Downloader(tmp_path, output_template='{artists} - {title}')
    song = {'name': 'Good Song!', 'artists': ['Good Artist']}
    folder = tmp_path / 'Nested'
    folder.mkdir()
    existing = folder / 'good artist - good song.flac'
    existing.write_text('audio', encoding='utf-8')

    assert downloader.duplicate_filename_for(song) == 'Nested/good artist - good song.flac'


def test_duplicate_detection_ignores_non_audio_files(tmp_path):
    downloader = Downloader(tmp_path, output_template='{artists} - {title}')
    song = {'name': 'Good Song', 'artists': ['Good Artist']}
    (tmp_path / 'Good Artist - Good Song.txt').write_text(
        'not audio',
        encoding='utf-8',
    )

    assert downloader.duplicate_filename_for(song) is None


def test_duplicate_detection_matches_when_only_first_artist_was_saved(tmp_path):
    downloader = Downloader(tmp_path, output_template='{artists} - {title}')
    song = {
        'name': 'Swing',
        'artists': ['Connor Price', 'Nic D', '4Korners'],
    }
    (tmp_path / 'Connor Price - Swing.mp3').write_text('audio', encoding='utf-8')

    assert downloader.duplicate_filename_for(song) == 'Connor Price - Swing.mp3'


def test_duplicate_detection_does_not_skip_different_album_track(tmp_path):
    downloader = Downloader(tmp_path, output_template='{artists} - {title}')
    existing = tmp_path / 'Uriel Vega - Intro.mp3'
    tags = ID3()
    tags.add(TALB(encoding=3, text='Already Owned Album'))
    tags.save(existing)

    song = {
        'name': 'Intro',
        'artists': ['Uriel Vega'],
        'album_name': 'Live in Israel',
    }

    assert downloader.duplicate_filename_for(song) is None
