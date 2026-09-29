# Phase 4 — Frontend + delete

React + Vite + Tailwind v4, Clerk for login/signup, mockups at `assets/mockup/`
(`home.png`, `content.png`). Delete lives only here per ADR-0003 — the MCP server has no
delete tool.

## Mockups are stale on the data model

Both mockups predate the flat Notebook/Note decision (ADR-0001) — `content.png` shows Parent
References, Child References and a node graph. Those don't map to anything: a Note has no
parent/child, only Notebook → many Notes. The UI adopts the mockups' visual language (search
bar, bordered list rows, title/date/tags/link header on the detail page) but drops the
graph-specific sections entirely. The detail page shows: Notebook title, its `retrieve` view
(Roll-up Summary or Derived Summary + staleness delta), then each Note in the Notebook with its
own title, tags, chat link, source app and content — each deletable.

## New: a REST API

Nothing except MCP tools has existed until now. The frontend can't call MCP tools directly (an
SPA is not an MCP client), so `app/api.py` adds a plain JSON API under `/api`, reusing
`db/repository.py` directly rather than going through the MCP layer.

Auth is Clerk, but not the OAuth resource-server flow `app/auth.py` does for MCP clients. The
browser gets a **Clerk session token** from `@clerk/clerk-react`, not an OAuth access token —
same signer and same public key, different shape (no `client_id`/`scopes`/`resource`, no
audience to check). `app/web_auth.py` verifies it with the same RS256 public key and pulls
`sub`, nothing more. Ownership still matches across both entry points because Clerk's user id
(`sub`) is the same value whether the session came from OAuth or from a browser session — the
same `owner_id` space in `db/models.py` serves both.

Endpoints:

- `GET /api/notebooks?q=` — list (or search, if `q` given), reuses `list_recent_notebooks` /
  `search_notes`.
- `GET /api/notebooks/{id}` — Notebook + its `retrieve` view + full Notes, reuses
  `get_notebook_contents` and `render_notebook_view`.
- `DELETE /api/notebooks/{id}` — deletes a whole Notebook, cascades to its Notes (DB-level
  `ON DELETE CASCADE`, already in place from phase 1).
- `DELETE /api/notebooks/{id}/notes/{note_id}` — deletes a single Note.

Both delete operations are new in `db/repository.py` — nothing there deletes today, since the
MCP tool layer deliberately has no delete path.

CORS is opened for the Vite dev origin only.

## Frontend

`frontend/` — Vite + React + TypeScript, Tailwind v4, `@clerk/clerk-react`. Pages:

- Home — search box + list of the 10 most recent Notebooks (mockup: `home.png`).
- Notebook detail — header + summary + Notes, each with a delete affordance; a delete button
  on the Notebook itself (mockup: `content.png`, minus the graph/parent/child sections).
- Sign in / sign up — Clerk's prebuilt components.

## Not doing

- No edit/update of a Note or Notebook's content from the UI — out of scope, wasn't asked for.
- No pagination beyond the existing `limit` params — matches what the tools already do.
