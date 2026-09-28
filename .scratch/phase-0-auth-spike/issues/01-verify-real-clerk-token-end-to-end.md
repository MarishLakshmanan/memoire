# Verify a real Clerk token end to end

Status: open

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
