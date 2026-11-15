from __future__ import annotations

import sqlite3
from uuid import uuid4

from app.database import connect_database


class BoardNotFoundError(Exception):
    pass


class ColumnNotFoundError(Exception):
    pass


class CardNotFoundError(Exception):
    pass


class BoardOrderError(Exception):
    pass


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


def get_board(username: str) -> dict | None:
    with connect_database() as connection:
        result = read_board(connection, username)
    return result[1] if result else None


def create_card(
    username: str, column_id: str, title: str, details: str
) -> dict:
    with connect_database() as connection:
        column = connection.execute(
            """
            SELECT columns.id
            FROM columns
            JOIN boards ON boards.id = columns.board_id
            JOIN users ON users.id = boards.user_id
            WHERE users.username = ? AND columns.id = ?
            """,
            (username, column_id),
        ).fetchone()
        if column is None:
            raise ColumnNotFoundError

        card = {
            "id": f"card-{uuid4().hex}",
            "title": title,
            "details": details,
        }
        position = connection.execute(
            "SELECT COALESCE(MAX(position), -1) + 1 FROM cards WHERE column_id = ?",
            (column_id,),
        ).fetchone()[0]
        connection.execute(
            """
            INSERT INTO cards (id, column_id, title, details, position)
            VALUES (?, ?, ?, ?, ?)
            """,
            (card["id"], column_id, card["title"], card["details"], position),
        )
    return card


def update_card(
    username: str,
    card_id: str,
    title: str | None,
    details: str | None,
) -> dict:
    with connect_database() as connection:
        card = connection.execute(
            """
            SELECT cards.id, cards.title, cards.details
            FROM cards
            JOIN columns ON columns.id = cards.column_id
            JOIN boards ON boards.id = columns.board_id
            JOIN users ON users.id = boards.user_id
            WHERE users.username = ? AND cards.id = ?
            """,
            (username, card_id),
        ).fetchone()
        if card is None:
            raise CardNotFoundError

        next_title = title if title is not None else card["title"]
        next_details = details if details is not None else card["details"]
        connection.execute(
            "UPDATE cards SET title = ?, details = ? WHERE id = ?",
            (next_title, next_details, card_id),
        )
    return {"id": card_id, "title": next_title, "details": next_details}


def delete_card(username: str, card_id: str) -> None:
    with connect_database() as connection:
        card = connection.execute(
            """
            SELECT cards.id, cards.column_id, cards.position
            FROM cards
            JOIN columns ON columns.id = cards.column_id
            JOIN boards ON boards.id = columns.board_id
            JOIN users ON users.id = boards.user_id
            WHERE users.username = ? AND cards.id = ?
            """,
            (username, card_id),
        ).fetchone()
        if card is None:
            raise CardNotFoundError

        max_position = connection.execute(
            "SELECT COALESCE(MAX(position), 0) FROM cards WHERE column_id = ?",
            (card["column_id"],),
        ).fetchone()[0]
        offset = max_position + 1
        connection.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        connection.execute(
            """
            UPDATE cards SET position = position + ?
            WHERE column_id = ? AND position > ?
            """,
            (offset, card["column_id"], card["position"]),
        )
        connection.execute(
            """
            UPDATE cards SET position = position - ?
            WHERE column_id = ? AND position >= ?
            """,
            (offset + 1, card["column_id"], offset),
        )


def rename_column(username: str, column_id: str, title: str) -> dict:
    with connect_database() as connection:
        result = connection.execute(
            """
            UPDATE columns
            SET title = ?
            WHERE id = ? AND board_id = (
                SELECT boards.id
                FROM boards
                JOIN users ON users.id = boards.user_id
                WHERE users.username = ?
            )
            """,
            (title, column_id, username),
        )
        if result.rowcount == 0:
            raise ColumnNotFoundError
    return {"id": column_id, "title": title}


def reorder_cards(
    username: str, columns: list[tuple[str, list[str]]]
) -> None:
    with connect_database() as connection:
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
            raise BoardNotFoundError

        current_columns = connection.execute(
            "SELECT id FROM columns WHERE board_id = ?", (board["id"],)
        ).fetchall()
        expected_column_ids = {column["id"] for column in current_columns}
        provided_column_ids = [column_id for column_id, _ in columns]
        if (
            len(provided_column_ids) != len(set(provided_column_ids))
            or set(provided_column_ids) != expected_column_ids
        ):
            raise BoardOrderError(
                "Order must include every board column exactly once"
            )

        card_rows = connection.execute(
            """
            SELECT cards.id, cards.position
            FROM cards
            JOIN columns ON columns.id = cards.column_id
            WHERE columns.board_id = ?
            """,
            (board["id"],),
        ).fetchall()
        current_card_ids = {card["id"] for card in card_rows}
        provided_card_ids = [
            card_id for _, card_ids in columns for card_id in card_ids
        ]
        if (
            len(provided_card_ids) != len(set(provided_card_ids))
            or set(provided_card_ids) != current_card_ids
        ):
            raise BoardOrderError(
                "Order must include every board card exactly once"
            )

        offset = len(card_rows) + max(
            (card["position"] for card in card_rows), default=0
        ) + 1
        connection.execute(
            """
            UPDATE cards
            SET position = position + ?
            WHERE column_id IN (SELECT id FROM columns WHERE board_id = ?)
            """,
            (offset, board["id"]),
        )
        for column_id, card_ids in columns:
            for position, card_id in enumerate(card_ids):
                connection.execute(
                    "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
                    (column_id, position, card_id),
                )
