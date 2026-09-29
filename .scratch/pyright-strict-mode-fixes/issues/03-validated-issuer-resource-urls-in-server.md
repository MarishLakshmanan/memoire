# 03: Validated Clerk issuer/resource URLs in app/server.py

**What to build:** `build_server` constructs the MCP SDK's `AuthSettings` from validated
`AnyHttpUrl` values instead of raw strings, so a malformed `CLERK_ISSUER` or `MCP_RESOURCE_URL`
environment variable is caught at startup instead of silently passed through.

**Blocked by:** None (can start immediately)

**Status:** resolved

**Deviation from the original acceptance criteria (caught by code review before merge):**
pre-wrapping the settings in `AnyHttpUrl(...)` at the call site was implemented first, but verified
to be a real bug — a bare `AnyHttpUrl(...)` normalizes a path-less issuer differently than
`AuthSettings`' own field validation does, silently appending a trailing slash
(`https://foo.clerk.accounts.dev` → `.../`) and corrupting RFC 8414 exact-string issuer matching.
Confirmed directly: `str(AuthSettings(issuer_url=AnyHttpUrl(...)).issuer_url)` has the trailing
slash; `str(AuthSettings(issuer_url="...").issuer_url)` (raw string) does not. The actual fix keeps
passing plain strings — pydantic already validates/coerces them correctly via `AuthSettings`' own
field config — and silences pyright's static-only complaint with a narrow, documented
`# pyright: ignore[reportArgumentType]` instead.

- [x] `build_server`'s `AuthSettings(...)` call passes `issuer_url`/`resource_server_url` as plain
      strings (not `AnyHttpUrl(...)`, per the deviation above), with pyright's complaint narrowly
      suppressed and documented
- [x] `Settings.clerk_issuer`/`resource_url` and `ClerkTokenVerifier` keep their current plain
      `str` typing and string-equality comparisons — untouched
- [x] `uv run pyright app/server.py` reports zero errors for this file
- [x] Dev server starts successfully with real `CLERK_ISSUER`/`MCP_RESOURCE_URL` values, and the
      OAuth protected-resource metadata endpoint
      (`/.well-known/oauth-protected-resource/mcp`) reports the exact same issuer/resource values
      as before (no trailing slash) — verified against the real Clerk issuer
