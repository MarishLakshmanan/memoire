# Confirm Clerk matches Claude Code's loopback redirect port-agnostically

Status: resolved

Claude Code uses an ephemeral-port loopback redirect for the OAuth flow, so the port differs
on every connection attempt. Clerk must match `http://localhost/callback` and
`http://127.0.0.1/callback` without pinning a port, or the flow fails at the redirect step.

Hosted Claude surfaces need the exact redirect `https://claude.ai/api/mcp/auth_callback`
instead, so both need to be configured.

This is dashboard configuration, not code. It is the kind of mismatch that presents as a
generic OAuth error and costs an afternoon, so check it before debugging anything else.

## Answer

Claude Code completed the OAuth flow end to end and `ping` succeeded, which is only possible
if the loopback redirect matched. Confirmed working, no further action needed.
