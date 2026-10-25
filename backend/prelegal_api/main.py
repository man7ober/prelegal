import json
import os
import re
import secrets
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.sessions import SessionMiddleware

from .auth import hash_password, require_user, verify_password
from .database import database_connection, initialize_database
from .documents import DocumentLibrary
from .openrouter import OpenRouterError, request_intake
from .schemas import SUPPORTED_CHAT_DOCUMENT_IDS


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


project_root = Path(
    os.environ.get("PRELEGAL_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
)
documents = DocumentLibrary(project_root)

app = FastAPI(title="Prelegal API", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET_KEY") or secrets.token_urlsafe(32),
    session_cookie="prelegal_session",
    max_age=60 * 60 * 24 * 7,
    same_site="lax",
    https_only=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=16)
    document_id: str | None = None
    field_values: dict[str, str] = Field(default_factory=dict)
    consent: bool


class RenderRequest(BaseModel):
    field_values: dict[str, str] = Field(default_factory=dict)


class EmailRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Enter a valid email address.")
        return email


class SignupRequest(EmailRequest):
    password: str = Field(min_length=8, max_length=128)


class SigninRequest(EmailRequest):
    password: str = Field(min_length=1, max_length=128)


class SaveDocumentRequest(BaseModel):
    field_values: dict[str, str] = Field(min_length=1)

    @field_validator("field_values")
    @classmethod
    def validate_field_values(cls, values: dict[str, str]) -> dict[str, str]:
        if any(len(value) > 2000 for value in values.values()):
            raise ValueError("Field values must be 2000 characters or fewer.")
        return values


@app.post("/api/auth/signup", status_code=201)
def signup(request: SignupRequest, response_request: Request) -> dict:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with database_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO users(email, password_hash, created_at) VALUES (?, ?, ?)",
                (request.email, hash_password(request.password), created_at),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="An account with that email already exists.") from error

    response_request.session.clear()
    response_request.session["user_id"] = user_id
    return {"id": user_id, "email": request.email}


@app.post("/api/auth/signin")
def signin(request: SigninRequest, response_request: Request) -> dict:
    with database_connection() as connection:
        user = connection.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (request.email,),
        ).fetchone()

    stored_hash = user["password_hash"] if user else None
    if not verify_password(request.password, stored_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")

    response_request.session.clear()
    response_request.session["user_id"] = user["id"]
    return {"id": user["id"], "email": user["email"]}


@app.post("/api/auth/logout")
def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"signed_out": True}


@app.get("/api/auth/me")
def current_user(user: dict = Depends(require_user)) -> dict:
    return user


@app.get("/api/templates")
def list_templates(_: dict = Depends(require_user)) -> list[dict]:
    return [
        document
        for document in documents.list_documents()
        if document["id"] in SUPPORTED_CHAT_DOCUMENT_IDS
    ]


@app.get("/api/documents")
def list_saved_documents(user: dict = Depends(require_user)) -> list[dict]:
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, created_at, updated_at FROM documents "
            "WHERE user_id = ? ORDER BY updated_at DESC",
            (user["id"],),
        ).fetchall()
    return [dict(row) for row in rows]


def _clean_nda_fields(field_values: dict[str, str]) -> dict[str, str]:
    allowed_fields = {
        field["id"]
        for field in documents.chat_context("mutual-nda")["selected_document"]["fields"]
    }
    if set(field_values) - allowed_fields:
        raise HTTPException(status_code=422, detail="Unknown fields were supplied for this agreement.")
    return {key: value.strip() for key, value in field_values.items()}


def _document_title(field_values: dict[str, str]) -> str:
    parties = [field_values.get("party_1", "").strip(), field_values.get("party_2", "").strip()]
    names = " and ".join(name for name in parties if name)
    return f"Mutual NDA — {names}" if names else "Mutual NDA Draft"


