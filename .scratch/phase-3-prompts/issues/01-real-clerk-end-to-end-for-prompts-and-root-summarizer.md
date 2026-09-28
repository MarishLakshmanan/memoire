# Test the four prompts and the Root Summarizer flow through real Clerk + Claude Code

Status: open

Phase 2's issue 01 covers the original four tools against real Clerk. Phase 3 added four
prompts and two more tools (`get_notebook_contents`, `save_notebook_summary`), all verified
against a stubbed token verifier — no live Clerk network call, since the real OAuth flow needs
a browser. Neither the prompts nor the Root Summarizer flow have been exercised for real yet.

## Steps

1. Do phase 2's issue 01 first if it hasn't been done — same server, same connection.
2. In Claude Code, run `/ai-notes:how_to` and check the rendered text looks right as an actual
   slash command (not just correct in isolation — how it reads/renders in the client matters).
3. Run `/ai-notes:save_session` on a real conversation, confirm it writes a sensible summary
   and calls `save_note`.
4. Run `/ai-notes:summarize_notebook <id>` on a Notebook with a few real Notes in it, confirm
   it calls `get_notebook_contents` then `save_notebook_summary` and produces a genuine
   synthesis rather than a concatenation.
5. Run `/ai-notes:recall` (with and without a query argument) from a different AI app if
   possible — this is the actual cross-app scenario the whole project exists for.

## What to look for

Whether prompt discoverability holds up in practice — the MCP client research flagged that
Claude Desktop's prompt discovery is weaker than Claude Code's, so if Desktop is tested, note
whether the prompts actually surface via the "+" → Connectors menu as expected.
