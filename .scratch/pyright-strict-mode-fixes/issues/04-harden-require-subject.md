# 04: Harden _require_subject against a missing access token in app/tools.py

**What to build:** `_require_subject` explicitly handles a missing access token at its single
seam, so all six MCP tools are protected by one checked, deliberate failure instead of an unchecked
assumption that `get_access_token()` always returns a token.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] `_require_subject`'s parameter type is `AccessToken | None`
- [ ] `_require_subject` raises a clear, deliberate error when passed `None`, before accessing any
      attribute of the token
- [ ] All six call sites in `app/tools.py` (`save_note` and the other five tools) remain unchanged
      other than benefiting from the wider parameter type — no per-call-site null checks added
- [ ] `uv run pyright app/tools.py` reports zero errors for this file
- [ ] Each of the six MCP tools (`save_note`, `retrieve`, `list_notebooks`, `search_notes`,
      `get_notebook_contents`, `save_notebook_summary`) verified once through a real
      Clerk-authenticated MCP client, behaving identically to before
