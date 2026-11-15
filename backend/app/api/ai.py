from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException

from app import boards
from app.ai import build_chat_messages, parse_ai_response
from app.ai_actions import AIResponseError, BoardChatRequest
from app.board_updates import apply_board_update
from app.openrouter import MODEL, OpenRouterError, request_completion

router = APIRouter(tags=["ai"])


def _require_api_key() -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY is not configured",
        )
    return api_key


@router.post("/api/ai/connectivity")
def check_ai_connectivity() -> dict:
    api_key = _require_api_key()

    try:
        answer = request_completion(
            api_key,
            [
                {
                    "role": "user",
                    "content": "What is 2 + 2? Reply with only the number.",
                }
            ],
        )
    except OpenRouterError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return {"model": MODEL, "answer": answer}


@router.post("/api/boards/{username}/chat")
def board_chat(username: str, payload: BoardChatRequest) -> dict:
    api_key = _require_api_key()
    board = boards.get_board(username)
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")

    try:
        completion = request_completion(
            api_key,
            build_chat_messages(board, payload),
        )
        ai_response = parse_ai_response(completion)
    except OpenRouterError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except AIResponseError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    updated_board = None
    if ai_response.board_update and ai_response.board_update.actions:
        try:
            updated_board = apply_board_update(
                username,
                ai_response.board_update,
            )
        except boards.BoardNotFoundError as error:
            raise HTTPException(status_code=404, detail="Board not found") from error
        except AIResponseError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error

    return {"reply": ai_response.reply, "board": updated_board}
