import sqlite3

from fastapi.testclient import TestClient

from prelegal_api.main import app


def test_health_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRELEGAL_DATABASE_PATH", str(tmp_path / "prelegal.db"))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_creates_empty_database(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "nested" / "prelegal.db"
    monkeypatch.setenv("PRELEGAL_DATABASE_PATH", str(database_path))

    with TestClient(app):
        assert database_path.is_file()

    with sqlite3.connect(database_path) as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()

    assert tables == []
