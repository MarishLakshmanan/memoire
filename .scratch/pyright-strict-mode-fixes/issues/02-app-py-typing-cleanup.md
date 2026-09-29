# 02: Typed /health response and modern async-generator annotation in app/app.py

**What to build:** The FastAPI host's `/health` endpoint returns a typed body instead of a bare
`dict`, and its `lifespan` context manager uses the currently-recommended `AsyncGenerator`
return-type annotation instead of the deprecated `AsyncIterator` one — both with no behavior
change.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `/health` returns a `TypedDict`-typed body (`status`, `resource`) instead of bare `dict`
- [ ] `lifespan`'s return type is `AsyncGenerator[None]`, imported from `collections.abc`, instead
      of the deprecated `AsyncIterator[None]`
- [ ] `uv run pyright app/app.py` reports zero errors for this file
- [ ] `GET /health` verified against the real dev server, returning identical JSON to before
- [ ] Dev server starts and serves `/mcp` successfully, confirming `lifespan` still runs the MCP
      session manager correctly
