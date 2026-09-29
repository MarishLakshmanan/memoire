# Test save_note / retrieve / list_notebooks / search_notes through real Clerk + Claude Code

Status: resolved

Phase 0 proved the auth chain end to end with a throwaway `ping` tool. Phase 2 proved the four
real tools end to end through the actual MCP protocol, but against a stubbed token verifier —
no live Clerk network call, since the real OAuth flow needs a browser.

## Steps

1. `docker compose up -d` if the DB isn't already running.
2. Check nothing else holds port 8000 — see "Port 8000 is shadowed" below.
3. `uv run uvicorn app.app:app --reload --port 8000`
4. Claude Code should already be connected from phase 0 (`claude mcp add ...` /mcp). If not, see
   the phase 0 spec for setup. **Start the server before the Claude Code session** — the client
   only connects to MCP servers at session start, so a session opened while the server is down
   has no ai-notes tools and cannot get them without a restart.
5. Ask Claude Code to save a note about the current conversation, then list notebooks, then
   retrieve the notebook back, then search for something in it.

## Port 8000 is shadowed by another project

The unrelated `enterprisemvp-app-1` container publishes port 8000 on `0.0.0.0` **and `[::]`**.
Our uvicorn only binds IPv4 `127.0.0.1:8000`. Windows resolves `localhost` to IPv6 `::1` first,
so with both running, `http://localhost:8000/mcp` reaches enterprisemvp and returns a FastAPI
404 — while `http://127.0.0.1:8000/mcp` reaches us and works.

This fails silently and looks like a broken MCP server. Check with
`netstat -ano | grep ":8000 .*LISTENING"` — exactly one listener should be there. Same root cause
as the Postgres 5433 choice.

## Confirmed so far (2026-09-29)

Against real Clerk, with the server running and enterprisemvp stopped:

- `/health` returns 200 and the expected resource identifier.
- Unauthenticated `POST /mcp` returns 401 with `WWW-Authenticate` naming
  `http://localhost:8000/.well-known/oauth-protected-resource/mcp`.
- That metadata document resolves and lists the Clerk issuer as its authorization server.
- Clerk's own authorization-server metadata is reachable.
- `claude mcp list` reports `ai-notes ... ✔ Connected` — so a real Clerk token is being minted
  and accepted by `ClerkTokenVerifier` against the current code, not just the phase 0 spike.

Still outstanding: actually calling the six tools and four prompts through the client.

## What to look for

That the real Summarizer-shaped flow (a model writing a summary and calling `save_note`) works
without an explicit prompt yet — this validates the tool descriptions are clear enough on their
own. Also confirms `resolve_source_app` maps the real Claude Code `client_id` correctly (it
should, per the phase-0 finding, but this is the first time it runs against these tools).

## Confirmed (2026-09-29, continued)

All six tools called for real against the live server (real Clerk token, real Postgres, no
stubbed verifier), unprompted — Claude Code wrote and called these on its own from the tool
descriptions alone, matching the Summarizer-shaped flow this issue asked to check:

- `save_note` — created a new Notebook, then appended a second Note to it (`notebook_created`
  correctly `true` then `false`).
- `list_notebooks` — reflected the resulting Notebook with an accurate `note_count`.
- `retrieve` — served the Derived Summary fallback before a roll-up existed, then correctly
  switched to serving the Roll-up Summary once `save_notebook_summary` was called.
- `search_notes` — full-text search found the note and reported `"source_app": "claude-code"`
  on the hit, confirming `resolve_source_app` maps the real Claude Code OAuth `client_id`
  correctly.
- `get_notebook_contents` — returned both Notes in full (untruncated), oldest first.
- `save_notebook_summary` — accepted a genuine cross-Note synthesis, not a concatenation, and
  `retrieve` immediately reflected it.

Tools are fully verified. Prompts (`save_session`, `summarize_notebook`, `recall`, `how_to`)
are still outstanding — see the phase-3 issue, since only the user can invoke slash commands.
