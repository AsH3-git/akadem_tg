"""SQLite persistence layer.

Every function opens and closes its own short-lived connection. This is
deliberate: pyTelegramBotAPI runs message/callback handlers in a thread pool
by default, and sqlite3 connections must not be shared across threads. Given
the write volume of a student quest (a handful of writes per student per
sight), the overhead of a fresh connection per call is irrelevant.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from config import DB_PATH

# States a student can be in.
STATE_IDLE = "idle"                    # waiting for them to press "Отправить фото"
STATE_AWAITING_PHOTO = "awaiting_photo"  # button pressed, waiting for the photo itself
STATE_AWAITING_APPROVAL = "awaiting_approval"  # photo sent, waiting on the manager
STATE_FINISHED = "finished"

PHASE_MAIN = "main"
PHASE_BONUS = "bonus"

SUBMISSION_PENDING = "pending"
SUBMISSION_APPROVED = "approved"
SUBMISSION_REJECTED = "rejected"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id     INTEGER PRIMARY KEY,
                username    TEXT,
                full_name   TEXT,
                route       TEXT,                 -- e.g. "213"; NULL until chosen
                phase       TEXT DEFAULT 'main',   -- 'main' or 'bonus'
                sector_idx  INTEGER DEFAULT 0,     -- index into route (main phase)
                sight_idx   INTEGER DEFAULT 0,     -- index into current sector's sights
                state       TEXT DEFAULT 'idle',
                created_at  TEXT,
                updated_at  TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS submissions (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id            INTEGER NOT NULL,
                sector             INTEGER NOT NULL,
                sight_name         TEXT,
                photo_file_id      TEXT NOT NULL,
                status             TEXT DEFAULT 'pending',
                manager_id         INTEGER,
                manager_chat_id    INTEGER,
                manager_message_id INTEGER,
                created_at         TEXT,
                decided_at         TEXT
            )
            """
        )


# --- users ---------------------------------------------------------------

def get_user(chat_id: int) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchone()


def create_user(chat_id: int, username: str | None, full_name: str | None) -> None:
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO users (chat_id, username, full_name, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET username = excluded.username,
                                                full_name = excluded.full_name
            """,
            (chat_id, username, full_name, STATE_IDLE, now, now),
        )


def reset_user(chat_id: int) -> None:
    """Wipe a user's progress so they can (re)start the quest from scratch."""
    with _connect() as conn:
        conn.execute(
            """
            UPDATE users
            SET route = NULL, phase = ?, sector_idx = 0, sight_idx = 0,
                state = ?, updated_at = ?
            WHERE chat_id = ?
            """,
            (PHASE_MAIN, STATE_IDLE, _now(), chat_id),
        )


def update_user(chat_id: int, **fields) -> None:
    if not fields:
        return
    fields["updated_at"] = _now()
    columns = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [chat_id]
    with _connect() as conn:
        conn.execute(f"UPDATE users SET {columns} WHERE chat_id = ?", values)


def count_users_by_state() -> dict[str, int]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT state, COUNT(*) AS n FROM users GROUP BY state"
        ).fetchall()
    return {row["state"]: row["n"] for row in rows}


# --- submissions -----------------------------------------------------------

def create_submission(chat_id: int, sector: int, sight_name: str, photo_file_id: str) -> int:
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO submissions (chat_id, sector, sight_name, photo_file_id, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, sector, sight_name, photo_file_id, _now()),
        )
        return cursor.lastrowid


def get_submission(submission_id: int) -> sqlite3.Row | None:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM submissions WHERE id = ?", (submission_id,)
        ).fetchone()


def set_submission_manager_message(submission_id: int, manager_id: int, manager_chat_id: int, manager_message_id: int) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE submissions
            SET manager_id = ?, manager_chat_id = ?, manager_message_id = ?
            WHERE id = ?
            """,
            (manager_id, manager_chat_id, manager_message_id, submission_id),
        )


def decide_submission(submission_id: int, status: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE submissions SET status = ?, decided_at = ? WHERE id = ?",
            (status, _now(), submission_id),
        )


def count_pending_submissions() -> int:
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM submissions WHERE status = ?",
            (SUBMISSION_PENDING,),
        ).fetchone()
    return row["n"]
