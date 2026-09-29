# 01: Typed REST responses in app/api.py

**What to build:** The `/api` REST router's responses are declared with precise typed shapes
instead of bare `dict`/`list[dict]`, so pyright can verify the frontend gets what it expects, with
no change to the actual response content.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] `list_notebooks` returns a `TypedDict`-based shape: a list of Notebook summaries when called
      with no `q`, a list of Note search hits when called with `q`
- [x] `get_notebook` returns a `TypedDict`-based Notebook detail shape, including its nested list
      of Note details
- [x] Field names and types match what `frontend/src/api.ts`'s existing TypeScript types already
      expect — no response field renamed, added, or removed
- [x] `uv run pyright app/api.py` reports zero errors for this file
- [x] Verified against a real running dev server: the OpenAPI schema at `/openapi.json` shows
      `NotebookSummary`/`NoteHit`/`NotebookDetail` component schemas exactly matching the new
      TypedDicts, and unauthenticated `GET /api/notebooks`/`GET /api/notebooks/{id}` return 401
      (not 500), confirming FastAPI built the routes and response models without error
- [ ] Full authenticated pass with a real Clerk session (both `q` branches, `get_notebook`, and the
      two delete routes returning identical JSON/status to before) — **not done**; only
      unauthenticated routing + schema shape were verified, not authenticated response bodies. A
      real-Clerk pass through the frontend or a REST client is still worth doing.
