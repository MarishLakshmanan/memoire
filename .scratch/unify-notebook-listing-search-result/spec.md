Status: open

# Resolve "listing vs. search hit" once, not three times

## Problem Statement

Home.tsx needs to know whether it's currently showing the caller's Notebook listing or the results
of a search, and that single fact is decided three separate times: `GET /api/notebooks` branches
on whether `q` is present server-side; `frontend/src/api.ts` exposes it as two differently-named
client functions (`listNotebooks`/`searchNotes`); and `Home.tsx` re-decides it a third time in
component state, using `hits !== null` as a stand-in for "am I displaying a search result."
Nothing type-checks that `hits` being `null` and `notebooks` being populated stay consistent with
each other — it's maintained entirely by hand inside a `useEffect`, and a bug there (e.g. an error
path that clears one but not the other) would render silently wrong content rather than fail to
compile.

## Solution

Resolve the discriminated union once, at the fetch boundary, instead of a third time in the view.
`frontend/src/api.ts`'s two functions return a single tagged result shape; `Home.tsx` holds one
piece of state and switches on its tag, rather than holding two pieces of state and inferring which
one is "active" from a null check.

## User Stories

1. As a frontend maintainer, I want "am I showing Notebooks or search hits" represented as one
   tagged value, so the view can switch on a tag instead of inferring intent from a null check.
2. As a user searching in the app, I want the results I see to always match what I actually
   searched for, so a stale error path can't leave the old list visible under a new query (or
   vice versa).
3. As a frontend maintainer, I want TypeScript to catch a case where the "notebooks" and "hits"
   branches are both handled, so the compiler — not a manual review — enforces that the two states
   can't both be true or both be false.
4. As a user, I want the empty states ("No notebooks yet." / "No matches.") to keep rendering
   exactly when they do today, so this refactor changes no visible behavior for an empty result.
5. As a user, I want the 250ms search debounce and cancellation-on-unmount/re-query behavior to
   keep working exactly as it does today, so this refactor doesn't reintroduce a race between a
   slow search response and a newer query.
6. As a frontend maintainer, I want `GET /api/notebooks`'s existing REST contract (branching on
   `q`, returning `NotebookSummary[]` or `NoteHit[]`) left unchanged, so this refactor is isolated
   to the frontend and doesn't require a backend change.
7. As a frontend maintainer, I want the error state (`error`) to remain a separate piece of state
   from the tagged result, so a fetch failure is represented distinctly from "zero results."
8. As a future contributor adding a third view state to Home (e.g. a loading state), I want the
   tagged-result pattern to be the obvious place to extend, so a fourth ad hoc boolean or null
   sentinel doesn't get added next to it.

## Implementation Decisions

- `frontend/src/api.ts`'s `listNotebooks` and `searchNotes` keep their current HTTP calls
  unchanged, but their return type becomes a single discriminated union — a `kind: 'notebooks'`
  variant carrying `NotebookSummary[]` and a `kind: 'hits'` variant carrying `NoteHit[]` — instead
  of each function returning its own bare array type.
- `Home.tsx` replaces its two pieces of state (`notebooks: NotebookSummary[]`,
  `hits: NoteHit[] | null`) with one: the tagged result (or `null` before the first fetch
  completes). The render logic switches on the tag (`result.kind === 'hits'`) instead of
  `hits !== null`.
- The existing debounce (250ms when `query` is non-empty, immediate when empty),
  cancellation-on-unmount, and error-clearing behavior in the `useEffect` are preserved — only the
  shape of what gets set into state changes, not the fetch timing or cancellation logic.
- `GET /api/notebooks` itself (`app/api.py`) is unchanged — this is a frontend-only consolidation of
  a client-side representation, not a backend contract change.

## Testing Decisions

- A good test here confirms the empty-notebooks state, the empty-search-results state, a populated
  notebooks list, a populated search-hits list, and the error state each render the correct content
  — behavior, not the internal state shape.
- No frontend test tooling exists yet in this repo (no vitest, no React Testing Library) and this
  spec does not introduce it — that's a separate decision the user has explicitly deferred for now.
  Verification is manual: run `npm run dev`, exercise the Home page with an empty account, an
  account with several Notebooks, a search with matches, a search with no matches, and a forced
  error (e.g. an expired session), confirming each renders the same content it does today before
  the refactor.
- `npm run typecheck` (already wired into pre-commit) must continue to pass, and should now also
  catch a missing branch on the tagged union if one is later added and not handled.

## Out of Scope

- Introducing Vitest, React Testing Library, or any frontend test framework.
- Any change to `GET /api/notebooks`'s REST contract, status codes, or response shapes.
- Any change to `NotebookDetail.tsx` or the delete flow.
- Any change to the search debounce duration or trigger condition.

## Further Notes

- This project's issue tracker (`docs/agents/issue-tracker.md`) uses a `Status: open|resolved`
  line rather than a labeling system — no `ready-for-agent` label was applied since that
  vocabulary isn't configured for this project (see `/setup-matt-pocock-skills`).
- Source: architecture review of `D:\Projects\ai-notes`, 2026-09-29, candidate 5 (Speculative).
