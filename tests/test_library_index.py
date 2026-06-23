from pathlib import Path

import pytest
from mutagen.id3 import ID3, TALB, TCON, TIT2, TPE1

from downtify import library_index


def test_list_library_files_reads_tags_and_paths(tmp_path):
    artist_dir = tmp_path / 'Artist One' / 'Album A'
    artist_dir.mkdir(parents=True)
    path = artist_dir / '01 - Song Title.mp3'
    path.write_bytes(b'audio')
    tags = ID3()
    tags.add(TIT2(encoding=3, text='Song Title'))
    tags.add(TPE1(encoding=3, text='Tagged Artist'))
    tags.add(TALB(encoding=3, text='Tagged Album'))
    tags.add(TCON(encoding=3, text='Jazz'))
    tags.save(path)

    items = library_index.list_library_files(tmp_path)

    assert len(items) == 1
    assert items[0]['file'] == 'Artist One/Album A/01 - Song Title.mp3'
    assert items[0]['title'] == 'Song Title'
    assert items[0]['artist'] == 'Artist One'
    assert items[0]['album'] == 'Album A'
    assert items[0]['genre'] == 'Jazz'


def test_list_library_files_falls_back_to_filename(tmp_path):
    path = tmp_path / 'Artist - Title.mp3'
    path.write_bytes(b'audio')

    items = library_index.list_library_files(tmp_path)

    assert items == [
        {
            'file': 'Artist - Title.mp3',
            'title': 'Title',
            'artist': 'Artist',
            'album': '',
            'genre': '',
        }
    ]


def test_read_library_entry_rejects_traversal(tmp_path):
    with pytest.raises(ValueError, match='Invalid library path'):
        library_index.read_library_entry(tmp_path, '../outside.mp3')
