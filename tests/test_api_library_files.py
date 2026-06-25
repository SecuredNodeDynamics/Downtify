from __future__ import annotations

from mutagen.id3 import ID3, TIT2, TPE1

from downtify import api
from downtify.api import get_library_files


def test_get_library_files_returns_artists_list(tmp_path, monkeypatch):
    download_dir = tmp_path / 'downloads'
    album_dir = download_dir / 'Connor Price' / 'Swing'
    album_dir.mkdir(parents=True)
    path = album_dir / '01 - Swing.mp3'
    path.write_bytes(b'audio')
    tags = ID3()
    tags.add(TIT2(encoding=3, text='Swing'))
    tags.add(TPE1(encoding=3, text='Connor Price, Nic D'))
    tags.save(path)

    api.state.default_download_dir = download_dir
    api.state.downloader = None
    api.state.library_files_cache = {
        'root': '',
        'items': [],
        'built_at': 0.0,
        'building': False,
    }

    items = get_library_files()

    assert len(items) == 1
    assert items[0]['artist'] == 'Connor Price'
    assert items[0]['artists'] == ['Connor Price', 'Nic D']
