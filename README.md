# Prelegal

A platform for drafting common legal agreements

## Status

> **In progress** — Prelegal is currently under development and is expected to be completed within one week (by **October 30, 2026**).

## Run Prelegal

The app provides account signup/signin, a per-user NDA history, and an AI-guided
Mutual NDA workflow. Other template files are retained in the repository for
future work, but are not currently exposed by the chat or document-rendering API.
Users explicitly save drafts; reopening a saved draft starts a fresh chat with
its saved fields. Chat transcripts are not stored.

Start both services with Docker Compose:

```bash
docker compose up -d --build
```

Open [http://localhost:3000](http://localhost:3000) to sign up or sign in.
Before using AI guidance, the app discloses that conversation details are sent to
OpenRouter and requires explicit consent. Saved NDA fields and account data are
stored in temporary SQLite and reset whenever the backend restarts. Set
`OPENROUTER_API_KEY` in the project-root `.env` file to enable AI guidance. For
deployments, set a strong `SESSION_SECRET_KEY` and `COOKIE_SECURE=true`. The
backend health endpoint is available at
[http://localhost:8000/health](http://localhost:8000/health).

Stop the services with `docker compose down`. The database is stored only in the
backend container and is not mounted to a persistent volume.

For local frontend development and checks, see [`frontend/README.md`](frontend/README.md).

Drafts are general starting points, not legal advice. Review with an attorney.
