Status: open

# Give the MCP mount-order invariant in app.py a seam, not a comment

## Problem Statement

Every request to `/mcp` depends on `mcp_server.streamable_http_app()` running before
`mcp_server.session_manager` is ever touched — calling them out of order raises `RuntimeError`.
Today that invariant exists only as a prose comment in `app/app.py`'s composition root ("Must run
before `session_manager` is touched: it raises RuntimeError otherwise."), directly above the call
that satisfies it. `app/server.py`'s `build_server` gives no indication, from its own interface,
that this ordering matters — a reader auditing `server.py` in isolation has no way to discover the
constraint. Because the bug would live in how `app.py` wires `build_server`'s result together, not
inside `build_server` or `app/tools.py` themselves, no amount of testing either module in
isolation would catch a regression if someone reordered these lines during a future refactor.

## Solution

Move the ordering-sensitive step inside `build_server` (or a small object it returns), so the
sequencing is enforced by one module's own implementation instead of being a fact the composition
root has to remember and re-state as a comment.

## User Stories

1. As a backend maintainer, I want the MCP mount-order requirement enforced by code rather than a
   comment, so a future refactor of `app/app.py` can't silently reintroduce the `RuntimeError`.
2. As a backend maintainer, I want `app/server.py`'s own interface to make the ordering requirement
   impossible to violate from `app/app.py`, so the constraint is discoverable by reading
   `server.py` alone, not only by reading `app.py`'s comment.
3. As an operator running this server, I want `/mcp` and `/health` to keep working exactly as they
   do today, so this refactor introduces no downtime or behavior change.
4. As a backend maintainer, I want `app/app.py`'s lifespan function to keep disposing the database
   engine on shutdown exactly as it does today, so this refactor doesn't disturb shutdown behavior.
5. As a reviewer, I want this change reviewable as a pure internal reordering/encapsulation, so I
   can confirm no request-handling behavior changed.
6. As a future contributor wiring a second mounted sub-application into this host app, I want a
   precedent for how a mount-order constraint should be encoded, so they don't reach for a comment
   as the first instinct.
7. As a backend maintainer, I want whatever `build_server` now returns to still expose exactly what
   `app/tools.py`'s tool registration and `app/prompts.py`'s prompt registration need, so this
   change doesn't ripple into those modules.

## Implementation Decisions

- `build_server` (in `app/server.py`) changes what it returns so the caller in `app/app.py` no
  longer needs to know that `streamable_http_app()` must run before `session_manager` is accessed —
  either by having `build_server` call `streamable_http_app()` itself before returning, bundling
  the resulting ASGI app together with the `MCPServer` (or with a lifespan-context-manager wrapper
  around `session_manager.run()`) in whatever it hands back to `app/app.py`.
- `app/app.py`'s lifespan function and `app.mount("/", mcp_app)` call are updated to use whatever
  shape `build_server` now returns, but keep disposing the database engine on shutdown exactly as
  today.
- The comment at `app/app.py`'s current mount-order line is removed once the ordering is enforced
  in code rather than documented in prose — if any residual note is still useful, it belongs on
  `build_server`'s own docstring, describing what it guarantees, not what the caller must remember.
- No change to `app/tools.py`'s `register_tools`, `app/prompts.py`'s prompt registration, or any
  MCP tool/prompt's external behavior.

## Testing Decisions

- A good test here exercises the actual wiring, not `build_server`'s internals in isolation — the
  bug this spec fixes lives specifically in composition-root ordering, so the only test that could
  have caught it is one that builds the real app the way `app/app.py` does and makes a request
  through it.
- No automated test suite exists in this repo and this spec does not introduce one. Verification is
  manual: start the real host app (`uv run uvicorn app.app:app --reload`) against real Postgres,
  confirm `/health` responds, and confirm a real MCP client can complete a full session against
  `/mcp` (e.g. `list_notebooks`) without a `RuntimeError` — the same smoke check this ordering
  requirement exists to prevent from failing. Additionally, as a deliberate regression check during
  implementation, temporarily reintroduce the wrong order locally and confirm the new code shape
  makes it impossible to write, before removing that check.
- Any one-off verification script belongs in the session scratchpad directory, not the repo.

## Out of Scope

- Introducing pytest, an ASGI test client, or any automated test framework.
- Any change to CORS configuration, the `/health` endpoint's response shape, or
  `ClerkSessionVerifier`/`ClerkTokenVerifier` construction in `app/app.py`.
- Any restructuring toward `src/features/<feature>/`-style folders.
- The Clerk JWT-decode duplication (`.scratch/shared-clerk-jwt-core/spec.md`) or the Notebook/Note
  view-shaping duplication (`.scratch/shared-notebook-view-module/spec.md`) — unrelated to this
  composition-root concern.

## Further Notes

- This project's issue tracker (`docs/agents/issue-tracker.md`) uses a `Status: open|resolved`
  line rather than a labeling system — no `ready-for-agent` label was applied since that
  vocabulary isn't configured for this project (see `/setup-matt-pocock-skills`).
- Source: architecture review of `D:\Projects\ai-notes`, 2026-09-29, candidate 4 (Worth exploring).
