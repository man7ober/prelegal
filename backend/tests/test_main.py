import sqlite3

from fastapi.testclient import TestClient

from prelegal_api import main
from prelegal_api.database import database_path
from prelegal_api.main import app


def create_account(client: TestClient, email: str = "reader@example.test") -> str:
    response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "example-pass-123"},
    )
    assert response.status_code == 201
    return response.json()["email"]


def test_health_endpoint(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRELEGAL_DATABASE_PATH", str(tmp_path / "prelegal.db"))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_startup_creates_schema_and_resets_existing_data(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "nested" / "prelegal.db"
    database_path.parent.mkdir(parents=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute("CREATE TABLE stale_data (value TEXT)")
        connection.execute("INSERT INTO stale_data VALUES ('old')")
    monkeypatch.setenv("PRELEGAL_DATABASE_PATH", str(database_path))

    with TestClient(app):
        assert database_path.is_file()

    with sqlite3.connect(database_path) as connection:
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        document_count = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    assert {table[0] for table in tables if not table[0].startswith("sqlite_")} == {"users", "documents"}
    assert user_count == 0
    assert document_count == 0


def test_chat_catalog_endpoint_exposes_only_mutual_nda() -> None:
    with TestClient(app) as client:
        create_account(client)
        response = client.get("/api/templates")

    assert response.status_code == 200
    assert [document["id"] for document in response.json()] == ["mutual-nda"]


def test_chat_requires_explicit_ai_disclosure() -> None:
    with TestClient(app) as client:
        create_account(client)
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
        create_account(client)
        response = client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "I need an NDA"}], "consent": True},
        )

    assert response.status_code == 200
    assert response.json()["action"] == "ready"
    assert "not_a_field" not in response.json()["field_values"]


def test_render_endpoint_returns_mutual_nda_with_values() -> None:
    with TestClient(app) as client:
        create_account(client)
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
        create_account(client)
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
        create_account(client)
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


def test_signup_signin_and_logout_use_hashed_password_and_http_only_cookie() -> None:
    password = "example-pass-123"
    with TestClient(app) as client:
        signup = client.post(
            "/api/auth/signup",
            json={"email": " User@Example.Test ", "password": password},
        )
        assert signup.status_code == 201
        assert signup.json()["email"] == "user@example.test"
        assert "httponly" in signup.headers["set-cookie"].lower()
        assert client.get("/api/auth/me").json()["email"] == "user@example.test"

        with sqlite3.connect(database_path()) as connection:
            stored_hash = connection.execute(
                "SELECT password_hash FROM users WHERE email = ?",
                ("user@example.test",),
            ).fetchone()[0]
        assert stored_hash != password

        duplicate = client.post(
            "/api/auth/signup",
            json={"email": "user@example.test", "password": password},
        )
        assert duplicate.status_code == 409
        assert client.post(
            "/api/auth/signin",
            json={"email": "user@example.test", "password": "wrong-password"},
        ).status_code == 401
        assert client.post(
            "/api/auth/signin",
            json={"email": "user@example.test", "password": password},
        ).status_code == 200
        assert client.post("/api/auth/logout").status_code == 200
        assert client.get("/api/auth/me").status_code == 401


def test_saved_documents_are_scoped_to_the_signed_in_user() -> None:
    field_values = {
        "party_1": "Example One",
        "party_2": "Example Two",
        "purpose": "Evaluate a business relationship",
        "effective_date": "October 25, 2026",
        "governing_law": "California",
        "jurisdiction": "San Francisco, California",
    }
    with TestClient(app) as client:
        create_account(client, "first@example.test")
        saved = client.post("/api/documents", json={"field_values": field_values})
        assert saved.status_code == 201
        document_id = saved.json()["id"]
        assert client.get("/api/documents").json()[0]["id"] == document_id
        assert client.get(f"/api/documents/{document_id}").json()["field_values"] == field_values

        updated_values = {**field_values, "purpose": "Evaluate a pilot"}
        updated = client.put(
            f"/api/documents/{document_id}",
            json={"field_values": updated_values},
        )
        assert updated.status_code == 200
        assert updated.json()["field_values"] == updated_values

        client.cookies.clear()
        create_account(client, "second@example.test")
        assert client.get("/api/documents").json() == []
        assert client.get(f"/api/documents/{document_id}").status_code == 404
        assert client.put(
            f"/api/documents/{document_id}",
            json={"field_values": updated_values},
        ).status_code == 404


def test_protected_endpoints_require_a_session() -> None:
    with TestClient(app) as client:
        assert client.get("/api/templates").status_code == 401
        assert client.get("/api/documents").status_code == 401
        assert client.post(
            "/api/chat",
            json={"messages": [{"role": "user", "content": "Create an NDA"}], "consent": True},
        ).status_code == 401


def test_backend_restart_clears_accounts_and_saved_documents() -> None:
    field_values = {
        "party_1": "Example One",
        "party_2": "Example Two",
        "purpose": "Discuss a project",
        "effective_date": "October 25, 2026",
        "governing_law": "California",
        "jurisdiction": "San Francisco, California",
    }
    with TestClient(app) as client:
        create_account(client)
        saved = client.post("/api/documents", json={"field_values": field_values})
        assert saved.status_code == 201
        session_cookie = client.cookies.get("prelegal_session")

    with TestClient(app) as restarted_client:
        restarted_client.cookies.set("prelegal_session", session_cookie)
        assert restarted_client.get("/api/auth/me").status_code == 401
        assert restarted_client.post(
            "/api/auth/signin",
            json={"email": "reader@example.test", "password": "example-pass-123"},
        ).status_code == 401
