# 01: Add the shared Notebook/Note view-shaping module

**What to build:** A new module in `app/`, alongside `app/notebook_view.py`, that owns the
`NotebookSummary`/`NoteHit`/`NoteFull` `TypedDict`s and the functions that build them from ORM
rows, plus a single id-parsing function. Also add one repository query that returns a caller's
recent Notebooks paired with their Note counts in a single round trip. Purely additive: nothing
calls this module yet, so it's verifiable in isolation before any caller is touched.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] New module (`app/notebook_views.py`) defines `NotebookSummary`, `NoteHit`, `NoteFull` — note:
      `NoteFull` here matches `app/tools.py`'s shape (no `chat_link`), since `app/api.py`'s
      `NoteFull` turned out to carry an extra `chat_link` field the MCP side doesn't — not truly
      identical as first assumed. `app/api.py` keeps its own richer `NoteFull` in ticket 02,
      composed from this module's `to_note_full` plus `chat_link`.
- [x] A function builds a `NotebookSummary` from a `Notebook` plus a note count
- [x] A function builds a `NoteHit` from a `Note`
- [x] A function builds a `NoteFull` from a `Note`
- [x] A function parses a string into a `uuid.UUID`, raising plain `ValueError` on failure
- [x] `db/repository.py` gains `list_recent_notebooks_with_counts`, returning `(Notebook, count)`
      pairs for a caller's recent Notebooks in one grouped `outerjoin` query (no N+1 per-Notebook
      count call); `count_notes` is kept until ticket 02 migrates its two callers off it
- [x] `uv run pyright` reports zero errors
- [x] Verified manually against real Postgres: seeded a throwaway owner with a Notebook with 2
      Notes and an empty Notebook; `list_recent_notebooks_with_counts`'s counts matched
      `count_notes` called per-row for both
