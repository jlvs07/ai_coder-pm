from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    database_file = tmp_path / "kanban.db"
    monkeypatch.setenv("DATABASE_PATH", str(database_file))
    with TestClient(app) as test_client:
        yield test_client
    assert database_file.is_file()
