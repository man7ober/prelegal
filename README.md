# Prelegal

A platform for drafting common legal agreements

## Status

> **In progress** — Prelegal is currently under development and is expected to be completed within one week (by **October 30, 2026**).

## Run Prelegal

The app provides a demo-only entry screen and an AI-guided Mutual NDA workflow.
Other template files are retained in the repository for future work, but are not
currently exposed by the chat or document-rendering API. The NDA flow renders the
catalogued terms and provides a PDF download. The app does not provide real
authentication or persistence.

Start both services with Docker Compose:

```bash
docker compose up -d --build
```

Open [http://localhost:3000](http://localhost:3000) and continue to the
workspace. Before using AI guidance, the app discloses that conversation details
are sent to OpenRouter and requires explicit consent. Chat and field values stay
in browser memory and are not written to SQLite. Set `OPENROUTER_API_KEY` in the
project-root `.env` file to enable AI guidance. The backend health endpoint is available at
[http://localhost:8000/health](http://localhost:8000/health).

Stop the services with `docker compose down`. The database is stored only in the
backend container and is not mounted to a persistent volume.

For local frontend development and checks, see [`frontend/README.md`](frontend/README.md).

Drafts are general starting points, not legal advice. Review with an attorney.
