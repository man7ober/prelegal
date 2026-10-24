import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .documents import DocumentLibrary
from .openrouter import OpenRouterError, request_intake


def initialize_database() -> None:
    """Create an empty SQLite database file without adding product tables."""
    database_path = Path(os.environ.get("PRELEGAL_DATABASE_PATH", "data/prelegal.db"))
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA user_version = 0")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


project_root = Path(
    os.environ.get("PRELEGAL_PROJECT_ROOT", str(Path(__file__).resolve().parents[2]))
)
documents = DocumentLibrary(project_root)

app = FastAPI(title="Prelegal API", lifespan=lifespan)


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


@app.get("/api/documents")
def list_documents() -> list[dict]:
    return documents.list_documents()


@app.post("/api/chat")
async def chat(request: ChatRequest) -> dict:
    if not request.consent:
        raise HTTPException(status_code=400, detail="Consent is required before sending messages to the AI service.")
    if not any(message.role == "user" for message in request.messages):
        raise HTTPException(status_code=422, detail="At least one user message is required.")
    if request.document_id and request.document_id not in documents.by_id:
        raise HTTPException(status_code=404, detail="The selected agreement is not supported.")

    context = documents.chat_context(request.document_id)
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
    if result_document_id not in documents.by_id:
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
            if result.get("suggested_document_id") in documents.by_id
            else None,
            "field_values": values,
            "required_missing": sorted(required_missing),
        }

    suggestion = result.get("suggested_document_id")
    return {
        "action": "unsupported" if result.get("action") == "unsupported" else "ask",
        "document_id": None,
        "message": result.get("message", "Tell me a little more about the agreement you need."),
        "suggested_document_id": suggestion if suggestion in documents.by_id else None,
        "field_values": {},
        "required_missing": [],
    }


@app.post("/api/documents/{document_id}/render")
def render_document(document_id: str, request: RenderRequest) -> dict:
    if document_id not in documents.by_id:
        raise HTTPException(status_code=404, detail="The selected agreement is not supported.")
    field_ids = {
        field["id"] for field in documents.chat_context(document_id)["selected_document"]["fields"]
    }
    if set(request.field_values) - field_ids:
        raise HTTPException(status_code=422, detail="Unknown fields were supplied for this agreement.")
    return documents.render(document_id, request.field_values)
