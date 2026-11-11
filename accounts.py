"""Akun lokal SQLite; kata sandi hanya disimpan sebagai hash scrypt."""

import hashlib
import hmac
import re
import secrets
import sqlite3
import time

from finance import database

LANGUAGES = {"ja": "日本語", "en": "English", "id": "Bahasa Indonesia"}


def initialize(path):
    with database(path) as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL, password_hash TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'ja' CHECK(language IN ('ja','en','id')),
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")


def password_hash(password, salt=None):
    salt = salt if salt is not None else secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**17,
        r=8,
        p=1,
        maxmem=256 * 1024 * 1024,
        dklen=64,
    )
    return f"scrypt$131072$8$1${salt.hex()}${digest.hex()}"


def validate_username(username):
    username = username.strip().lower()
    if not re.fullmatch(r"[a-z0-9_]{3,32}", username):
        raise ValueError(
            "ユーザー名は半角英数字・アンダースコアで3〜32文字にしてください。"
        )
    return username


def validate_password(password):
    if not 12 <= len(password) <= 128:
        raise ValueError("パスワードは12〜128文字で入力してください。")


def register(path, username, display_name, password, language="ja"):
    username, display_name = validate_username(username), display_name.strip()
    if not 1 <= len(display_name) <= 40:
        raise ValueError("表示名は1〜40文字で入力してください。")
    validate_password(password)
    if language not in LANGUAGES:
        raise ValueError("対応していない言語です。")
    hashed = password_hash(password)
    try:
        with database(path) as connection:
            return connection.execute(
                "INSERT INTO users(username,display_name,password_hash,language) VALUES(?,?,?,?)",
                (username, display_name, hashed, language),
            ).lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("このユーザー名はすでに使われています。") from None


def get_user(path, user_id):
    with database(path) as connection:
        row = connection.execute(
            "SELECT id,username,display_name,language FROM users WHERE id=?", (user_id,)
        ).fetchone()
        return dict(row) if row else None


def list_local_users(path):
    with database(path) as connection:
        return connection.execute(
            "SELECT id, username, display_name FROM users ORDER BY id"
        ).fetchall()


def recover_local_user(path, user_id, username=None, password=None):
    """Update credentials for an account selected by the local computer owner."""
    changes = {}
    if username is not None:
        changes["username"] = validate_username(username)
    if password is not None:
        validate_password(password)
        changes.update(password_hash=password_hash(password), failed_attempts=0, locked_until=0)
    if not changes:
        raise ValueError("ユーザー名またはパスワードを入力してください。")
    assignments = ", ".join(f"{column}=?" for column in changes)
    try:
        with database(path) as connection:
            updated = connection.execute(
                f"UPDATE users SET {assignments} WHERE id=?",
                (*changes.values(), user_id),
            )
            if not updated.rowcount:
                raise ValueError("アカウントが見つかりません。ログインし直してください。")
    except sqlite3.IntegrityError:
        raise ValueError("このユーザー名はすでに使われています。") from None


def authenticate(path, username, password):
    if len(password) > 128:
        raise ValueError("ユーザー名またはパスワードが正しくありません。")
    username = username.strip().lower()
    # Serialize attempts so parallel local sessions cannot bypass the lockout counter.
    with database(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
        now = time.time()
        if row and row["locked_until"] > now:
            message = "試行回数が上限に達しました。5分後にもう一度お試しください。"
            user_id = None
        else:
            stored = row["password_hash"] if row else None
            salt = bytes.fromhex(stored.split("$")[4]) if stored else bytes(16)
            valid = hmac.compare_digest(password_hash(password, salt), stored or "")
            if row and valid:
                connection.execute(
                    "UPDATE users SET failed_attempts=0,locked_until=0 WHERE id=?",
                    (row["id"],),
                )
                user_id, message = row["id"], None
            else:
                if row:
                    failures = (
                        row["failed_attempts"] + 1 if row["locked_until"] == 0 else 1
                    )
                    connection.execute(
                        "UPDATE users SET failed_attempts=?,locked_until=? WHERE id=?",
                        (failures, now + 300 if failures >= 5 else 0, row["id"]),
                    )
                user_id, message = (
                    None,
                    "ユーザー名またはパスワードが正しくありません。",
                )
    # Raise after commit: failed-attempt counters must survive unsuccessful logins.
    if message:
        raise ValueError(message)
    return get_user(path, user_id)


def set_language(path, user_id, language):
    if language not in LANGUAGES:
        raise ValueError("対応していない言語です。")
    with database(path) as connection:
        if not connection.execute(
            "UPDATE users SET language=? WHERE id=?", (language, user_id)
        ).rowcount:
            raise ValueError("アカウントが見つかりません。ログインし直してください。")
