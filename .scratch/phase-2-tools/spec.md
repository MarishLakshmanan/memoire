# Phase 2 — The four MCP tools

`save_note`, `retrieve`, `list_notebooks`, `search_notes` — wired to real Clerk auth (phase 0)
and the real Postgres schema (phase 1), with a real MCP client used throughout rather than
tested only as plain Python function calls.

## What's here

- `db/repository.py` — the ownership-enforcing query layer deferred from phase 1
  (`.scratch/phase-1-db-layer/issues/01`). Every function takes `owner_id` and filters by it;
  no tool issues its own `select()`.
- `app/notebook_view.py` — the Q3/Q14 retrieve logic: a Roll-up Summary if fresh, a Derived
  Summary (or a delta against a stale one) otherwise. Never returns an empty string.
- `app/source_app.py` — maps a token's `client_id` to the Source App label, server-side only.
  A new, unrecognized client degrades to the raw `client_id` rather than failing the save.
- `app/tools.py` — the four tools, plus `SaveNoteResult` / `NotebookSummary` / `NoteHit`
  TypedDicts so every tool gets a real output schema, not `additionalProperties: true`.
- `app/server.py`, `app/app.py` — promoted from `spike/`, now wired to the real tools instead
  of `ping`. `spike/` is deleted; see `.scratch/phase-0-auth-spike/spec.md`'s update note.
- `migrations/versions/f8c1ce335c87_*.py` — GIN index for `search_notes`'s full-text search.

## Verified against the real MCP protocol, not just as function calls

Two in-process test scripts (not committed — scratchpad, real Postgres, a stubbed
`TokenVerifier` instead of live Clerk since the real OAuth flow needs a browser):

1. **Tool wiring**: registers, calls `save_note` (new + existing Notebook), `retrieve` on
   both a Notebook id (hits the Q3 derived-summary fallback) and a Note id, `list_notebooks`,
   `search_notes` (full-text, confirmed it actually matches), and two negative cases — an
   unowned/missing `notebook_id`, a malformed id. All through the real streamable-HTTP
   transport and JSON-RPC dispatch, not direct Python calls.
2. **Cross-tenant isolation** — the actual point of Q8, not just the schema for it: two real
   MCP client sessions, distinguished only by bearer token as real callers would be. Confirmed
   Owner B's `list_notebooks`, `retrieve`, and `search_notes` cannot see Owner A's data, and
   Owner B cannot append a Note to Owner A's Notebook. All rejections come back as
   not-found, never as a permission error that would leak the id's existence.

Caught one real bug along the way: `save_note`'s plain `dict` return type produced no output
schema at all (`structured_content` was `None`), while `list[dict]` did. Fixed by giving
`save_note`, `list_notebooks`, and `search_notes` proper `TypedDict` return types.

## Not yet done

- **Real Clerk end-to-end test of these tools** — phase 0 proved the auth chain with `ping`;
  these specific tools haven't been called through a real browser OAuth flow yet. See issue 01.
- Prompts (Summarizer, Root Summarizer/summarize_notebook, Retriever, How-to) — phase 3.
- `save_notebook_summary` validation (reject empty/unrelated content) mentioned when Q12 was
  settled — only matters once the summarizer prompt exists to call it. Phase 3.
