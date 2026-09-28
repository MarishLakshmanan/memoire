# Phase 0 — Auth spike

Throwaway spike proving the riskiest part of the architecture composes before any domain code is written: FastAPI hosting an MCP server over streamable HTTP, with Clerk as the external OAuth authorization server.

## Scope

One trivial `ping` tool that reports the authenticated caller. No database, no Notebooks, no Notes.

## Proven so far

- `mcp` 2.x mounts into FastAPI, with the session manager entered from the host app's lifespan (a mounted sub-app's own lifespan never runs).
- RFC 9728 protected resource metadata is served at `/.well-known/oauth-protected-resource/mcp`.
- Unauthenticated calls to `/mcp` return 401 with a `WWW-Authenticate` header pointing at that metadata.
- Audience validation is environment-gated and warns loudly when off.

## Not yet proven

End-to-end auth with a real Clerk instance and a real MCP client. See issues 01 and 02.

## Exit criteria

Claude Code connects to the server, completes the OAuth flow against Clerk, and calls `ping`
successfully, with the returned `audience` inspected to confirm what Clerk stamps.
