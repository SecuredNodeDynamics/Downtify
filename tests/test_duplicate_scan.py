from __future__ import annotations

from pathlib import Path

from downtify.duplicate_scan import delete_library_files, find_duplicate_groups


def test_find_duplicate_groups_keeps_larger_copy(tmp_path: Path) -> None:
    first = tmp_path / 'Connor Price' / 'Hits'
    second = tmp_path / 'Connor Price' / 'Swing'
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    (first / 'Swing.mp3').write_bytes(b'1234')
    (second / 'Swing.flac').write_bytes(b'1234567890')

    result = find_duplicate_groups(tmp_path)

    assert result['scanned'] == 2
    assert result['duplicate_tracks'] == 1
    assert len(result['groups']) == 1
    copies = result['groups'][0]['copies']
    keepers = [item for item in copies if item['keep']]
    extras = [item for item in copies if not item['keep']]
    assert len(keepers) == 1
    assert keepers[0]['format'] == 'flac'
    assert extras[0]['format'] == 'mp3'


def test_delete_library_files_removes_audio_and_lyrics(tmp_path: Path) -> None:
    song = tmp_path / 'Artist - Song.mp3'
    lyrics = tmp_path / 'Artist - Song.lrc'
    song.write_bytes(b'audio')
    lyrics.write_text('[00:00.00]hello', encoding='utf-8')
    nested = tmp_path / 'Artist' / 'Album'
    nested.mkdir(parents=True)
    other = nested / 'keep.mp3'
    other.write_bytes(b'keep')

    result = delete_library_files(tmp_path, ['Artist - Song.mp3', '../escape.mp3'])

    assert result['deleted'] == ['Artist - Song.mp3']
    assert result['failed_count'] == 1
    assert not song.exists()
    assert not lyrics.exists()
    assert other.exists()
