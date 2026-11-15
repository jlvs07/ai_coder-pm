from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from app import boards
from app.api.schemas import (
    BoardCardOrder,
    CardCreate,
    CardUpdate,
    ColumnUpdate,
)

router = APIRouter(prefix="/api/boards", tags=["boards"])


@router.get("/{username}")
def get_board(username: str) -> dict:
    board = boards.get_board(username)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@router.post("/{username}/columns/{column_id}/cards", status_code=201)
def create_card(
    username: str, column_id: str, payload: CardCreate
) -> dict:
    try:
        return boards.create_card(
            username, column_id, payload.title, payload.details
        )
    except boards.ColumnNotFoundError as error:
        raise HTTPException(status_code=404, detail="Column not found") from error


@router.patch("/{username}/cards/{card_id}")
def update_card(
    username: str, card_id: str, payload: CardUpdate
) -> dict:
    title = payload.title if "title" in payload.model_fields_set else None
    details = payload.details if "details" in payload.model_fields_set else None
    try:
        return boards.update_card(username, card_id, title, details)
    except boards.CardNotFoundError as error:
        raise HTTPException(status_code=404, detail="Card not found") from error


@router.delete("/{username}/cards/{card_id}", status_code=204)
def delete_card(username: str, card_id: str) -> Response:
    try:
        boards.delete_card(username, card_id)
    except boards.CardNotFoundError as error:
        raise HTTPException(status_code=404, detail="Card not found") from error
    return Response(status_code=204)


@router.patch("/{username}/columns/{column_id}")
def rename_column(
    username: str, column_id: str, payload: ColumnUpdate
) -> dict:
    try:
        return boards.rename_column(username, column_id, payload.title)
    except boards.ColumnNotFoundError as error:
        raise HTTPException(status_code=404, detail="Column not found") from error


@router.put("/{username}/cards/order")
def reorder_cards(username: str, payload: BoardCardOrder) -> dict:
    try:
        boards.reorder_cards(
            username,
            [
                (column.columnId, column.cardIds)
                for column in payload.columns
            ],
        )
    except boards.BoardNotFoundError as error:
        raise HTTPException(status_code=404, detail="Board not found") from error
    except boards.BoardOrderError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"status": "ok"}
