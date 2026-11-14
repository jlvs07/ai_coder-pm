from __future__ import annotations

import json
from urllib.error import HTTPError, URLError

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import openrouter


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_file = tmp_path / "kanban.db"
    monkeypatch.setenv("DATABASE_PATH", str(database_file))
    with TestClient(app) as test_client:
        yield test_client
    assert database_file.is_file()


def test_health_and_board_are_initialized(client):
    assert client.get("/health").json() == {
        "status": "ok",
        "service": "kanban-api",
    }

    response = client.get("/api/boards/usuario")
    assert response.status_code == 200
    board = response.json()
    assert [column["id"] for column in board["columns"]] == [
        "col-backlog",
        "col-discovery",
        "col-progress",
        "col-review",
        "col-done",
    ]
    assert board["columns"][0]["cardIds"] == ["card-1", "card-2"]
    assert board["cards"]["card-1"]["title"] == "Align roadmap themes"


def test_card_crud_and_column_rename_are_persisted(client):
    create_response = client.post(
        "/api/boards/usuario/columns/col-backlog/cards",
        json={"title": "  New card  ", "details": "Card details"},
    )
    assert create_response.status_code == 201
    card = create_response.json()
    assert card["title"] == "New card"

    update_response = client.patch(
        f"/api/boards/usuario/cards/{card['id']}",
        json={"title": "Updated card"},
    )
    assert update_response.json() == {
        "id": card["id"],
        "title": "Updated card",
        "details": "Card details",
    }
    client.patch(
        f"/api/boards/usuario/cards/{card['id']}",
        json={"details": "Updated details"},
    )

    rename_response = client.patch(
        "/api/boards/usuario/columns/col-backlog",
        json={"title": "Incoming"},
    )
    assert rename_response.json() == {"id": "col-backlog", "title": "Incoming"}

    board = client.get("/api/boards/usuario").json()
    assert board["columns"][0]["title"] == "Incoming"
    assert board["cards"][card["id"]]["details"] == "Updated details"

    delete_response = client.delete(f"/api/boards/usuario/cards/{card['id']}")
    assert delete_response.status_code == 204
    board = client.get("/api/boards/usuario").json()
    assert card["id"] not in board["cards"]
    assert card["id"] not in board["columns"][0]["cardIds"]
    assert client.delete("/api/boards/usuario/cards/card-1").status_code == 204
    board = client.get("/api/boards/usuario").json()
    assert board["columns"][0]["cardIds"] == ["card-2"]


def test_reorder_persists_card_moves_between_columns(client):
    response = client.put(
        "/api/boards/usuario/cards/order",
        json={
            "columns": [
                {"columnId": "col-backlog", "cardIds": ["card-2", "card-1"]},
                {"columnId": "col-discovery", "cardIds": ["card-3"]},
                {"columnId": "col-progress", "cardIds": ["card-4", "card-5"]},
                {"columnId": "col-review", "cardIds": ["card-6", "card-2"]},
                {"columnId": "col-done", "cardIds": ["card-7", "card-8"]},
            ]
        },
    )
    assert response.status_code == 422

    response = client.put(
        "/api/boards/usuario/cards/order",
        json={
            "columns": [
                {"columnId": "col-backlog", "cardIds": ["card-2"]},
                {"columnId": "col-discovery", "cardIds": ["card-3"]},
                {"columnId": "col-progress", "cardIds": ["card-4", "card-5"]},
                {"columnId": "col-review", "cardIds": ["card-6", "card-1"]},
                {"columnId": "col-done", "cardIds": ["card-7", "card-8"]},
            ]
        },
    )
    assert response.status_code == 200
    reordered = client.get("/api/boards/usuario").json()
    assert reordered["columns"][0]["cardIds"] == ["card-2"]
    assert reordered["columns"][3]["cardIds"] == ["card-6", "card-1"]


def test_unknown_resources_and_invalid_payloads_are_rejected(client):
    assert client.get("/api/boards/unknown").status_code == 404
    assert (
        client.post(
            "/api/boards/usuario/columns/not-a-column/cards",
            json={"title": "Card"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            "/api/boards/usuario/columns/col-backlog/cards",
            json={"title": "   "},
        ).status_code
        == 422
    )
    assert (
        client.patch("/api/boards/usuario/cards/card-1", json={}).status_code
        == 422
    )
    assert (
        client.patch(
            "/api/boards/usuario/cards/card-1", json={"details": None}
        ).status_code
        == 422
    )


def test_card_changes_survive_a_new_connection(client):
    created = client.post(
        "/api/boards/usuario/columns/col-backlog/cards",
        json={"title": "Persistent card"},
    ).json()

    response = client.get("/api/boards/usuario")
    assert response.json()["cards"][created["id"]]["title"] == "Persistent card"


def test_ai_connectivity_requires_api_key(client, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 503
    assert response.json()["detail"] == "OPENROUTER_API_KEY is not configured"


def test_ai_connectivity_uses_configured_model_and_returns_answer(
    client, monkeypatch
):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(
                {"choices": [{"message": {"content": "4"}}]}
            ).encode()

    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(openrouter, "urlopen", fake_urlopen)

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 200
    assert response.json() == {
        "model": "inclusionai/ling-3.2-flash:free",
        "answer": "4",
    }
    assert captured["request"].full_url == openrouter.OPENROUTER_URL
    assert captured["request"].get_header("Authorization").startswith("Bearer ")
    assert json.loads(captured["request"].data) == {
        "model": openrouter.MODEL,
        "messages": [
            {
                "role": "user",
                "content": "What is 2 + 2? Reply with only the number.",
            }
        ],
    }
    assert captured["timeout"] == openrouter.REQUEST_TIMEOUT_SECONDS


@pytest.mark.parametrize(
    ("urlopen_error", "expected_detail"),
    [
        (
            HTTPError(openrouter.OPENROUTER_URL, 429, "rate limited", {}, None),
            "OpenRouter returned HTTP 429",
        ),
        (
            URLError(TimeoutError()),
            "OpenRouter request timed out",
        ),
    ],
)
def test_ai_connectivity_reports_upstream_errors(
    client, monkeypatch, urlopen_error, expected_detail
):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def fail_urlopen(*args, **kwargs):
        raise urlopen_error

    monkeypatch.setattr(openrouter, "urlopen", fail_urlopen)

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 502
    assert response.json()["detail"] == expected_detail
    assert client.get("/api/boards/usuario").status_code == 200


def test_ai_connectivity_rejects_empty_response(client, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class EmptyResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":" "}}]}'

    monkeypatch.setattr(
        openrouter,
        "urlopen",
        lambda *args, **kwargs: EmptyResponse(),
    )

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 502
    assert response.json()["detail"] == "OpenRouter returned an empty response"
