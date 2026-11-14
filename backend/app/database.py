from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DEFAULT_USER = ("user-demo", "usuario")
DEFAULT_BOARD = ("board-demo", "Kanban Studio")
DEFAULT_COLUMNS = [
    ("col-backlog", "Backlog", 0),
    ("col-discovery", "Discovery", 1),
    ("col-progress", "In Progress", 2),
    ("col-review", "Review", 3),
    ("col-done", "Done", 4),
]
DEFAULT_CARDS = [
    (
        "card-1",
        "col-backlog",
        "Align roadmap themes",
        "Draft quarterly themes with impact statements and metrics.",
        0,
    ),
    (
        "card-2",
        "col-backlog",
        "Gather customer signals",
        "Review support tags, sales notes, and churn feedback.",
        1,
    ),
    (
        "card-3",
        "col-discovery",
        "Prototype analytics view",
        "Sketch initial dashboard layout and key drill-downs.",
        0,
    ),
    (
        "card-4",
        "col-progress",
        "Refine status language",
        "Standardize column labels and tone across the board.",
        0,
    ),
    (
        "card-5",
        "col-progress",
        "Design card layout",
        "Add hierarchy and spacing for scanning dense lists.",
        1,
    ),
    (
        "card-6",
        "col-review",
        "QA micro-interactions",
        "Verify hover, focus, and loading states.",
        0,
    ),
    (
        "card-7",
        "col-done",
        "Ship marketing page",
        "Final copy approved and asset pack delivered.",
        0,
    ),
    (
        "card-8",
        "col-done",
        "Close onboarding sprint",
        "Document release notes and share internally.",
        1,
    ),
]


def database_path() -> Path:
    configured_path = os.environ.get("DATABASE_PATH")
    if configured_path:
        return Path(configured_path)
    return Path(__file__).resolve().parents[1] / "data" / "kanban.db"


@contextmanager
def connect_database() -> Iterator[sqlite3.Connection]:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    with connect_database() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY NOT NULL,
                username TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS boards (
                id TEXT PRIMARY KEY NOT NULL,
                user_id TEXT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL DEFAULT 'Kanban Studio',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS columns (
                id TEXT PRIMARY KEY NOT NULL,
                board_id TEXT NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                position INTEGER NOT NULL CHECK(position >= 0),
                UNIQUE(board_id, position)
            );

            CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY NOT NULL,
                column_id TEXT NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL CHECK(position >= 0),
                UNIQUE(column_id, position)
            );
            """
        )
        connection.execute(
            "INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)",
            DEFAULT_USER,
        )
        user = connection.execute(
            "SELECT id FROM users WHERE username = ?", (DEFAULT_USER[1],)
        ).fetchone()
        connection.execute(
            "INSERT OR IGNORE INTO boards (id, user_id, title) VALUES (?, ?, ?)",
            (DEFAULT_BOARD[0], user["id"], DEFAULT_BOARD[1]),
        )
        board = connection.execute(
            "SELECT id FROM boards WHERE user_id = ?", (user["id"],)
        ).fetchone()
        if connection.execute(
            "SELECT 1 FROM columns WHERE board_id = ? LIMIT 1", (board["id"],)
        ).fetchone():
            return

        connection.executemany(
            "INSERT INTO columns (id, board_id, title, position) VALUES (?, ?, ?, ?)",
            [
                (column_id, board["id"], title, position)
                for column_id, title, position in DEFAULT_COLUMNS
            ],
        )
        connection.executemany(
            """
            INSERT INTO cards (id, column_id, title, details, position)
            VALUES (?, ?, ?, ?, ?)
            """,
            DEFAULT_CARDS,
        )
