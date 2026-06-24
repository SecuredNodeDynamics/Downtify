from __future__ import annotations

from datetime import datetime, timedelta, timezone

from downtify.history import DownloadHistoryDB


def test_history_list_orders_newest_completed_first(tmp_path):
    db = DownloadHistoryDB(tmp_path / 'history.db')
    first_id = db.create({'name': 'First'}, status='queued')
    second_id = db.create({'name': 'Second'}, status='queued')
    third_id = db.create({'name': 'Third'}, status='queued')

    db.mark_done(first_id, 'First.mp3')
    db.mark_done(second_id, 'Second.mp3')
    db.mark_done(third_id, 'Third.mp3')

    rows = db.list()
    assert [row['id'] for row in rows] == [third_id, second_id, first_id]
    assert [row['title'] for row in rows] == ['Third', 'Second', 'First']


def test_history_list_uses_completed_at_over_updated_at(tmp_path):
    db = DownloadHistoryDB(tmp_path / 'history.db')
    older_id = db.create({'name': 'Older'}, status='queued')
    newer_id = db.create({'name': 'Newer'}, status='queued')

    db.mark_done(older_id, 'Older.mp3')
    db.mark_done(newer_id, 'Newer.mp3')

    older_completed = (
        datetime.now(timezone.utc) - timedelta(hours=2)
    ).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    newer_completed = (
        datetime.now(timezone.utc) - timedelta(minutes=5)
    ).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    with db._connect() as conn:
        conn.execute(
            'UPDATE download_history SET completed_at = ? WHERE id = ?',
            (older_completed, older_id),
        )
        conn.execute(
            'UPDATE download_history SET completed_at = ? WHERE id = ?',
            (newer_completed, newer_id),
        )

    rows = db.list()
    assert rows[0]['id'] == newer_id
    assert rows[1]['id'] == older_id


def test_history_records_and_lists_download_attempts(tmp_path):
    db = DownloadHistoryDB(tmp_path / 'history.db')
    song = {
        'song_id': 'track-1',
        'name': 'First Song',
        'artists': ['One', 'Two'],
        'album_name': 'The Album',
        'url': 'https://example.test/song',
    }

    history_id = db.create(song, status='queued')
    db.mark_done(history_id, 'One - First Song.mp3')

    rows = db.list()
    assert len(rows) == 1
    assert rows[0]['id'] == history_id
    assert rows[0]['status'] == 'done'
    assert rows[0]['filename'] == 'One - First Song.mp3'
    assert rows[0]['song'] == song


def test_history_retry_state_clears_error_and_filename(tmp_path):
    db = DownloadHistoryDB(tmp_path / 'history.db')
    history_id = db.create({'name': 'Broken Song'}, status='downloading')

    db.mark_error(history_id, 'boom')
    assert db.get(history_id)['status'] == 'error'

    db.mark_running(history_id)
    row = db.get(history_id)

    assert row['status'] == 'downloading'
    assert row['error'] is None
    assert row['filename'] is None
    assert row['completed_at'] is None


def test_history_clear_removes_rows(tmp_path):
    db = DownloadHistoryDB(tmp_path / 'history.db')
    db.create({'name': 'Song'}, status='done')

    db.clear()

    assert db.list() == []


def test_history_can_mark_duplicate_as_skipped(tmp_path):
    db = DownloadHistoryDB(tmp_path / 'history.db')
    history_id = db.create({'name': 'Song'}, status='downloading')

    db.mark_skipped(history_id, 'Artist - Song.mp3')
    row = db.get(history_id)

    assert row['status'] == 'skipped'
    assert row['filename'] == 'Artist - Song.mp3'
    assert row['error'] is None
    assert row['completed_at'] is not None


def test_history_counts_recent_completed_rows(tmp_path):
    db = DownloadHistoryDB(tmp_path / 'history.db')
    done_id = db.create({'name': 'Done'}, status='downloading')
    skipped_id = db.create({'name': 'Skipped'}, status='downloading')
    old_id = db.create({'name': 'Old'}, status='downloading')
    failed_id = db.create({'name': 'Failed'}, status='downloading')

    db.mark_done(done_id, 'Done.mp3')
    db.mark_skipped(skipped_id, 'Skipped.mp3')
    db.mark_done(old_id, 'Old.mp3')
    db.mark_error(failed_id, 'boom')

    old_completed_at = (
        datetime.now(timezone.utc) - timedelta(days=2)
    ).isoformat()
    with db._connect() as conn:
        conn.execute(
            'UPDATE download_history SET completed_at = ? WHERE id = ?',
            (old_completed_at, old_id),
        )

    since = datetime.now(timezone.utc) - timedelta(hours=24)

    assert db.count_completed_since(since) == 2
