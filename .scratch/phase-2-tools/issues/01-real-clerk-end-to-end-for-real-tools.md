# Test save_note / retrieve / list_notebooks / search_notes through real Clerk + Claude Code

Status: open

Phase 0 proved the auth chain end to end with a throwaway `ping` tool. Phase 2 proved the four
real tools end to end through the actual MCP protocol, but against a stubbed token verifier —
no live Clerk network call, since the real OAuth flow needs a browser.

## Steps

1. `docker compose up -d` if the DB isn't already running.
2. `uv run uvicorn app.app:app --reload --port 8000`
3. Claude Code should already be connected from phase 0 (`claude mcp add ...` /mcp). If not, see
   the phase 0 spec for setup.
4. Ask Claude Code to save a note about the current conversation, then list notebooks, then
   retrieve the notebook back, then search for something in it.

## What to look for

That the real Summarizer-shaped flow (a model writing a summary and calling `save_note`) works
without an explicit prompt yet — this validates the tool descriptions are clear enough on their
own. Also confirms `resolve_source_app` maps the real Claude Code `client_id` correctly (it
should, per the phase-0 finding, but this is the first time it runs against these tools).
