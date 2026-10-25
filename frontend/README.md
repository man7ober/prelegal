# Prelegal Frontend

The Next.js frontend provides signup/signin, per-user saved NDA history, and an
AI-guided Mutual NDA workspace. Other template files remain in the repository
but are not exposed by the current chat workflow or document-rendering API.
Users explicitly save drafts; reopening a saved draft starts a fresh chat using
the saved fields, without retaining chat transcripts.

Before chat details are sent to OpenRouter, the user must consent to the
disclosure. Chat transcripts are not stored. Saved NDA fields and account data
are stored in temporary SQLite and reset when the backend restarts. Do not enter
health information or other highly sensitive personal data.

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and continue to the workspace.
For AI requests, run the backend and configure `OPENROUTER_API_KEY` for it. The
frontend proxies `/api/*` requests to the backend; local development defaults to
`http://localhost:8000`. For production deployments, configure a strong
`SESSION_SECRET_KEY` and set `COOKIE_SECURE=true`.

## Checks

```bash
npm run lint
npm run typecheck
npm run build
```

This is a general starting-point template, not legal advice. Have an attorney review the document for your situation.
