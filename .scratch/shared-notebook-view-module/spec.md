Status: open

# Deepen a shared Notebook/Note view module behind REST and MCP

## Problem Statement

`app/api.py` (the REST API) and `app/tools.py` (the MCP tools) each independently define
`NotebookSummary`, `NoteHit`, and `NoteFull` as `TypedDict`s, and each independently write the
loop that turns a `Notebook`/`Note` row into that shape. The two copies are field-for-field
identical today, but nothing enforces that: a field added to one and not the other silently
diverges, and a bug fixed in one (or introduced in one) doesn't reach the other. The duplication
is concrete, not hypothetical — both copies also independently call `count_notes` once per
Notebook inside a list comprehension (`app/api.py`, `app/tools.py`), so the same N+1 query
pattern exists in two places rather than one. Both surfaces also duplicate a small id-parsing
helper (`_parse_uuid`) that does the same `uuid.UUID(value)` parse before translating a failure
into their own transport's error type.

## Solution

Add a shared view-shaping module in `app/`, alongside the existing `app/notebook_view.py` (which
already renders `retrieve`'s text view identically for both `app/api.py`'s `get_notebook` and
`app/tools.py`'s `retrieve` — this spec extends that same proven pattern to the listing/search
shapes). The new module owns the `NotebookSummary`/`NoteHit`/`NoteFull` `TypedDict`s, the
functions that build them from ORM rows, and a single id-parsing function. `app/api.py` and
`app/tools.py` call into it and only handle translating a parse failure into their own transport's
error idiom (`HTTPException` vs `ValueError`). As part of consolidating the shaping code, replace
the duplicated per-Notebook `count_notes` call with one repository query that returns Notebooks
paired with their Note counts in a single round trip.

## User Stories

1. As a backend maintainer, I want Notebook/Note response shapes defined once, so that a field
   added to one surface can't silently drift out of sync with the other.
2. As a backend maintainer, I want the note-count-per-Notebook data fetched in one query per
   listing rather than one query per Notebook, so that listing N Notebooks doesn't issue N+1
   queries in either `app/api.py` or `app/tools.py`.
3. As a backend maintainer, I want id-parsing defined once, so that both surfaces reject a
   malformed id the same way before translating into their own transport's error type.
4. As a Claude Code (or other MCP client) user, I want `list_notebooks`, `search_notes`, and
   `get_notebook_contents` to return exactly the field shapes they do today, so that this refactor
   changes no client-visible behavior.
5. As a frontend developer, I want `GET /api/notebooks` and `GET /api/notebooks/{id}` to return
   exactly the JSON shapes they do today, so that `frontend/src/api.ts` needs no changes.
6. As a backend maintainer, I want the shared shaping module to depend on neither FastAPI nor the
   MCP SDK, so that both `app/api.py` and `app/tools.py` can call it without pulling in the other
   transport's machinery.
7. As a backend maintainer, I want the shared id-parsing function to raise one plain exception
   that each caller translates into its own transport error (`HTTPException` 404 for REST,
   `ValueError` with a field name for MCP tools), so the parsing logic isn't duplicated even
   though the two error idioms differ.
8. As a backend maintainer, I want the new module named and placed so it's obviously the sibling
   of `app/notebook_view.py` (text rendering) rather than a third, unrelated place to look for
   Notebook/Note presentation logic.
9. As a reviewer, I want this refactor to touch no database schema, migration, or MCP tool/REST
   route signature, so it's reviewable purely as an internal consolidation.
10. As a backend maintainer, I want the consolidated note-count query checked against real
    Postgres before landing, so the fix doesn't introduce a subtly wrong join or count (e.g. a
    Notebook with zero Notes silently dropping out of a join).
11. As a future contributor, I want this shared module to be the obvious place to add the next
    REST/MCP-shared response shape, so future features don't reintroduce this duplication.
12. As a backend maintainer, I want `db/repository.py`'s standalone `count_notes` retired once the
    new grouped-count query replaces its only two call sites, so the repository doesn't carry a
    now-redundant one-notebook-at-a-time query alongside the batched one.

## Implementation Decisions

