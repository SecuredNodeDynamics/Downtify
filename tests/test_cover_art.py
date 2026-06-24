
from downtify.cover_art import resolve_cover_bytes


def test_resolve_cover_bytes_uses_embedded_tags(tmp_path):
    from mutagen.id3 import APIC, ID3, TIT2

    path = tmp_path / 'Artist - Song.mp3'
    path.write_bytes(b'audio')
    tags = ID3()
    tags.add(TIT2(encoding=3, text='Song'))
    tags.add(
        APIC(
            encoding=3,
            mime='image/jpeg',
            type=3,
            desc='cover',
            data=b'embedded-cover',
        )
    )
    tags.save(path)

    data, mime = resolve_cover_bytes(path)

    assert data == b'embedded-cover'
    assert mime == 'image/jpeg'


def test_resolve_cover_bytes_falls_back_to_folder_jpg(tmp_path):
    album = tmp_path / 'Aaron Copland' / 'Hollywood'
    album.mkdir(parents=True)
    track = album / '01 Opening.mp3'
    track.write_bytes(b'audio')
    (album / 'folder.jpg').write_bytes(b'\xff\xd8\xff\xe0fake-jpeg')

    data, mime = resolve_cover_bytes(track)

    assert data == b'\xff\xd8\xff\xe0fake-jpeg'
    assert mime == 'image/jpeg'


def test_resolve_cover_bytes_checks_parent_artist_folder(tmp_path):
    artist = tmp_path / 'Aaron Copland'
    album = artist / 'Hollywood'
    album.mkdir(parents=True)
    track = album / '01 Opening.mp3'
    track.write_bytes(b'audio')
    (artist / 'folder.jpg').write_bytes(b'\xff\xd8\xff\xe0artist-cover')

    data, _mime = resolve_cover_bytes(track)

    assert data == b'\xff\xd8\xff\xe0artist-cover'


def test_resolve_cover_bytes_walks_up_playlist_subfolders(tmp_path):
    playlist = tmp_path / 'My Playlist' / 'Aaron Copland' / 'Hollywood'
    playlist.mkdir(parents=True)
    track = playlist / '01 Opening.mp3'
    track.write_bytes(b'audio')
    (playlist / 'folder.jpg').write_bytes(b'\xff\xd8\xff\xe0album-cover')

    data, _mime = resolve_cover_bytes(track)

    assert data == b'\xff\xd8\xff\xe0album-cover'
