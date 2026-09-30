# mémoire

A notes store for AI chat sessions, exposed to AI clients as an MCP server. A user summarises a
session in one AI tool, saves it here, then references it from a different AI tool that cannot see
that conversation. Domain vocabulary is in `CONTEXT.md` — use those words, not their `_Avoid_`
synonyms.

Backend: FastAPI + the official MCP Python SDK + Postgres, with Clerk as the OAuth authorization
server. Frontend: React + Vite + Tailwind v4 + Clerk.

## Where things stand

The phase plan lives in `.scratch/PLAN.md` and is the source of truth for build order. The
original brief (`plan.md`) has been removed now that the phases it describes are done and
superseded by this file and the ADRs.

Phases 0–4 are done and committed, including the frontend, delete UI, and the REST API. The
real-browser + real-Clerk pass (login, search, Notebook detail, Note delete, Notebook delete
with cascade verified at the DB level) is done (2026-09-29) — see
`.scratch/phase-4-frontend/issues/01-real-browser-clerk-login-end-to-end.md`.
The real Clerk + Claude Code end-to-end pass over the six MCP tools and four prompts is done
(2026-09-29) — see `.scratch/phase-2-tools/issues/01-real-clerk-end-to-end-for-real-tools.md` and
`.scratch/phase-3-prompts/issues/01-real-clerk-end-to-end-for-prompts-and-root-summarizer.md`.
Only the optional cross-app `recall` check (from a second AI client, not just Claude Code) is
still deferred.

## Layout

- `app/` — the MCP server and its FastAPI host.
  - `app.py` — FastAPI host; builds engine, session factory and MCP server at module level.
  - `server.py` — `build_server()`; wires the token verifier, tools and prompts.
  - `auth.py` — `ClerkTokenVerifier`, an MCP `TokenVerifier` that validates Clerk RS256 JWTs.
  - `config.py` — `Settings` + `load_settings()`, reads and validates env vars.
  - `tools.py` — the six MCP tools and their `TypedDict` return types.
  - `prompts.py` — the four MCP prompts; plain instructional strings, no DB access.
  - `notebook_view.py` — renders a Notebook for `retrieve`, including the staleness delta.
  - `source_app.py` — maps an OAuth `client_id` to a Source App name.
  - `web_auth.py` — `ClerkSessionVerifier`, verifies the browser's Clerk *session* token
    (not the OAuth access token MCP clients use — see `.scratch/phase-4-frontend/spec.md`).
  - `api.py` — the `/api` REST router the frontend calls: list/search, Notebook detail,
    Notebook/Note delete. The only place anything gets deleted (ADR-0003).
- `db/` — `models.py` (SQLModel), `repository.py` (ownership-enforcing queries), `session.py`.
- `migrations/` — Alembic, async template.
- `docs/adr/` — architectural decisions. `docs/agents/` — issue tracker and domain doc conventions.
- `.scratch/` — the issue tracker. **Tracked in git deliberately**; do not gitignore it.
- `assets/mockup/` — `home.png`, `content.png`, the original frontend mockups. Predate
  ADR-0001 (flat Notes) — their graph/parent/child sections don't apply; see the phase 4 spec.
- `frontend/` — Vite + React + TS + Tailwind v4 + `@clerk/clerk-react`. `npm run dev` (port 5173),
  needs its own `frontend/.env` (see `frontend/.env.example`).

## Running it

```
docker compose up -d                              # Postgres on port 5433
uv run alembic upgrade head
uv run uvicorn app.app:app --reload --port 8000
```

`uv` is the toolchain — there is no system Python on this machine. Use `uv run`, `uv add`.
Postgres is on **5433**, not 5432; 5432 is taken by an unrelated project's container.

Secrets live in `.env` (gitignored, along with `clerk.pem`). Never echo `.env` contents into a
message — it holds a live Clerk secret key.

`.pre-commit-config.yaml` runs ruff on `app/`/`db`/`migrations`, pyright (strict) and bandit on
`app/`/`db` only, and eslint, `tsc`, and `npm audit --audit-level=high` on `frontend/`, on every
commit. `uv run pre-commit install` sets it up.

## MCP surface

Tools:

- `save_note` — the main write path. Creates or appends to a Notebook.
- `retrieve` — a Notebook rendered as text: its Roll-up Summary, or a Derived Summary fallback.
- `list_notebooks`, `search_notes` — discovery. Search is Postgres full-text.
- `get_notebook_contents` — full untruncated Notes, for synthesising a Roll-up Summary.
- `save_notebook_summary` — writes a Roll-up Summary back.

There is deliberately **no delete tool** (ADR-0003). Delete belongs to the frontend only, via
`DELETE /api/notebooks/{id}` and `DELETE /api/notebooks/{id}/notes/{note_id}`.

Prompts: `save_session`, `summarize_notebook`, `recall`, `how_to`. Named to read well as Claude
Code slash commands (`/ai-notes:save_session`).

## Things that will bite you

- **MCP SDK v2**: `FastMCP` was renamed. Import `from mcp.server.mcpserver import MCPServer`.
- **Mounted lifespans never run.** `mcp_server.session_manager.run()` must be entered inside the
  host FastAPI app's own lifespan, or every request raises `RuntimeError`.
- **Use SQLModel's `AsyncSession`**, not SQLAlchemy's — only SQLModel's has `.exec()`.
- **`passive_deletes=True`** is required on `Notebook.notes`. Without it SQLAlchemy nulls the
  children's FK before deleting, which violates the `NOT NULL` constraint.
- **Tool return types must be `TypedDict`s.** A plain `dict` annotation produces no output schema
  at all, so `structured_content` comes back `None`. A bare `list[dict]` gets a useless generic
  schema. This was a real bug, not a theoretical one.
- **`alembic check` always proposes dropping the full-text GIN index.** It is a raw-SQL expression
  index, invisible to SQLAlchemy's metadata. This is expected drift — never "fix" it.
- **RFC 9728 path**: protected resource metadata is at
  `/.well-known/oauth-protected-resource/mcp`, with the resource path appended.
- **Audience validation is production-only.** Clerk development instances do not stamp `aud`, so
  `validate_token_resource` follows `APP_ENV`.
- **Sampling is deprecated** protocol-wide (MCP revision 2026-07-28). Anything needing an LLM runs
  on the user's own subscription via a prompt, or calls a provider API server-side — never
  client-side sampling.
- Protocol tests need `TransportSecuritySettings(enable_dns_rebinding_protection=False)`, and any
  manually-entered async context managers must be closed in strict LIFO order.

## Working conventions

- Track work in `.scratch/<phase-slug>/` — a `spec.md` plus `issues/<NN>-<slug>.md` files with a
  `Status: open|resolved` line. See `docs/agents/issue-tracker.md`.
- Commit at the end of each phase, before moving on.
- **Never put an attribution or co-author line in a commit message.**
- Verification scripts go in the session scratchpad directory, not the repo.
- Google-style docstrings, 1–2 line summaries, every parameter and return documented.

## Agent skills

### Issue tracker

Issues and specs are tracked as local markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context layout: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
