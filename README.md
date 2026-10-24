# Prelegal

A platform for drafting common legal agreements

## Status

> **In progress** — Prelegal is currently under development and is expected to be completed within one week (by **October 30, 2026**).

## Run the V1 foundation

The V1 foundation includes a demo-only entry screen, the existing NDA workspace,
a minimal FastAPI health endpoint, and an empty SQLite database created when the
backend starts. The demo screen does not authenticate users or store credentials.

Start both services with Docker Compose:

```bash
docker compose up -d --build
```

Open [http://localhost:3000](http://localhost:3000) to continue to the NDA
workspace. The backend health endpoint is available at
[http://localhost:8000/health](http://localhost:8000/health).

Stop the services with `docker compose down`. The database is stored only in the
backend container and is not mounted to a persistent volume.

For frontend development without Docker, see [`frontend/README.md`](frontend/README.md).

The NDA prototype builds a mutual NDA preview and downloads it as a PDF. It is a
general starting point, not legal advice.
