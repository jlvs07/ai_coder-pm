from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator, model_validator

from app.database import connect_database, initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Kanban MVP API", version="0.1.0", lifespan=lifespan)
frontend_dir = Path(__file__).parent / "static"


class CardCreate(BaseModel):
    title: str = Field(min_length=1)
    details: str = ""

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class CardUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    details: str | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value

    @model_validator(mode="after")
    def require_a_change(self) -> CardUpdate:
        if not self.model_fields_set:
            raise ValueError("provide title or details to update")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("updated values cannot be null")
        return self


class ColumnUpdate(BaseModel):
    title: str = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class ColumnCardOrder(BaseModel):
    columnId: str
    cardIds: list[str]


class BoardCardOrder(BaseModel):
    columns: list[ColumnCardOrder]


@app.get("/health")
def healthcheck() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "kanban-api"})


@app.get("/api/hello")
def hello_api() -> JSONResponse:
    return JSONResponse({"message": "hello from the Kanban backend"})


@app.get("/api/boards/{username}")
def get_board(username: str) -> dict:
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
            raise HTTPException(status_code=404, detail="Board not found")

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

    return {
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


@app.post("/api/boards/{username}/columns/{column_id}/cards", status_code=201)
def create_card(username: str, column_id: str, payload: CardCreate) -> dict:
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
            raise HTTPException(status_code=404, detail="Column not found")

        card = {
            "id": f"card-{uuid4().hex}",
            "title": payload.title,
            "details": payload.details,
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


@app.patch("/api/boards/{username}/cards/{card_id}")
def update_card(username: str, card_id: str, payload: CardUpdate) -> dict:
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
            raise HTTPException(status_code=404, detail="Card not found")

        title = (
            payload.title
            if "title" in payload.model_fields_set
            else card["title"]
        )
        details = (
            payload.details
            if "details" in payload.model_fields_set
            else card["details"]
        )
        connection.execute(
            "UPDATE cards SET title = ?, details = ? WHERE id = ?",
            (title, details, card_id),
        )
    return {"id": card_id, "title": title, "details": details}


@app.delete("/api/boards/{username}/cards/{card_id}", status_code=204)
def delete_card(username: str, card_id: str) -> Response:
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
            raise HTTPException(status_code=404, detail="Card not found")

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
    return Response(status_code=204)


@app.patch("/api/boards/{username}/columns/{column_id}")
def rename_column(username: str, column_id: str, payload: ColumnUpdate) -> dict:
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
            (payload.title, column_id, username),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Column not found")
    return {"id": column_id, "title": payload.title}


@app.put("/api/boards/{username}/cards/order")
def reorder_cards(username: str, payload: BoardCardOrder) -> dict:
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
            raise HTTPException(status_code=404, detail="Board not found")

        current_columns = connection.execute(
            "SELECT id FROM columns WHERE board_id = ?", (board["id"],)
        ).fetchall()
        expected_column_ids = {column["id"] for column in current_columns}
        provided_column_ids = [column.columnId for column in payload.columns]
        if (
            len(provided_column_ids) != len(set(provided_column_ids))
            or set(provided_column_ids) != expected_column_ids
        ):
            raise HTTPException(
                status_code=422,
                detail="Order must include every board column exactly once",
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
            card_id for column in payload.columns for card_id in column.cardIds
        ]
        if (
            len(provided_card_ids) != len(set(provided_card_ids))
            or set(provided_card_ids) != current_card_ids
        ):
            raise HTTPException(
                status_code=422,
                detail="Order must include every board card exactly once",
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
        for column in payload.columns:
            for position, card_id in enumerate(column.cardIds):
                connection.execute(
                    "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
                    (column.columnId, position, card_id),
                )
    return {"status": "ok"}


if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:

    @app.get("/", response_class=HTMLResponse)
    def home_page() -> str:
        return """
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <title>Kanban MVP</title>
          </head>
          <body>
            <h1>Hello from Kanban MVP</h1>
            <p>The backend is running correctly.</p>
            <p>Use /health or /api/hello to verify the API.</p>
          </body>
        </html>
        """
