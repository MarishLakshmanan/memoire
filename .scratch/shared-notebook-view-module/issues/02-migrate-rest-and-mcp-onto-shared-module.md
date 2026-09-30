# 02: Migrate REST and MCP surfaces onto the shared view module

**What to build:** `app/api.py` and `app/tools.py` both call the shared view-shaping module from
ticket 01 instead of their own duplicated `TypedDict`s, dict-building loops, and `_parse_uuid`
helpers. The duplicated per-Notebook `count_notes` call inside both list comprehensions is
replaced by the new consolidated query, and `count_notes` is removed once these were its only
callers.

**Blocked by:** 01 (needs the shared module and consolidated query to exist first)

**Status:** resolved

- [x] `app/api.py`'s local `NotebookSummary`/`NoteHit` definitions and shaping code are removed;
      it imports and calls the shared module's versions. `NoteFull` stays locally defined but now
      extends the shared `NoteFull` (via TypedDict subclassing) adding only `chat_link`, since
      the REST detail view needs a field the MCP side's `NoteFull` doesn't — see ticket 01's note.
- [x] `app/tools.py`'s local `NotebookSummary`/`NoteHit`/`NoteFull` definitions and shaping code
      are removed; it imports and calls the shared module's versions directly (its `NoteFull` is
      identical to the shared one)
- [x] `app/api.py`'s `_parse_uuid` is a thin wrapper: catches the shared parser's `ValueError`,
      raises `HTTPException(404)` exactly as before
- [x] `app/tools.py`'s `_parse_uuid` is a thin wrapper: catches the shared parser's `ValueError`,
      raises `ValueError` with its existing field-name-qualified message exactly as before
- [x] Both `list_notebooks` implementations (REST and MCP) use
      `list_recent_notebooks_with_counts` instead of calling `count_notes` per Notebook
- [x] `db/repository.py`'s standalone `count_notes` is removed
- [x] Code review caught `list_recent_notebooks` (the plain, no-counts version) as dead code once
      both callers moved to `list_recent_notebooks_with_counts` — removed
- [x] No HTTP status code, MCP tool signature, or JSON/structured-content field name changed
- [x] `uv run pyright` reports zero errors; `uv run ruff check` passes
- [x] Verified manually: started the real dev server against real Postgres —
      `GET /api/notebooks` (both branches) and `GET /api/notebooks/{id}` return 401 unauthenticated
      (not 500, confirming the routes/response models still build), and the OpenAPI schema's
      `NotebookSummary`/`NoteHit`/`NoteFull`/`NotebookDetail` component shapes are byte-for-byte
      the same field sets as before, matching `frontend/src/api.ts`'s existing types exactly.
      In-process MCP verification (stubbed access token in the SDK's auth contextvar + real
      Postgres, same style as phase 2's original verification, since this session has no browser
      for a live Clerk OAuth flow): `list_notebooks`, `search_notes`, and `get_notebook_contents`
      all returned correctly-shaped, correct-content results for a seeded Notebook/Note. A
      real-browser, real-Clerk pass through both surfaces is still worth doing before this ships,
      but wasn't required to confirm this refactor is behavior-preserving.
