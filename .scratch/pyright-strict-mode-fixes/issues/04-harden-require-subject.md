# 04: Harden _require_subject against a missing access token in app/tools.py

**What to build:** `_require_subject` explicitly handles a missing access token at its single
seam, so all six MCP tools are protected by one checked, deliberate failure instead of an unchecked
assumption that `get_access_token()` always returns a token.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Deviation from the original acceptance criteria (caught by code review before merge):** the
first pass added a redundant, unreachable `if token is None: raise ...` inline in `save_note`
right after `_require_subject(token)` already raised on `None` — needed because `save_note` also
reads `token.client_id` directly, and pyright can't narrow across a function-call boundary without
a `TypeGuard`. That duplicated the null-check logic instead of keeping it in one seam. Fixed by
extracting a small `_require_token(token) -> AccessToken` helper that does the narrowing once;
`_require_subject` now calls it internally, and `save_note` calls it directly to get a properly
narrowed token before reading `client_id`. The other five call sites are genuinely unchanged.

- [x] `_require_subject`'s parameter type is `AccessToken | None`
- [x] `_require_subject` raises a clear, deliberate error when passed `None` (via `_require_token`,
      per the deviation above), before accessing any attribute of the token
- [x] Five of six call sites in `app/tools.py` remain unchanged other than benefiting from the
      wider parameter type; `save_note` (the one that also reads `token.client_id`) calls the new
      `_require_token` helper instead of duplicating a null check — no per-call-site null checks
- [x] `uv run pyright app/tools.py` reports zero errors for this file
- [ ] Each of the six MCP tools verified through a real Clerk-authenticated MCP client — **not
      done**; instead verified directly with a synthetic `AccessToken` (happy path, `None` token,
      and no-subject token all exercised against `_require_token`/`_require_subject`) plus the
      existing real-Clerk end-to-end pass from `.scratch/phase-2-tools/issues/01-...md`, which this
      change doesn't alter the call pattern of for five of six tools. A fresh full real-client pass
      is still a reasonable thing to run before relying on this in production.
