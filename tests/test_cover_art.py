
from io import BytesIO

from downtify.cover_art import (
    clear_cover_cache,
    cover_response_for_file,
    resize_image_bytes,
    resolve_cover_bytes,
)


def _make_jpeg(width: int, height: int) -> bytes:
    from PIL import Image

    img = Image.new('RGB', (width, height), (10, 120, 200))
    out = BytesIO()
    img.save(out, format='JPEG')
    return out.getvalue()


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


def test_resize_image_bytes_downscales_large_image():
    from PIL import Image

    original = _make_jpeg(1000, 1000)
    resized = resize_image_bytes(original, 256)

    assert resized is not None
    assert len(resized) < len(original)
    with Image.open(BytesIO(resized)) as img:
        assert max(img.size) == 256


def test_resize_image_bytes_skips_when_already_small():
    original = _make_jpeg(128, 128)
    assert resize_image_bytes(original, 256) is None


def test_resize_image_bytes_ignores_invalid_size():
    assert resize_image_bytes(_make_jpeg(500, 500), 0) is None


def test_cover_response_returns_thumbnail_for_size(tmp_path):
    from mutagen.id3 import APIC, ID3
    from PIL import Image

    clear_cover_cache()
    path = tmp_path / 'Artist - Song.mp3'
    path.write_bytes(b'audio')
    tags = ID3()
    tags.add(
        APIC(
            encoding=3,
            mime='image/jpeg',
            type=3,
            desc='cover',
            data=_make_jpeg(900, 900),
        )
    )
    tags.save(path)

    full = cover_response_for_file(tmp_path, 'Artist - Song.mp3')
    thumb = cover_response_for_file(tmp_path, 'Artist - Song.mp3', size=200)

    assert len(thumb.body) < len(full.body)
    with Image.open(BytesIO(thumb.body)) as img:
        assert max(img.size) == 200
    clear_cover_cache()
