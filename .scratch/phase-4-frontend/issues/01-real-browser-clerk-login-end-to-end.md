# Test login and the delete flow through a real browser and real Clerk

Status: resolved

Everything built so far was verified with `tsc -b`, `npm run build`, and curling the dev
server — no assistant-driven browser exists in this environment, so the actual Clerk sign-in
modal, session token issuance, and the delete confirmation flow have not been clicked through.

## Result (2026-09-29)

Ran end to end via Playwright against the already-running backend/frontend/Postgres, signed
in as `marishlakshmanan@gmail.com` through the real Clerk modal (password + email verification
code, entered by the user). All 7 steps passed:

- Home page listed both existing Notebooks from phase 2/3 testing; search correctly switched
  to Note results with matching snippets.
- Notebook detail rendered the `retrieve`-style Roll-up Summary and the full Notes list with
  timestamps, source app and tags.
- Deleting a Note removed it and the Notebook's count updated to "0 notes".
- Deleting a Notebook redirected home, removed it from the list, and a direct Postgres check
  confirmed both the `notebook` row and its `note` rows (`passive_deletes=True` cascade) were
  actually gone, not just hidden in the UI.
- CORS: no blocked requests, `access-control-allow-origin` correctly echoed `localhost:5173`.

One transient 401 ("Invalid or expired session token") was hit on the very first `/api/notebooks`
call — traced to the session token's 60s TTL expiring during manual network-request inspection,
not a real bug. A page reload got a fresh token from the active Clerk session and everything
worked from then on, confirming `ClerkSessionVerifier` correctly validates what
`@clerk/clerk-react`'s `getToken()` returns in practice.

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
