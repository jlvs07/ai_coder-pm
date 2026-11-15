from __future__ import annotations

import copy
import logging
from uuid import uuid4

from app.ai_actions import (
    AIResponseError,
    BoardUpdate,
    CardCreate,
    CardDelete,
    CardEdit,
    CardMove,
    ColumnRename,
)
from app.boards import BoardNotFoundError, read_board
from app.database import connect_database

logger = logging.getLogger(__name__)


def apply_board_update(username: str, update: BoardUpdate) -> dict:
    with connect_database() as connection:
        board_result = read_board(connection, username)
        if board_result is None:
            raise BoardNotFoundError
        board_id, current_board = board_result
        next_board = copy.deepcopy(current_board)
        created_card_ids: set[str] = set()

        try:
            for action in update.actions:
                if isinstance(action, ColumnRename):
                    column = next(
                        (
                            item
                            for item in next_board["columns"]
                            if item["id"] == action.column_id
                        ),
                        None,
                    )
                    if column is None:
                        raise ValueError("unknown column")
                    column["title"] = action.title
                elif isinstance(action, CardCreate):
                    column = _find_column(next_board, action.column_id)
                    card_id = f"card-{uuid4().hex}"
                    next_board["cards"][card_id] = {
                        "id": card_id,
                        "title": action.title,
                        "details": action.details,
                    }
                    column["cardIds"].append(card_id)
                    created_card_ids.add(card_id)
                elif isinstance(action, CardEdit):
                    card = next_board["cards"].get(action.card_id)
                    if card is None:
                        raise ValueError("unknown card")
                    if action.title is not None:
                        card["title"] = action.title
                    if action.details is not None:
                        card["details"] = action.details
                elif isinstance(action, CardMove):
                    destination = _find_column(next_board, action.column_id)
                    source = _find_card_column(next_board, action.card_id)
                    source["cardIds"].remove(action.card_id)
                    position = (
                        len(destination["cardIds"])
                        if action.position is None
                        else action.position
                    )
                    if position > len(destination["cardIds"]):
                        raise ValueError("invalid card position")
                    destination["cardIds"].insert(position, action.card_id)
                elif isinstance(action, CardDelete):
                    _find_card_column(next_board, action.card_id)[
                        "cardIds"
                    ].remove(action.card_id)
                    del next_board["cards"][action.card_id]
        except ValueError as error:
            logger.warning("OpenRouter proposed an invalid board update")
            raise AIResponseError("AI proposed an invalid board update") from error

        card_rows = connection.execute(
            """
            SELECT cards.id, cards.position
            FROM cards
            JOIN columns ON columns.id = cards.column_id
            WHERE columns.board_id = ?
            """,
            (board_id,),
        ).fetchall()
        max_position = max((card["position"] for card in card_rows), default=0)
        offset = len(card_rows) + max_position + 1
        connection.execute(
            """
            UPDATE cards
            SET position = position + ?
            WHERE column_id IN (SELECT id FROM columns WHERE board_id = ?)
            """,
            (offset, board_id),
        )

        surviving_ids = set(next_board["cards"])
        for card in card_rows:
            if card["id"] not in surviving_ids:
                connection.execute("DELETE FROM cards WHERE id = ?", (card["id"],))

        temporary_position = offset + max_position + 1
        for card_id in created_card_ids:
            card = next_board["cards"][card_id]
            column_id = _find_card_column(next_board, card_id)["id"]
            connection.execute(
                """
                INSERT INTO cards (id, column_id, title, details, position)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    card_id,
                    column_id,
                    card["title"],
                    card["details"],
                    temporary_position,
                ),
            )
            temporary_position += 1

        for card_id, card in next_board["cards"].items():
            column = _find_card_column(next_board, card_id)
            position = column["cardIds"].index(card_id)
            connection.execute(
                """
                UPDATE cards
                SET column_id = ?, title = ?, details = ?, position = ?
                WHERE id = ?
                """,
                (
                    column["id"],
                    card["title"],
                    card["details"],
                    position,
                    card_id,
                ),
            )

        for column in next_board["columns"]:
            connection.execute(
                "UPDATE columns SET title = ? WHERE id = ? AND board_id = ?",
                (column["title"], column["id"], board_id),
            )

    return next_board


def _find_column(board: dict, column_id: str) -> dict:
    column = next(
        (item for item in board["columns"] if item["id"] == column_id),
        None,
    )
    if column is None:
        raise ValueError("unknown column")
    return column


def _find_card_column(board: dict, card_id: str) -> dict:
    for column in board["columns"]:
        if card_id in column["cardIds"]:
            return column
    raise ValueError("unknown card")