def _read_saved_document(document_id: str, user_id: int) -> dict:
    with database_connection() as connection:
        row = connection.execute(
            "SELECT id, title, field_values, created_at, updated_at FROM documents "
            "WHERE id = ? AND user_id = ?",
            (document_id, user_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "id": row["id"],
        "title": row["title"],
        "field_values": json.loads(row["field_values"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@app.post("/api/documents", status_code=201)
def save_document(request: SaveDocumentRequest, user: dict = Depends(require_user)) -> dict:
    field_values = _clean_nda_fields(request.field_values)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    document_id = str(uuid4())
    title = _document_title(field_values)
    with database_connection() as connection:
        connection.execute(
            "INSERT INTO documents(id, user_id, title, field_values, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (document_id, user["id"], title, json.dumps(field_values), now, now),
        )
    return _read_saved_document(document_id, user["id"])


@app.get("/api/documents/{document_id}")
def get_saved_document(document_id: str, user: dict = Depends(require_user)) -> dict:
    return _read_saved_document(document_id, user["id"])


@app.put("/api/documents/{document_id}")
def update_saved_document(
    document_id: str,
    request: SaveDocumentRequest,
    user: dict = Depends(require_user),
) -> dict:
    field_values = _clean_nda_fields(request.field_values)
    title = _document_title(field_values)
    updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with database_connection() as connection:
        cursor = connection.execute(
            "UPDATE documents SET title = ?, field_values = ?, updated_at = ? "
            "WHERE id = ? AND user_id = ?",
            (title, json.dumps(field_values), updated_at, document_id, user["id"]),
        )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Document not found.")
    return _read_saved_document(document_id, user["id"])


@app.post("/api/chat")
async def chat(request: ChatRequest, _: dict = Depends(require_user)) -> dict:
    if not request.consent:
        raise HTTPException(status_code=400, detail="Consent is required before sending messages to the AI service.")
    if not any(message.role == "user" for message in request.messages):
        raise HTTPException(status_code=422, detail="At least one user message is required.")
    if request.document_id and request.document_id not in SUPPORTED_CHAT_DOCUMENT_IDS:
        raise HTTPException(status_code=404, detail="The selected agreement is not supported.")

    context = documents.chat_context(request.document_id)
    context["catalog"] = [
        item for item in context["catalog"] if item["id"] in SUPPORTED_CHAT_DOCUMENT_IDS
    ]
    if request.document_id:
        field_ids = {field["id"] for field in context["selected_document"]["fields"]}
        unknown_fields = set(request.field_values) - field_ids
        if unknown_fields:
            raise HTTPException(status_code=422, detail="Unknown fields were supplied for this agreement.")
        required = set(context["selected_document"]["required_fields"])
        context["current_values"] = request.field_values
        context["required_fields_missing"] = sorted(required - set(request.field_values))

    try:
        result = await request_intake(
            [message.model_dump() for message in request.messages], context
        )
    except OpenRouterError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    result_document_id = result.get("document_id")
    if result_document_id not in SUPPORTED_CHAT_DOCUMENT_IDS:
        result_document_id = request.document_id
    if result_document_id:
        field_ids = {
            field["id"] for field in documents.chat_context(result_document_id)["selected_document"]["fields"]
        }
        values = {
            key: value.strip()
            for key, value in request.field_values.items()
            if key in field_ids and value.strip()
        }
        for update in result.get("field_updates", []):
            key, value = update.get("id"), update.get("value", "")
            if key in field_ids and isinstance(value, str) and value.strip():
                values[key] = value.strip()
        config = documents.by_id[result_document_id]["config"]
        required_missing = set(config.required_fields) - set(values)
        action = result.get("action", "ask")
        message = result.get("message", "")
        if action == "ready" and required_missing:
            action = "ask"
            labels = {
                field["id"]: field["label"]
                for field in documents.chat_context(result_document_id)["selected_document"]["fields"]
            }
            message = "I still need: " + ", ".join(labels.get(key, key) for key in sorted(required_missing)) + "."
        return {
            "action": action,
            "document_id": result_document_id,
            "message": message,
            "suggested_document_id": result.get("suggested_document_id")
            if result.get("suggested_document_id") in SUPPORTED_CHAT_DOCUMENT_IDS
            else None,
            "field_values": values,
            "required_missing": sorted(required_missing),
        }

    suggestion = result.get("suggested_document_id")
    return {
        "action": "unsupported" if result.get("action") == "unsupported" else "ask",
        "document_id": None,
        "message": result.get("message", "Tell me a little more about the agreement you need."),
        "suggested_document_id": suggestion if suggestion in SUPPORTED_CHAT_DOCUMENT_IDS else None,
        "field_values": {},
        "required_missing": [],
    }


@app.post("/api/documents/{document_id}/render")
def render_document(
    document_id: str,
    request: RenderRequest,
    _: dict = Depends(require_user),
) -> dict:
    if document_id not in SUPPORTED_CHAT_DOCUMENT_IDS:
        raise HTTPException(status_code=404, detail="The selected agreement is not supported.")
    field_ids = {
        field["id"] for field in documents.chat_context(document_id)["selected_document"]["fields"]
    }
    if set(request.field_values) - field_ids:
        raise HTTPException(status_code=422, detail="Unknown fields were supplied for this agreement.")
    return documents.render(document_id, request.field_values)
