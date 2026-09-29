# 01: Typed REST responses in app/api.py

**What to build:** The `/api` REST router's responses are declared with precise typed shapes
instead of bare `dict`/`list[dict]`, so pyright can verify the frontend gets what it expects, with
no change to the actual response content.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `list_notebooks` returns a `TypedDict`-based shape: a list of Notebook summaries when called
      with no `q`, a list of Note search hits when called with `q`
- [ ] `get_notebook` returns a `TypedDict`-based Notebook detail shape, including its nested list
      of Note details
- [ ] Field names and types match what `frontend/src/api.ts`'s existing TypeScript types already
      expect — no response field renamed, added, or removed
- [ ] `uv run pyright app/api.py` reports zero errors for this file
- [ ] `GET /api/notebooks` (with and without `q`), `GET /api/notebooks/{id}`, and the two delete
      routes verified against the real dev server with a real Clerk session — identical JSON/status
      codes to before this change