- New module in `app/` (flat layout, matching every existing module — no feature-folder
  restructuring as a side effect of this refactor) holding: the `NotebookSummary`, `NoteHit`, and
  `NoteFull` `TypedDict`s (moved out of both `app/api.py` and `app/tools.py`); a function that
  builds a `NotebookSummary` from a `Notebook` plus its note count; a function that builds a
  `NoteHit` from a `Note` (used by both `list_notebooks`'s search branch in the REST API and
  `search_notes` in the MCP tools); a function that builds a `NoteFull` from a `Note` (used by
  `get_notebook` in the REST API and `get_notebook_contents` in the MCP tools); and a single
  `parse_id`-style function wrapping `uuid.UUID(value)` that raises plain `ValueError` on failure.
- `app/api.py`'s `_parse_uuid` and `app/tools.py`'s `_parse_uuid` both become thin wrappers around
  the shared parse function: `app/api.py`'s catches `ValueError` and raises `HTTPException(404)`;
  `app/tools.py`'s catches it and raises `ValueError` with its existing field-name-qualified
  message. Neither transport's current error behavior changes.
- `db/repository.py` gains one new query that returns the caller's recent Notebooks paired with
  each one's Note count in a single query (a grouped count over `Note`, joined or correlated
  against the Notebook ids already being fetched) — replacing the per-Notebook `count_notes` call
  currently made inside both `app/api.py`'s and `app/tools.py`'s list comprehensions.
  `count_notes` is removed once these are its only two callers.
- `NotebookDetail` (REST-only, wraps a rendered view plus a list of `NoteFull`) and
  `SaveNoteResult`/`SaveSummaryResult` (MCP-only) are not duplicated today and stay where they are
  — only the three shapes that exist identically in both files move into the shared module.
- No change to any HTTP status code, MCP tool signature, or JSON/structured-content field name.

## Testing Decisions

- A good test here confirms the shaping functions produce the same field values the two
  hand-written copies did, and that the new grouped-count query returns the same counts
  `count_notes` did per Notebook, including a Notebook with zero Notes.
- This project has no automated test suite (no pytest, no `tests/` directory) and this spec does
  not introduce one — that's a separate decision the user has explicitly deferred. Verification
  is manual, against the real dev stack, matching how every prior phase in this project was
  verified (see `.scratch/phase-2-tools/issues/01-real-clerk-end-to-end-for-real-tools.md` and
  `.scratch/pyright-strict-mode-fixes/spec.md`'s Testing Decisions): run
  `uv run uvicorn app.app:app --reload` against the real Postgres instance on port 5433, exercise
  `list_notebooks`, `search_notes`, and `get_notebook_contents` through a real Clerk-authenticated
  MCP client, and exercise `GET /api/notebooks` (with and without `q`) and `GET /api/notebooks/{id}`
  through the real frontend or a REST client carrying a real Clerk session token. Confirm field
  values and note counts match what the pre-refactor code returned for the same data, including at
  least one Notebook with zero Notes and one with several.
- Any one-off verification script belongs in the session scratchpad directory, not the repo, per
  CLAUDE.md's "Verification scripts go in the session scratchpad directory, not the repo."

## Out of Scope

- Introducing pytest, vitest, or any automated test framework.
- Any restructuring toward `src/features/<feature>/`-style folders — new code stays in the
  existing flat `app/`/`db/` layout.
- Changing `NotebookDetail`, `SaveNoteResult`, or `SaveSummaryResult` — they aren't duplicated and
  aren't part of this consolidation.
- Any change to `app/notebook_view.py`'s existing text-rendering behavior (`render_notebook_view`,
  `snippet`) beyond it gaining a sibling module.
- The Clerk JWT-decode duplication between `app/web_auth.py` and `app/auth.py` — tracked
  separately in `.scratch/shared-clerk-jwt-core/spec.md`.

## Further Notes

- This spec folds in the smaller `_parse_uuid` duplication flagged alongside it in the
  architecture review (`architecture-review-20260929-193032.html`, candidate 6) — it's the same
  REST/MCP duplication shape at a smaller scale, not worth its own spec.
- This project's issue tracker (`docs/agents/issue-tracker.md`) uses a `Status: open|resolved`
  line rather than a labeling system — no `ready-for-agent` label was applied since that
  vocabulary isn't configured for this project (see `/setup-matt-pocock-skills`).
- Source: architecture review of `D:\Projects\ai-notes`, 2026-09-29, candidate 1 (Strong) plus
  candidate 6's `_parse_uuid` item.
