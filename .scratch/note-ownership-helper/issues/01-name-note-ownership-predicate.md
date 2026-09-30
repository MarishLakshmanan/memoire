# 01: Name the Note ownership check via a shared predicate

**What to build:** `db/repository.py` gains one named ownership predicate for Notes — shaped as a
composable predicate (not `_owned_notebook`'s existence-check-and-boolean shape), since `get_note`,
`list_notes`, and `search_notes` each need to combine it with their own additional filters
(id equality, notebook-id equality, full-text match). All three functions replace their inline
`Note.owner_id == owner_id` clause with a call to this predicate.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] New private helper `_note_owned_by(owner_id)` in `db/repository.py`, returning the
      ownership `ColumnElement[bool]` — shaped as a predicate factory (composed into a larger
      `where(...)`), not `_owned_notebook`'s standalone existence-check-and-bool
- [x] `get_note`, `list_notes`, and `search_notes` each use `_note_owned_by(owner_id)` in their
      `where(...)` instead of a hand-written `Note.owner_id == owner_id` clause
- [x] Every other clause in those three functions (id equality, notebook-id equality, the
      full-text `@@` match, ordering, `limit`) is unchanged
- [x] `_owned_notebook` and `add_note` are untouched
- [x] No function signature or return type changed
- [x] `uv run pyright` reports zero errors; `uv run ruff check` passes
- [x] Verified against real Postgres with two owners: seeded owner A with a Notebook/Note, and
      confirmed owner B's `get_note`, `list_notes`, and `search_notes` all return nothing for it,
      while owner A's own calls still return it correctly
