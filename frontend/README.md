# Prelegal Frontend

The Next.js frontend provides a demo-only entry screen and an AI-guided Mutual
NDA workspace. The entry screen does not authenticate users. The workspace
guides NDA creation, updates a preview from chat responses, and downloads a PDF.
Other template files remain in the repository but are not exposed by the current
chat workflow or document-rendering API.

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
