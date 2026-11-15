from __future__ import annotations


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
    assert (
        client.post(
            "/api/boards/usuario/columns/col-backlog/cards",
            json={"title": "x" * 201},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/boards/usuario/columns/col-backlog/cards",
            json={"title": "Card", "details": "x" * 4001},
        ).status_code
        == 422
    )
    assert (
        client.patch(
            "/api/boards/usuario/columns/col-backlog",
            json={"title": "x" * 121},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/boards/usuario/columns/col-backlog/cards",
            json={"title": "Card", "unexpected": True},
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
