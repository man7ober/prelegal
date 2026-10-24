# Prelegal Frontend

The Next.js frontend provides a demo-only entry screen and the existing mutual
NDA workspace. The entry screen does not authenticate users; any valid-looking
email and non-empty password continue to `/workspace` without sending or storing
the values.

## Run locally

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and continue to the workspace.
The form and live document preview run in the browser; PDF export is generated
locally and form details are not sent to a server.

## Checks

```bash
npm run lint
npm run typecheck
npm run build
```

This is a general starting-point template, not legal advice. Have an attorney review the document for your situation.
