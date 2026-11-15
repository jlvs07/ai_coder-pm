from __future__ import annotations


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


def test_cors_allows_frontend_dev_origin(client):
    response = client.options(
        "/api/boards/usuario",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:3000"
    )
