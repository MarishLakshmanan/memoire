Status: open

# Name the Note ownership check the same way the Notebook one is named

## Problem Statement

`db/repository.py`'s own module docstring states that going through this module, rather than
letting any caller issue its own `select()`, is what makes the owner filter "structurally hard to
skip" — the defense-in-depth guarantee from Q8. For Notebooks, that's literally true: every
Notebook query routes through the named `_owned_notebook` helper. For Notes, the identical
invariant (`Note.owner_id == owner_id`) is instead written out by hand, separately, inside
`get_note`, `list_notes`, and `search_notes`. Auditing "is ownership enforced for every Note
query" currently means reading three functions and confirming three independently-written clauses
all say the same thing, rather than confirming one named predicate is used everywhere.

## Solution

Give Notes the same seam Notebooks already have: a single named ownership predicate that
`get_note`, `list_notes`, and `search_notes` all include in their `where(...)`, so the invariant
has one name to read, one place to change, and one thing to verify.

## User Stories

1. As a backend maintainer, I want a single named function expressing "this Note belongs to this
   owner," so that auditing ownership enforcement for Notes means confirming one name is used
   everywhere, not comparing three hand-written clauses.
2. As a backend maintainer, I want `get_note`, `list_notes`, and `search_notes` to each include the
   named ownership predicate in their existing `where(...)` alongside their own additional filters
   (id equality, notebook-id equality, full-text match), so the predicate composes into each
   query's other conditions rather than replacing them.
3. As an MCP client user, I want `retrieve`, `get_notebook_contents`, and `search_notes` to keep
   returning exactly the same results for the same caller and data, so this refactor changes no
   observable behavior.
4. As a frontend user, I want Notebook detail pages and Note deletion to keep enforcing ownership
   exactly as they do today, so this refactor introduces no regression in cross-tenant isolation.
5. As a backend maintainer, I want the new Note ownership predicate named and shaped consistently
   with `_owned_notebook`, so a future contributor recognizes the pattern immediately rather than
   learning a second convention.
6. As a security reviewer, I want this change to be reviewable as a pure rename-and-consolidate
   with no logic change, so I can confirm cross-tenant isolation (Q8) still holds without
   re-deriving the query semantics from scratch.
7. As a backend maintainer, I want `add_note`'s existing use of `_owned_notebook` left untouched, so
   this spec only addresses the Note-side asymmetry, not the Notebook-side helper that already
   works correctly.
8. As a future contributor adding a new Note query, I want the named predicate to be the obvious
   thing to reach for, so a new query doesn't reintroduce a fourth hand-written
   `Note.owner_id == owner_id` clause.

## Implementation Decisions

- `db/repository.py` gains a private helper — shaped like a predicate factory rather than
  `_owned_notebook`'s existence-check-and-boolean shape, since `get_note`, `list_notes`, and
  `search_notes` each need to compose the ownership condition into a larger `select(...)` alongside
  their own additional filters and ordering, not perform a standalone existence check.
- `get_note`, `list_notes`, and `search_notes` each replace their inline
  `Note.owner_id == owner_id` clause with a call to this helper, keeping every other clause
  (id equality, notebook-id equality, the full-text `@@` match, ordering, `limit`) exactly as it is
  today.
- `_owned_notebook` is unchanged — this spec only closes the asymmetry on the Note side.
- No change to any function's signature, return type, or the set of rows any query returns for the
  same inputs.

## Testing Decisions

- A good test here confirms `get_note`, `list_notes`, and `search_notes` still return nothing for a
  Note owned by a different `owner_id`, and still return the expected rows for the caller's own
  Notes — the same cross-tenant-isolation property already verified manually in this project (see
  `.scratch/phase-2-tools/issues/01-real-clerk-end-to-end-for-real-tools.md`'s note on verifying
  "the actual point of Q8 — cross-tenant isolation — with two real client sessions distinguished
  only by bearer token").
- No automated test suite exists in this repo and this spec does not introduce one. Verification is
  manual against real Postgres: seed two owners' Notebooks/Notes, confirm each of `get_note`,
  `list_notes`, and `search_notes` still can't see or return the other owner's Notes, confirm the
  legitimate owner's results are unchanged, following the same two-real-session verification style
  used in phase 2.
- Any one-off verification script belongs in the session scratchpad directory, not the repo.

## Out of Scope

- Introducing pytest or any automated test framework.
- Any change to `_owned_notebook`, `create_notebook`, `add_note`, `delete_notebook`, or
  `delete_note`.
- Any change to the full-text search behavior (`search_notes`'s `tsquery`/`tsvector`/`ts_rank`
  logic) beyond composing the ownership predicate into its existing `where(...)`.
- Any restructuring toward `src/features/<feature>/`-style folders.

## Further Notes

- This project's issue tracker (`docs/agents/issue-tracker.md`) uses a `Status: open|resolved`
  line rather than a labeling system — no `ready-for-agent` label was applied since that
  vocabulary isn't configured for this project (see `/setup-matt-pocock-skills`).
- Source: architecture review of `D:\Projects\ai-notes`, 2026-09-29, candidate 3 (Worth exploring).
