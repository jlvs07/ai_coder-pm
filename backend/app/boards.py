from __future__ import annotations

import sqlite3


def read_board(
    connection: sqlite3.Connection, username: str
) -> tuple[str, dict] | None:
    board = connection.execute(
        """
        SELECT boards.id
        FROM boards
        JOIN users ON users.id = boards.user_id
        WHERE users.username = ?
        """,
        (username,),
    ).fetchone()
    if board is None:
        return None

    columns = connection.execute(
        """
        SELECT id, title
        FROM columns
        WHERE board_id = ?
        ORDER BY position
        """,
        (board["id"],),
    ).fetchall()
    cards = connection.execute(
        """
        SELECT cards.id, cards.title, cards.details, cards.column_id
        FROM cards
        JOIN columns ON columns.id = cards.column_id
        WHERE columns.board_id = ?
        ORDER BY columns.position, cards.position
        """,
        (board["id"],),
    ).fetchall()

    cards_by_id = {
        card["id"]: {
            "id": card["id"],
            "title": card["title"],
            "details": card["details"],
        }
        for card in cards
    }
    card_ids_by_column = {column["id"]: [] for column in columns}
    for card in cards:
        card_ids_by_column[card["column_id"]].append(card["id"])

    return board["id"], {
        "columns": [
            {
                "id": column["id"],
                "title": column["title"],
                "cardIds": card_ids_by_column[column["id"]],
            }
            for column in columns
        ],
        "cards": cards_by_id,
    }
