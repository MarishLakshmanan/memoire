# 03: Validated Clerk issuer/resource URLs in app/server.py

**What to build:** `build_server` constructs the MCP SDK's `AuthSettings` from validated
`AnyHttpUrl` values instead of raw strings, so a malformed `CLERK_ISSUER` or `MCP_RESOURCE_URL`
environment variable is caught at startup instead of silently passed through.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `build_server`'s `AuthSettings(...)` call constructs `issuer_url`/`resource_server_url` from
      `AnyHttpUrl(...)`, not the raw `str` settings values
- [ ] `Settings.clerk_issuer`/`resource_url` and `ClerkTokenVerifier` keep their current plain
      `str` typing and string-equality comparisons — the conversion is local to this one call site
- [ ] `uv run pyright app/server.py` reports zero errors for this file
- [ ] Dev server starts successfully with real `CLERK_ISSUER`/`MCP_RESOURCE_URL` values, and the
      OAuth protected-resource metadata endpoint
      (`/.well-known/oauth-protected-resource/mcp`) still reports the same issuer/resource values
      as before
