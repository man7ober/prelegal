# Prelegal Frontend

The Next.js frontend provides a demo-only entry screen and an AI-guided document
workspace. The entry screen does not authenticate users. The workspace can guide
creation for the 11 agreement types represented by `catalog.json`, render the
catalogued template text, and download a PDF. Templates that refer to absent
companion documents are flagged in the preview.

Before chat details are sent to OpenRouter, the user must consent to the
disclosure. The conversation and collected values remain in page memory and are
not stored in the database. Do not enter health information or other highly
sensitive personal data.

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and continue to the workspace.
For AI requests, run the backend and configure `OPENROUTER_API_KEY` for it. The
frontend proxies `/api/*` requests to the backend; local development defaults to
`http://localhost:8000`.

## Checks

```bash
npm run lint
npm run typecheck
npm run build
```

This is a general starting-point template, not legal advice. Have an attorney review the document for your situation.
