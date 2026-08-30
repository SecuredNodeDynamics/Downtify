"""Local user accounts and session tokens for Downtify backends."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

COOKIE_NAME = 'downtify_session'
SESSION_DAYS = 30
PBKDF2_ITERATIONS = 400_000
USERNAME_RE = re.compile(r'^[A-Za-z0-9_.-]{2,32}$')
PIN_RE = re.compile(r'^\d{4,8}$')
PUBLIC_API_PATHS = frozenset({
    '/api/auth/status',
    '/api/auth/setup',
    '/api/auth/login',
    '/api/auth/logout',
    '/api/version',
    '/api/health',
    '/api/capabilities',
    '/api/check_update',
})
ADMIN_API_PATHS = frozenset({
    '/api/summary',
})
ADMIN_API_PREFIXES = ('/api/metadata',)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def hash_secret(secret: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        'sha256',
        secret.encode('utf-8'),
        salt,
        PBKDF2_ITERATIONS,
    )
    return f'pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}'


def verify_secret(secret: str, stored: str) -> bool:
    if not secret or not stored:
        return False
    try:
        algo, iters_s, salt_hex, digest_hex = stored.split('$', 3)
        if algo != 'pbkdf2_sha256':
            return False
        expected = hashlib.pbkdf2_hmac(
            'sha256',
            secret.encode('utf-8'),
            bytes.fromhex(salt_hex),
            int(iters_s),
        )
        return hmac.compare_digest(expected.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def normalize_profile_key(value: str) -> str:
    cleaned = str(value or '').strip()
    if not cleaned:
        return ''
    try:
        return str(uuid.UUID(cleaned))
    except ValueError:
        return ''


def normalize_username(value: str) -> str:
    return str(value or '').strip()


def validate_username(username: str) -> str:
    cleaned = normalize_username(username)
    if not USERNAME_RE.fullmatch(cleaned):
        raise ValueError(
            'Username must be 2-32 characters: letters, numbers, . _ -'
        )
    return cleaned


def validate_password(password: str, *, required: bool) -> str:
    cleaned = str(password or '')
    if not cleaned:
        if required:
            raise ValueError('Password is required')
        return ''
    if len(cleaned) < 8:
        raise ValueError('Password must be at least 8 characters')
    return cleaned


def validate_pin(pin: str, *, required: bool) -> str:
    cleaned = str(pin or '').strip()
    if not cleaned:
        if required:
            raise ValueError('PIN is required')
        return ''
    if not PIN_RE.fullmatch(cleaned):
        raise ValueError('PIN must be 4-8 digits')
    return cleaned


def is_public_api_path(path: str) -> bool:
    return path in PUBLIC_API_PATHS


def is_admin_api_path(path: str) -> bool:
    if path in ADMIN_API_PATHS:
        return True
    return any(
        path == prefix or path.startswith(f'{prefix}/')
        for prefix in ADMIN_API_PREFIXES
    )


def public_user(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    return {
        'id': int(data['id']),
        'username': str(data['username']),
        'display_name': str(data.get('display_name') or data['username']),
        'is_admin': bool(data.get('is_admin')),
        'has_password': bool(data.get('password_hash')),
        'has_pin': bool(data.get('pin_hash')),
        'profile_key': str(data.get('profile_key') or ''),
        'created_at': str(data.get('created_at') or ''),
    }


class AuthDB:
    def __init__(self, db_path: Path) -> None:
        self._path = str(db_path)
        self._lock = threading.Lock()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    display_name TEXT NOT NULL,
                    password_hash TEXT NOT NULL DEFAULT '',
                    pin_hash TEXT NOT NULL DEFAULT '',
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    profile_key TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )
            self._migrate_profile_key(conn)

    @staticmethod
    def _migrate_profile_key(conn: sqlite3.Connection) -> None:
        columns = {row[1] for row in conn.execute('PRAGMA table_info(users)')}
        if 'profile_key' not in columns:
            conn.execute(
                'ALTER TABLE users ADD COLUMN profile_key TEXT NOT NULL '
                "DEFAULT ''"
            )
        conn.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS idx_users_profile_key '
            "ON users(profile_key) WHERE profile_key != ''"
        )
        empty = conn.execute(
            "SELECT id FROM users WHERE profile_key = ''"
        ).fetchall()
        for row in empty:
            conn.execute(
                'UPDATE users SET profile_key = ? WHERE id = ?',
                (str(uuid.uuid4()), row['id']),
            )

    def has_users(self) -> bool:
        with self._lock, self._connect() as conn:
            row = conn.execute('SELECT 1 FROM users LIMIT 1').fetchone()
            return row is not None

    def get_user(self, user_id: int) -> Optional[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                'SELECT * FROM users WHERE id = ?', (user_id,)
            ).fetchone()
            return public_user(row) if row else None

    def list_profiles(self) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                'SELECT * FROM users ORDER BY is_admin DESC, '
                'username COLLATE NOCASE'
            ).fetchall()
            return [public_user(row) for row in rows]

    def create_user(
        self,
        username: str,
        *,
        password: str = '',
        pin: str = '',
        display_name: str = '',
        is_admin: bool = False,
        profile_key: str = '',
    ) -> dict[str, Any]:
        username = validate_username(username)
        display = str(display_name or '').strip() or username
        first_user = not self.has_users()
        if first_user:
            is_admin = True
        password = validate_password(password, required=first_user and not pin)
        pin = validate_pin(pin, required=False)
        if not password and not pin:
            raise ValueError('Set a password or a PIN')
        password_hash = hash_secret(password) if password else ''
        pin_hash = hash_secret(pin) if pin else ''
        key = normalize_profile_key(profile_key) or str(uuid.uuid4())
        with self._lock, self._connect() as conn:
            try:
                cur = conn.execute(
                    """INSERT INTO users
                       (username, display_name, password_hash, pin_hash,
                        is_admin, created_at, profile_key)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        username,
                        display,
                        password_hash,
                        pin_hash,
                        1 if is_admin else 0,
                        _now_iso(),
                        key,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                if 'profile_key' in str(exc).lower():
                    key = str(uuid.uuid4())
                    cur = conn.execute(
                        """INSERT INTO users
                           (username, display_name, password_hash, pin_hash,
                            is_admin, created_at, profile_key)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            username,
                            display,
                            password_hash,
                            pin_hash,
                            1 if is_admin else 0,
                            _now_iso(),
                            key,
                        ),
                    )
                else:
                    raise ValueError('That username is already taken') from exc
            row = conn.execute(
                'SELECT * FROM users WHERE id = ?', (cur.lastrowid,)
            ).fetchone()
            return public_user(row)

    def adopt_profile_key(
        self, user_id: int, profile_key: str
    ) -> Optional[dict[str, Any]]:
        key = normalize_profile_key(profile_key)
        if not key:
            return self.get_user(user_id)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                'SELECT * FROM users WHERE id = ?', (user_id,)
            ).fetchone()
            if row is None:
                return None
            current = str(row['profile_key'] or '')
            if current:
                return public_user(row)
            try:
                conn.execute(
                    'UPDATE users SET profile_key = ? WHERE id = ?',
                    (key, user_id),
                )
            except sqlite3.IntegrityError:
                return public_user(row)
            row = conn.execute(
                'SELECT * FROM users WHERE id = ?', (user_id,)
            ).fetchone()
            return public_user(row) if row else None

    def delete_user(self, user_id: int) -> bool:
        with self._lock, self._connect() as conn:
            admins = conn.execute(
                'SELECT COUNT(*) AS n FROM users WHERE is_admin = 1'
            ).fetchone()['n']
            row = conn.execute(
                'SELECT is_admin FROM users WHERE id = ?', (user_id,)
            ).fetchone()
            if row is None:
                return False
            if row['is_admin'] and admins <= 1:
                raise ValueError('Cannot delete the last admin')
            cur = conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            return cur.rowcount > 0

    def set_credentials(
        self,
        user_id: int,
        *,
        password: Optional[str] = None,
        pin: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        updates: dict[str, Any] = {}
        if password is not None:
            cleaned = validate_password(password, required=False)
            updates['password_hash'] = hash_secret(cleaned) if cleaned else ''
        if pin is not None:
            cleaned_pin = validate_pin(pin, required=False)
            updates['pin_hash'] = (
                hash_secret(cleaned_pin) if cleaned_pin else ''
            )
        if display_name is not None:
            name = str(display_name).strip()
            if name:
                updates['display_name'] = name
        if not updates:
            return self.get_user(user_id)
        with self._lock, self._connect() as conn:
            current = conn.execute(
                'SELECT password_hash, pin_hash FROM users WHERE id = ?',
                (user_id,),
            ).fetchone()
            if current is None:
                return None
            password_hash = updates.get(
                'password_hash', current['password_hash']
            )
            pin_hash = updates.get('pin_hash', current['pin_hash'])
            if not password_hash and not pin_hash:
                raise ValueError('Each account needs a password or a PIN')
            set_clause = ', '.join(f'{key} = ?' for key in updates)
            conn.execute(
                f'UPDATE users SET {set_clause} WHERE id = ?',
                [*updates.values(), user_id],
            )
            row = conn.execute(
                'SELECT * FROM users WHERE id = ?', (user_id,)
            ).fetchone()
            return public_user(row) if row else None

    def authenticate(
        self,
        username: str,
        *,
        password: str = '',
        pin: str = '',
    ) -> Optional[dict[str, Any]]:
        username = normalize_username(username)
        if not username:
            return None
        with self._lock, self._connect() as conn:
            row = conn.execute(
                'SELECT * FROM users WHERE username = ? COLLATE NOCASE',
                (username,),
            ).fetchone()
        if row is None:
            return None
        password_ok = bool(password) and verify_secret(
            password, str(row['password_hash'] or '')
        )
        pin_ok = bool(pin) and verify_secret(pin, str(row['pin_hash'] or ''))
        if not password_ok and not pin_ok:
            return None
        return public_user(row)

    def create_session(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        expires = (_now() + timedelta(days=SESSION_DAYS)).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT INTO sessions (token_hash, user_id, created_at, expires_at)
                   VALUES (?, ?, ?, ?)""",
                (hash_token(token), user_id, _now_iso(), expires),
            )
        return token

    def user_for_token(self, token: str) -> Optional[dict[str, Any]]:
        if not token:
            return None
        digest = hash_token(token)
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """SELECT users.* FROM sessions
                   JOIN users ON users.id = sessions.user_id
                   WHERE sessions.token_hash = ?""",
                (digest,),
            ).fetchone()
            if row is None:
                return None
            expires_row = conn.execute(
                'SELECT expires_at FROM sessions WHERE token_hash = ?',
                (digest,),
            ).fetchone()
            try:
                expires = datetime.fromisoformat(expires_row['expires_at'])
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
                if expires < _now():
                    conn.execute(
                        'DELETE FROM sessions WHERE token_hash = ?', (digest,)
                    )
                    return None
            except (TypeError, ValueError):
                conn.execute(
                    'DELETE FROM sessions WHERE token_hash = ?', (digest,)
                )
                return None
            return public_user(row)

    def delete_session(self, token: str) -> None:
        if not token:
            return
        with self._lock, self._connect() as conn:
            conn.execute(
                'DELETE FROM sessions WHERE token_hash = ?',
                (hash_token(token),),
            )

    def delete_user_sessions(self, user_id: int) -> None:
        with self._lock, self._connect() as conn:
            conn.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))


def token_from_request(
    headers: dict[str, str], cookies: dict[str, str]
) -> str:
    auth = headers.get('authorization') or headers.get('Authorization') or ''
    if auth.lower().startswith('bearer '):
        return auth[7:].strip()
    return cookies.get(COOKIE_NAME) or ''
