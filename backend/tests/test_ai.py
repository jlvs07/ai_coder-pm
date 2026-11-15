from __future__ import annotations

import json
from urllib.error import HTTPError, URLError

import pytest

from app import openrouter


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
        "messages": [{
            "role": "user",
            "content": "What is 2 + 2? Reply with only the number.",
        }],
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


def test_board_chat_sends_context_and_applies_valid_actions(client, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    captured = {}
    completion = json.dumps(
        {
            "reply": "I updated the board.",
            "board_update": {
                "actions": [
                    {
                        "type": "rename_column",
                        "column_id": "col-backlog",
                        "title": "Inbox",
                    },
                    {
                        "type": "update_card",
                        "card_id": "card-1",
                        "title": "Updated roadmap",
                    },
                    {
                        "type": "move_card",
                        "card_id": "card-2",
                        "column_id": "col-review",
                        "position": 1,
                    },
                    {"type": "delete_card", "card_id": "card-3"},
                    {
                        "type": "create_card",
                        "column_id": "col-backlog",
                        "title": "New task",
                        "details": "Created by the assistant",
                    },
                ]
            },
        }
    )

    def fake_completion(api_key, messages):
        captured["api_key"] = api_key
        captured["messages"] = messages
        return completion

    monkeypatch.setattr("app.api.ai.request_completion", fake_completion)

    response = client.post(
        "/api/boards/usuario/chat",
        json={
            "message": "Create a task and update the board.",
            "history": [
                {"role": "user", "content": "Earlier request"},
                {"role": "assistant", "content": "Earlier reply"},
            ],
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["reply"] == "I updated the board."
    assert result["board"]["columns"][0]["title"] == "Inbox"
    assert result["board"]["columns"][0]["cardIds"][-1] in result["board"]["cards"]
    new_card_id = result["board"]["columns"][0]["cardIds"][-1]
    assert result["board"]["cards"][new_card_id] == {
        "id": new_card_id,
        "title": "New task",
        "details": "Created by the assistant",
    }
    assert result["board"]["cards"]["card-1"]["title"] == "Updated roadmap"
    assert result["board"]["cards"].get("card-3") is None
    assert result["board"]["columns"][1]["cardIds"] == []
    assert result["board"]["columns"][3]["cardIds"] == ["card-6", "card-2"]

    messages = captured["messages"]
    assert messages[0]["role"] == "system"
    assert '"Align roadmap themes"' in messages[0]["content"]
    assert messages[1:] == [
        {"role": "user", "content": "Earlier request"},
        {"role": "assistant", "content": "Earlier reply"},
        {
            "role": "user",
            "content": "Create a task and update the board.",
        },
    ]
    persisted_board = client.get("/api/boards/usuario").json()
    assert persisted_board == result["board"]


@pytest.mark.parametrize(
    "completion",
    [
        "not JSON",
        json.dumps(
            {
                "reply": "Done",
                "board_update": {
                    "actions": [
                        {
                            "type": "rename_column",
                            "column_id": "col-backlog",
                            "title": "Would be a partial change",
                        },
                        {
                            "type": "rename_column",
                            "column_id": "missing",
                            "title": "Oops",
                        },
                    ]
                },
            }
        ),
    ],
)
def test_board_chat_rejects_invalid_ai_output_without_mutating_board(
    client, monkeypatch, completion
):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    original_board = client.get("/api/boards/usuario").json()
    monkeypatch.setattr(
        "app.api.ai.request_completion",
        lambda api_key, messages: completion,
    )

    response = client.post(
        "/api/boards/usuario/chat",
        json={"message": "Make a change."},
    )

    assert response.status_code == 502
    assert client.get("/api/boards/usuario").json() == original_board


def test_board_chat_returns_text_without_board_update(client, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.api.ai.request_completion",
        lambda api_key, messages: json.dumps(
            {"reply": "The board looks good.", "board_update": None}
        ),
    )

    response = client.post(
        "/api/boards/usuario/chat",
        json={"message": "Any suggestions?"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "The board looks good.",
        "board": None,
    }


def test_board_chat_rejects_invalid_request_without_calling_model(
    client, monkeypatch
):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def unexpected_call(*args, **kwargs):
        pytest.fail("OpenRouter must not be called for invalid requests")

    monkeypatch.setattr("app.api.ai.request_completion", unexpected_call)

    response = client.post(
        "/api/boards/usuario/chat",
        json={"message": "  "},
    )

    assert response.status_code == 422
