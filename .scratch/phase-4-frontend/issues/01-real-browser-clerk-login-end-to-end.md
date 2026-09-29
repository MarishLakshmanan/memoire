# Test login and the delete flow through a real browser and real Clerk

Status: open

Everything built so far was verified with `tsc -b`, `npm run build`, and curling the dev
server — no assistant-driven browser exists in this environment, so the actual Clerk sign-in
modal, session token issuance, and the delete confirmation flow have not been clicked through.

## Steps

1. `docker compose up -d`, `uv run uvicorn app.app:app --reload --port 8000` (backend).
2. `cd frontend && npm run dev` (frontend, port 5173).
3. Open http://localhost:5173, sign in with Clerk (or sign up as a new user).
4. Confirm the home page lists your Notebooks (from phase 2/3 testing, if using the same
   Clerk account) and that typing in the search box switches to Note search results.
5. Open a Notebook, confirm the rendered `retrieve`-style view and the full Notes list.
6. Delete a Note, confirm it disappears and the Notebook's Note count/summary reacts sensibly.
7. Delete a Notebook, confirm it's gone from the home list and its Notes are gone too (cascade).

## What to look for

- Whether the Clerk session token `ClerkSessionVerifier` expects actually looks like what
  `@clerk/clerk-react`'s `getToken()` returns in practice — this was verified by code reading
  against Clerk's docs, not against a real token.
- CORS: confirm the browser doesn't block requests to `http://localhost:8000/api/*` from
  `http://localhost:5173`.
