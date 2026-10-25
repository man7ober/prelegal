# Prelegal Project

## Overview

This project is intended to become a SaaS product for drafting legal agreements from templates in the templates directory. AI-assisted drafting and the catalog of planned documents are described in `catalog.json`.

@catalog.json

The current `main` branch provides an NDA-only AI chat workflow; other catalog templates remain in the repository but are not exposed by its chat or rendering APIs. Real authentication and document persistence are not implemented. See **Project status** below for scope.

## Development process

When instructed to build a feature:

1. Use your Atlassian tools to read the feature instructions from Jira
2. Develop the feature - do not skip any step from the feature-dev 7 step process
3. Thoroughly test the feature with unit tests and integration tests and fix any issues
4. Submit a PR using your github tools
5. When the implementation is complete and its PR is opened, transition the Jira issue to Done
6. Update **Project status** in this file to reflect the completed work

## AI design

When implementing LLM calls, use OpenRouter with the `nvidia/nemotron-3-ultra-550b-a55b:free` model and schema-constrained structured tool calls to populate legal-document fields. Validate model output before use. Configure credentials through environment variables; never commit or expose secret values.

## Technical design

Package the frontend and backend as separate Docker services orchestrated by root-level Docker Compose.
The backend is a `uv` project using FastAPI; the frontend is in `frontend/` and uses Next.js.
Use SQLite for the temporary backend database. It is initialized at backend startup, stored only in the container (no persistent volume), and currently has no application tables. Authentication and user storage are not implemented.

```bash
docker compose up -d --build    # Build
docker compose up -d            # Start
docker compose down             # Stop
```

Frontend available at http://localhost:3000; backend available at http://localhost:8000 (health check: `/health`).

## Current frontend colors

- Green: `#285b45`
- Dark green: `#1f4837`
- Lime accent: `#c4da83`
- Ink: `#19251f`
- Muted text: `#606d64`

## Project status

### KAN-7 — V1 foundation (Done; merged in PR #5)

- `/` is a demo-only entry screen; submitting the form navigates to `/workspace` without checking or sending credentials.
- FastAPI exposes `GET /health` and initializes an empty SQLite database at startup.
- Docker Compose runs the frontend and backend as separate services. The frontend is not served by FastAPI.
- Real authentication and user/document tables or persistence are not implemented.

### KAN-8 — Support all agreement types (Done; merged in PR #6)

- KAN-8 expanded the workflow to 11 catalogued agreement types, with source-template rendering, PDF downloads, and warnings for missing companion documents.

### KAN-9 — Mutual NDA AI chat (Done; merged in PR #7)

- The feature branch limits the chat and rendering APIs to Mutual NDA; other template files remain available for future work.
- Freeform chat collects NDA details and refreshes the document preview after assistant responses.
- The KAN-9 changes are merged to `main`.
