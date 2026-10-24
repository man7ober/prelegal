import sqlite3

from fastapi.testclient import TestClient

from prelegal_api import main
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


def test_document_catalog_endpoint_returns_all_supported_types() -> None:
    with TestClient(app) as client:
        response = client.get("/api/documents")

    assert response.status_code == 200
    assert len(response.json()) == 11


def test_chat_requires_explicit_ai_disclosure() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "I need an NDA"}], "consent": False},
        )

    assert response.status_code == 400


def test_chat_uses_structured_intake_and_restricts_values(monkeypatch) -> None:
    async def fake_intake(messages, context):
        return {
            "action": "ready",
            "document_id": "mutual-nda",
            "message": "Your NDA draft is ready to review.",
            "suggested_document_id": None,
            "field_updates": [
                {"id": "party_1", "value": "Acme"},
                {"id": "party_2", "value": "Example Corp"},
                {"id": "purpose", "value": "Evaluate a partnership"},
                {"id": "effective_date", "value": "2026-10-24"},
                {"id": "governing_law", "value": "California"},
                {"id": "jurisdiction", "value": "San Francisco, California"},
                {"id": "not_a_field", "value": "ignored"},
            ],
        }

    monkeypatch.setattr(main, "request_intake", fake_intake)
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "I need an NDA"}], "consent": True},
        )

    assert response.status_code == 200
    assert response.json()["action"] == "ready"
    assert "not_a_field" not in response.json()["field_values"]


def test_render_endpoint_returns_completed_html_and_companion_warning() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/cloud-service-agreement/render",
            json={
                "field_values": {
                    "customer": "Acme",
                    "provider": "Prelegal",
                    "effective_date": "2026-10-24",
                    "governing_law": "California",
                }
            },
        )

    assert response.status_code == 200
    assert "Acme" in response.json()["html"]
    assert "Order Form" in response.json()["missing_companions"]


def test_unsupported_request_suggests_only_a_catalog_document(monkeypatch) -> None:
    async def fake_intake(messages, context):
        return {
            "action": "unsupported",
            "document_id": None,
            "message": "This request is not supported by a template.",
            "suggested_document_id": "pilot-agreement",
            "field_updates": [],
        }

    monkeypatch.setattr(main, "request_intake", fake_intake)
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={
                "messages": [{"role": "user", "content": "I need a residential lease."}],
                "consent": True,
            },
        )

    assert response.status_code == 200
    assert response.json()["action"] == "unsupported"
    assert response.json()["suggested_document_id"] == "pilot-agreement"
