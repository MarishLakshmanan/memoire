# Test the four prompts and the Root Summarizer flow through real Clerk + Claude Code

Status: resolved

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

## Confirmed so far (2026-09-29)

Phase 2's issue 01 is done — all six tools verified against real Clerk (see that issue).

- `/ai-notes:how_to` — renders cleanly as a real Claude Code slash command: correct Markdown,
  no MCP prompt-envelope leakage, content reads well in the actual client (not just correct in
  isolation).
- `/ai-notes:save_session` — produced a detailed, non-generic Markdown summary of the actual
  session (not a vague one-liner), picked a specific recognizable title, added sensible tags,
  and correctly called `save_note` without asking which Notebook to use (none was specified as
  a continuation, so it created a new one — Notebook `01a0ed63-901b-7433-aea4-d3fd8dc4d474`).

- `/ai-notes:summarize_notebook <id>` — called `get_notebook_contents` then `save_notebook_summary`
  as expected, producing a genuine cross-Note synthesis (throughline + how the two Notes relate)
  rather than a concatenation of their individual summaries.

- `/ai-notes:recall` (no query) — correctly fell back to `list_notebooks` to browse recent
  Notebooks, picked the most recent, called `retrieve` on it, got the Derived Summary fallback
  (no roll-up existed on that one), and reported to the user that a second, related Notebook
  existed with more depth available rather than silently ignoring it.

- `/ai-notes:recall <query>` — worked correctly (`search_notes` → `retrieve` → report back with
  a note about further depth available). Surfaced a real client-side bug along the way: invoking
  `/mcp__ai-notes__recall end to end` in Claude Code only passed the first word (`"end"`) as the
  prompt argument, silently dropping `to end`. Confirmed this is a Claude Code argument-parsing
  issue, not an ai-notes bug — `prompts.py`'s `recall(query)` just interpolates whatever string
  it receives. Not actionable in this repo; worth reporting upstream to Claude Code separately.

All four prompts and all six tools are now verified against real Clerk from Claude Code. The
cross-app `recall` check from a second AI client is deferred — optional/nice-to-have per the
original steps, not required to close this out.
