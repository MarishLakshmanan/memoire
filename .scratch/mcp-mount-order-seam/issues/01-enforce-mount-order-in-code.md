# 01: Enforce the MCP mount-order invariant in code, not a comment

**What to build:** `build_server` (in `app/server.py`) changes what it returns so `app/app.py` no
longer needs to know that `streamable_http_app()` must run before `session_manager` is touched —
either by having `build_server` call `streamable_http_app()` itself before returning, bundling the
resulting ASGI app together with the `MCPServer` (or a lifespan-context-manager wrapper around
`session_manager.run()`) in whatever it hands back. `app/app.py`'s lifespan and mount call update
to match, keeping engine disposal on shutdown unchanged. The prose comment documenting the ordering
requirement is removed once the ordering is enforced in code.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] `build_server` now returns a `MountedMCPServer` dataclass (`asgi_app` + a `lifespan()`
      async context manager wrapping `session_manager.run()`), built by calling
      `streamable_http_app()` itself before returning — `app/app.py` no longer holds the ordering
      knowledge at all, in either order it uses the two pieces
- [x] `app/app.py`'s lifespan function still disposes the database engine on shutdown, unchanged
- [x] The prose comment about mount ordering is removed; the guarantee is now documented on
      `MountedMCPServer`'s own docstring
- [x] No change to `app/tools.py`'s `register_tools`, `app/prompts.py`'s prompt registration, CORS
      configuration, or the `/health` endpoint's response shape
- [x] `uv run pyright` reports zero errors; `uv run ruff check` passes
- [x] Verified against real Postgres: started `uv run uvicorn app.app:app`; `/health` returned
      `200`; a real `POST /mcp` `initialize` request returned `401` (auth-gated, not a 500 or
      startup crash) with the log showing "StreamableHTTP session manager started" — the session
      manager entered cleanly with no `RuntimeError`
- [x] Regression check: confirmed directly against the MCP SDK that entering
      `session_manager.run()` before `streamable_http_app()` does raise `RuntimeError`
      ("Session manager can only be accessed after calling streamable_http_app()"), confirming
      this is a real invariant and that `build_server` now satisfies it unconditionally rather
      than by convention
