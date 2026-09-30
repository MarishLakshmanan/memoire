# 01: Unify Home.tsx's listing/search state into one discriminated result

**What to build:** `frontend/src/api.ts`'s `listNotebooks` and `searchNotes` return a single
discriminated union (a `kind: 'notebooks'` variant carrying `NotebookSummary[]`, a `kind: 'hits'`
variant carrying `NoteHit[]`) instead of each returning its own bare array type. `Home.tsx` holds
one piece of state for this tagged result instead of two (`notebooks` and `hits`), and switches on
the tag in its render logic instead of inferring the active view from `hits !== null`. The existing
debounce, cancellation-on-unmount, and error-clearing behavior in the `useEffect` are preserved.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] `frontend/src/api.ts`'s `listNotebooks`/`searchNotes` return one tagged union
      (`NotebookListResult`: `{kind: 'notebooks', items}` or `{kind: 'hits', items}`) instead of
      two separate array return types
- [x] `Home.tsx` holds one state variable (`result: NotebookListResult | null`, plus its existing
      separate `error` state) instead of `notebooks`/`hits`
- [x] Render logic switches on `result?.kind` instead of `hits !== null`
- [x] The empty-notebooks message ("No notebooks yet.") and empty-search message ("No matches.")
      render under the same steady-state conditions as before. One honest nuance: before the very
      first fetch resolves, the old code (`notebooks` defaulting to `[]`, `hits` to `null`) could
      briefly show "No notebooks yet." on initial mount; the new code (`result` starting `null`)
      shows nothing until the first fetch completes. Arguably the better behavior (it's what the
      null-sentinel ambiguity this ticket exists to remove was papering over), but flagged since
      it's a real, if imperceptible, difference from "identical."
- [x] The 250ms search debounce, immediate listing fetch when the query is empty, and
      cancellation-on-unmount/re-query behavior are unchanged
- [x] `GET /api/notebooks` (`app/api.py`) was not modified
- [x] `npm run typecheck`, `npm run lint`, and `npm run build` all pass clean
- [ ] Full manual pass via `npm run dev` with a real Clerk login (empty account, several
      Notebooks, a search with/without matches, a forced error) — not done in this session (no
      browser/Clerk credentials available here); verified instead by static analysis (typecheck +
      lint + production build all clean) and by reading the diff line-by-line against the original
      render logic to confirm the tag-switch is a faithful translation of the old null-check. A
      real-browser pass is still worth doing before this ships, per the pattern already
      established in `.scratch/phase-4-frontend/issues/01-real-browser-clerk-login-end-to-end.md`.
