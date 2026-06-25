
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
    assert items[0]['browse_genre'] == 'Jazz'


def test_list_library_files_falls_back_to_filename(monkeypatch, tmp_path):
    path = tmp_path / 'Artist - Title.mp3'
    path.write_bytes(b'audio')

    monkeypatch.setattr(
        library_index,
        'lookup_artist_genre',
        lambda artist, fetch=True: '',
    )

    items = library_index.list_library_files(tmp_path)

    assert items == [
        {
            'file': 'Artist - Title.mp3',
            'title': 'Title',
            'artist': 'Artist',
            'album': '',
            'genre': '',
            'browse_genre': '',
        }
    ]


def test_list_library_files_fast_reads_genre_from_tags(tmp_path):
    artist_dir = tmp_path / 'Artist One' / 'Album A'
    artist_dir.mkdir(parents=True)
    path = artist_dir / '01 - Song Title.mp3'
    path.write_bytes(b'audio')
    tags = ID3()
    tags.add(TIT2(encoding=3, text='Tagged Title'))
    tags.add(TPE1(encoding=3, text='Tagged Artist'))
    tags.add(TALB(encoding=3, text='Tagged Album'))
    tags.add(TCON(encoding=3, text='Jazz'))
    tags.save(path)

    items = library_index.list_library_files_fast(tmp_path)

    assert len(items) == 1
    assert items[0]['file'] == 'Artist One/Album A/01 - Song Title.mp3'
    assert items[0]['title'] == 'Song Title'
    assert items[0]['artist'] == 'Artist One'
    assert items[0]['album'] == 'Album A'
    assert items[0]['genre'] == 'Jazz'
    assert items[0]['browse_genre'] == 'Jazz'


def test_list_library_files_fast_reads_genre_from_tags_for_album_paths(tmp_path):
    artist_dir = tmp_path / 'Alan Silvestri'
    artist_dir.mkdir(parents=True)
    path = artist_dir / 'Alan Silvestri - Main Title.mp3'
    path.write_bytes(b'audio')
    tags = ID3()
    tags.add(TIT2(encoding=3, text='Main Title'))
    tags.add(TPE1(encoding=3, text='Alan Silvestri'))
    tags.add(TALB(encoding=3, text='Back to the Future'))
    tags.save(path)

    items = library_index.list_library_files_fast(tmp_path)

    assert len(items) == 1
    assert items[0]['artist'] == 'Alan Silvestri'
    assert items[0]['album'] == 'Back to the Future'
    assert items[0]['title'] == 'Main Title'


def test_read_library_entry_rejects_traversal(tmp_path):
    with pytest.raises(ValueError, match='Invalid library path'):
        library_index.read_library_entry(
            tmp_path,
            '../outside.mp3',
            {},
            fetch_missing_genres=False,
        )


def test_list_library_files_uses_artist_genre_when_tags_missing(
    monkeypatch, tmp_path
):
    path = tmp_path / 'Aaron Copland' / 'Fanfare.mp3'
    path.parent.mkdir(parents=True)
    path.write_bytes(b'audio')

    monkeypatch.setattr(
        library_index,
        'lookup_artist_genre',
        lambda artist, fetch=True: 'classical'
        if artist == 'Aaron Copland'
        else '',
    )

    items = library_index.list_library_files(tmp_path)

    assert len(items) == 1
    assert items[0]['genre'] == 'Classical'


def test_enrich_library_genres_propagates_within_album(tmp_path):
    album = tmp_path / 'Aaron Copland' / 'Hollywood'
    album.mkdir(parents=True)
    (album / '01 Fanfare.mp3').write_bytes(b'audio')
    tagged = album / '02 Rodeo.mp3'
    tagged.write_bytes(b'audio')
    tags = ID3()
    tags.add(TCON(encoding=3, text='Classical'))
    tags.save(tagged)

    items = library_index.list_library_files(tmp_path)

    assert len(items) == 2
    assert all(item['genre'] == 'Classical' for item in items)
