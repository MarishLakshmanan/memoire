# Verify a real Clerk token end to end

Status: resolved

The spike is proven structurally but has never seen a genuine Clerk token. Everything so far
used a placeholder issuer, so signature and audience verification are untested against reality.

## Steps

1. Put the real `CLERK_ISSUER` and `MCP_RESOURCE_URL` in `.env`.
2. Enable CIMD in the Clerk dashboard (Configure → OAuth Applications). Leave DCR off — see
   `docs/adr/` and issue 03.
3. Connect Claude Code to the server and complete the OAuth flow.
4. Call `ping` and read the returned `audience` field.

## What to look for

`audience` is the load-bearing value. If it comes back `null`, Clerk is not stamping `aud`
on this instance — expected on a development instance, but it must be non-null before
production, otherwise a token minted for another resource in the same Clerk instance is
accepted here. Record which one you observed.

## Answer

Tested against the real Clerk instance with Claude Code as the client, `APP_ENV=development`.

- `subject`: `user_3I9HxQw0FRcuZ2laaWJ70mqJIcm`
- `client_id`: `https://claude.ai/oauth/claude-code-client-metadata`
- `audience`: `http://localhost:8000/mcp` — matches `MCP_RESOURCE_URL` exactly
- `scopes`: `offline_access, profile, email`

Two findings:

1. **`client_id` is the CIMD metadata document URL itself**, not an opaque id. That's only
   possible via CIMD — confirms Claude Code actually used CIMD rather than falling back to
   DCR, matching the research from the Clerk investigation.
2. **`audience` was populated on this instance**, contradicting the research claim that Clerk
   development instances don't stamp `aud`. Either that claim doesn't hold for this instance,
   or Clerk's behavior has changed. Don't relax the `APP_ENV` gate on the strength of one
   observation — keep audience validation off by default in development and treat any
   populated value as a bonus, not a guarantee. Re-check this if Clerk changes are announced.
