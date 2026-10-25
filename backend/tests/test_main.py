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


def test_chat_catalog_endpoint_exposes_only_mutual_nda() -> None:
    with TestClient(app) as client:
        response = client.get("/api/documents")

    assert response.status_code == 200
    assert [document["id"] for document in response.json()] == ["mutual-nda"]


def test_chat_requires_explicit_ai_disclosure() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "I need an NDA"}], "consent": False},
        )

    assert response.status_code == 400


def test_chat_uses_structured_intake_and_restricts_values(monkeypatch) -> None:
    async def fake_intake(messages, context):
        assert [document["id"] for document in context["catalog"]] == ["mutual-nda"]
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


def test_render_endpoint_returns_mutual_nda_with_values() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/mutual-nda/render",
            json={
                "field_values": {
                    "party_1": "Acme",
                    "party_2": "Prelegal",
                    "purpose": "Evaluate a partnership",
                    "effective_date": "October 24, 2026",
                    "governing_law": "California",
                    "jurisdiction": "San Francisco, California",
                }
            },
        )

    assert response.status_code == 200
    assert "Acme" in response.json()["html"]
    assert response.json()["missing_companions"] == []


def test_chat_and_render_reject_all_non_nda_documents() -> None:
    with TestClient(app) as client:
        for document in main.documents.list_documents():
            if document["id"] == "mutual-nda":
                continue
            chat_response = client.post(
                "/api/chat",
                json={
                    "messages": [{"role": "user", "content": f"Create a {document['title']}"}],
                    "document_id": document["id"],
                    "consent": True,
                },
            )
            render_response = client.post(
                f"/api/documents/{document['id']}/render",
                json={"field_values": {}},
            )

            assert chat_response.status_code == 404
            assert render_response.status_code == 404


def test_unsupported_request_suggests_only_a_catalog_document(monkeypatch) -> None:
    async def fake_intake(messages, context):
        return {
            "action": "unsupported",
            "document_id": None,
            "message": "This request is not supported by a template.",
            "suggested_document_id": "mutual-nda",
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
    assert response.json()["suggested_document_id"] == "mutual-nda"
