# ai-notes

A shared notes store for AI chat sessions, exposed to AI clients as an **MCP server**.

The problem it solves: summarize a session in one AI tool (say, Claude Code), save it here, then
pull that context into a *different* AI tool later — one that has no way to see the earlier
conversation. ai-notes is the memory layer that crosses that gap.

```
Claude Code ──┐                                   ┌── Claude Code (later, different chat)
              ├── save_session ──▶ ai-notes ◀── recall ──┤
ChatGPT ──────┘        (MCP over OAuth)                  └── any other MCP-speaking client
```

A small React frontend sits alongside it for browsing and deleting Notebooks — the MCP surface
is deliberately read-and-append only (see [ADR-0003](docs/adr/0003-no-delete-tool-on-the-mcp-server.md)).

## Why this project is here

Two things I wanted to actually learn by building something real, not a tutorial:

**Designing an MCP prompt surface.** The four prompts (`save_session`, `summarize_notebook`,
`recall`, `how_to`) aren't UI — they're instructions returned to the *connected model*, telling
it which tools to call and how to use them well. Getting these right meant thinking about
failure modes an LLM would actually hit: how do you word a summarizer's prompt so it stops
itself from silently re-summarizing old sessions? How does a roll-up summary avoid going stale
the moment a new Note is added to a Notebook it already summarized? (Answer: `retrieve` detects
a stale roll-up and appends a delta section for everything saved after it — see
[app/prompts.py](app/prompts.py) and [app/notebook_view.py](app/notebook_view.py).) MCP's
`sampling` capability — letting a server ask the client's model to do work — is deprecated
protocol-wide, so the summarizer prompts hand that work back to the *user's own* model
subscription instead of calling an LLM API server-side.

**OAuth between MCP servers, old protocol vs new.** This server is a pure **OAuth resource
server** — it never issues tokens, only verifies them — with [Clerk](https://clerk.com) as the
external authorization server. That split, and the discovery mechanism that makes it work, is
new: [RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728) (Protected Resource Metadata) is
what lets an MCP client discover *which* authorization server to talk to, served here at
`/.well-known/oauth-protected-resource/mcp`; [RFC 8707](https://datatracker.ietf.org/doc/html/rfc8707)
(Resource Indicators) is what stops a token minted for one resource server from being replayed
against another — the confused-deputy problem the earlier, simpler "bearer token" model of MCP
auth didn't guard against. Getting this working end-to-end surfaced real, specific friction:

- A mounted MCP server's own lifespan never runs — the session manager has to be entered from
  the *host* FastAPI app's lifespan, or every request throws `RuntimeError`
  ([app/server.py](app/server.py)).
- Clerk's development instances don't stamp `aud` at all, so audience validation has to be an
  environment-gated check, not a blanket requirement ([app/auth.py](app/auth.py)).
- The browser frontend and MCP clients authenticate with two *different* Clerk token kinds —
  a session token vs. a scoped OAuth access token — that happen to share a signer and a user id
  but need different validation rules ([app/web_auth.py](app/web_auth.py)).
- A handful of sharper-edged bugs are logged as they were found and fixed, in
  [`.scratch/phase-0-auth-spike/issues/`](.scratch/phase-0-auth-spike/issues/) — pinned public
  keys breaking silently on rotation, redirect URL loopback matching, a `NEXT_PUBLIC_`-shaped
  env var that Vite just never reads.

## Tech stack

- **Backend**: FastAPI, the official MCP Python SDK, Postgres (async, via SQLModel), Alembic.
- **Auth**: Clerk as the OAuth authorization server; this server as a pure resource server.
- **Frontend**: React, Vite, TypeScript, Tailwind v4, `@clerk/clerk-react`.

## MCP surface

**Tools** — `save_note`, `retrieve`, `list_notebooks`, `search_notes`, `get_notebook_contents`,
`save_notebook_summary`. **Prompts** — `save_session`, `summarize_notebook`, `recall`, `how_to`
(named to read well as Claude Code slash commands: `/ai-notes:save_session`).

## Running it locally

Requires [`uv`](https://docs.astral.sh/uv/), Docker, Node, and a free [Clerk](https://clerk.com)
application (for `CLERK_ISSUER`, a publishable key, a secret key, and the instance's public key
downloaded as `clerk.pem`).

```bash
git clone https://github.com/<you>/ai-notes.git
cd ai-notes
cp .env.example .env              # fill in your Clerk values
docker compose up -d               # Postgres on port 5433
uv run alembic upgrade head
uv run uvicorn app.app:app --reload --port 8000
```

Frontend, in a second terminal:

```bash
cd frontend
cp .env.example .env               # same Clerk publishable key as the root .env
npm install
npm run dev                        # http://localhost:5173
```

Connect an MCP client (e.g. Claude Code) to `http://localhost:8000/mcp` — it will walk through
the OAuth flow against your Clerk instance automatically.

## Project layout

- [`app/`](app/) — the MCP server, its FastAPI host, the `/api` REST router, and Clerk auth.
- [`db/`](db/) — SQLModel models and ownership-enforcing repository queries.
- [`migrations/`](migrations/) — Alembic.
- [`docs/adr/`](docs/adr/) — the architectural decisions and why (flat Notes over a tree,
  Postgres over Neo4j, no delete tool over MCP).
- [`.scratch/`](.scratch/) — this project was built phase-by-phase with a written spec and
  tracked issues at each step; it's kept in the repo as the build log, not cleaned up afterward.
- [`frontend/`](frontend/) — the notebook browser and delete UI.

## Status

Functionally complete: MCP tools and prompts, the REST API, delete, and the frontend have all
been exercised end-to-end against a real Clerk instance and a real MCP client. Not deployed
anywhere — this is a local-first, single-developer project built to learn from, not a hosted
product.
