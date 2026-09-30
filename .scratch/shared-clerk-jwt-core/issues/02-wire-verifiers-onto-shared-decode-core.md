# 02: Wire both Clerk verifiers onto the shared decode core

**What to build:** `ClerkTokenVerifier.verify_token` and `ClerkSessionVerifier.verify` both call
the shared decode function from ticket 01, keeping only what's genuinely different: audience
matching and `AccessToken` construction in `ClerkTokenVerifier`, the plain `sub`-only return in
`ClerkSessionVerifier`. Also inline `app/tools.py`'s `_require_token` into `save_note` if it
remains a single-caller helper, having `_require_subject` perform its own null check directly.

**Blocked by:** 01 (needs the shared decode function to exist first)

**Status:** resolved

- [x] `ClerkTokenVerifier.verify_token` calls `decode_clerk_jwt`, then keeps its existing
      `_matching_audience` check, development-mode warning, and `AccessToken` construction
      unchanged
- [x] `ClerkSessionVerifier.verify` calls `decode_clerk_jwt` with `require_audience=False`, then
      keeps its existing plain `claims.get("sub")` return unchanged
- [x] Both verifiers' class, constructor, and public method signatures are unchanged — no caller in
      `app/server.py`, `app/app.py`, or `app/api.py` needed to change
- [x] `app/tools.py`'s `_require_token` was confirmed to have `save_note` as its only direct
      caller for the raw token (every other tool went through `_require_subject`); it's removed,
      `save_note` does its own null check on `get_access_token()`, and `_require_subject` performs
      its own null check directly instead of delegating to `_require_token`
- [x] `uv run pyright` reports zero errors; `uv run ruff check` passes (dropped the now-unused
      `logging`/`jwt` imports from `app/web_auth.py` and `app/auth.py` respectively)
- [x] Verified with locally-signed RSA tokens against the real verifier classes (no browser
      available in this session for a live Clerk OAuth flow): `ClerkTokenVerifier` in dev mode
      accepts an audience-less token, in prod mode accepts a matching `aud` and rejects a
      mismatched one, and rejects an expired token in both modes; `ClerkSessionVerifier` accepts a
      valid session token and rejects an expired one. Also ran `save_note` in-process (stubbed
      access token, real Postgres) to confirm the inlined null-check path still resolves
      `owner_id` and `source_app` correctly — created and then cleaned up a throwaway
      Notebook/Note. A real-browser, real-Clerk pass is still worth doing before this ships.
