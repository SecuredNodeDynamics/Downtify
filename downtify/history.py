"""Persistent download history storage."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _song_title(song: dict[str, Any]) -> str:
    return str(song.get('name') or song.get('title') or '')


def _song_artists(song: dict[str, Any]) -> str:
    artists = song.get('artists')
    if isinstance(artists, list):
        return ', '.join(str(a) for a in artists if a)
    return str(song.get('artist') or '')


class DownloadHistoryDB:
    def __init__(self, db_path: Path) -> None:
        self._path = str(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS download_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_id TEXT,
                    title TEXT NOT NULL,
                    artists TEXT NOT NULL,
                    album TEXT,
                    source_url TEXT,
                    song_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    filename TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)

    def create(
        self,
        song: dict[str, Any],
        status: str = 'queued',
        source_url: Optional[str] = None,
    ) -> int:
        now = _now_iso()
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO download_history
                   (song_id, title, artists, album, source_url, song_json,
                    status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(song.get('song_id') or song.get('url') or ''),
                    _song_title(song),
                    _song_artists(song),
                    str(song.get('album_name') or song.get('album') or ''),
                    source_url or song.get('url') or None,
                    json.dumps(song),
                    status,
                    now,
                    now,
                ),
            )
            return int(cur.lastrowid)

    def get(self, history_id: int) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                'SELECT * FROM download_history WHERE id = ?',
                (history_id,),
            ).fetchone()
            return _row_to_dict(row) if row else None

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM download_history
                   ORDER BY updated_at DESC, id DESC
                   LIMIT ?""",
                (max(1, min(limit, 500)),),
            ).fetchall()
            return [_row_to_dict(row) for row in rows]

    def mark_running(self, history_id: int) -> None:
        now = _now_iso()
        with self._connect() as conn:
            conn.execute(
                """UPDATE download_history
                   SET status = 'downloading',
                       filename = NULL,
                       error = NULL,
                       updated_at = ?,
                       completed_at = NULL
                   WHERE id = ?""",
                (now, history_id),
            )

    def mark_done(self, history_id: int, filename: str) -> None:
        now = _now_iso()
        with self._connect() as conn:
            conn.execute(
                """UPDATE download_history
                   SET status = 'done',
                       filename = ?,
                       error = NULL,
                       updated_at = ?,
                       completed_at = ?
                   WHERE id = ?""",
                (filename, now, now, history_id),
            )

    def mark_error(self, history_id: int, error: str) -> None:
        now = _now_iso()
        with self._connect() as conn:
            conn.execute(
                """UPDATE download_history
                   SET status = 'error',
                       error = ?,
                       updated_at = ?,
                       completed_at = ?
                   WHERE id = ?""",
                (error, now, now, history_id),
            )

    def mark_skipped(self, history_id: int, filename: str) -> None:
        now = _now_iso()
        with self._connect() as conn:
            conn.execute(
                """UPDATE download_history
                   SET status = 'skipped',
                       filename = ?,
                       error = NULL,
                       updated_at = ?,
                       completed_at = ?
                   WHERE id = ?""",
                (filename, now, now, history_id),
            )

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute('DELETE FROM download_history')


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    try:
        item['song'] = json.loads(item.pop('song_json'))
    except Exception:
        item['song'] = {}
    return item
