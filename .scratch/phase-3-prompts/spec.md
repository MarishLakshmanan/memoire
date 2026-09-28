# Phase 3 — Prompts

The four prompts from plan.md: Summarizer, Root Summarizer, Retriever, How-to — named
`save_session`, `summarize_notebook`, `recall`, `how_to` (chosen to read well as Claude Code
slash commands, per the client research from grilling plan.md).

## What's here

- `app/prompts.py` — all four, each a plain instructional string with no DB access of its
  own; they tell the connected model which tools to call and how.
- Two new tools in `app/tools.py` for the Root Summarizer flow (Q12: the two-step dance on
  the user's own subscription, not a server-side API call):
  - `get_notebook_contents` — full, untruncated Note content (unlike `retrieve`'s truncated
    snippets), because a roll-up needs the real thing to synthesize from.
  - `save_notebook_summary` — validates non-blank, validates the Notebook actually has Notes
    to summarize, then writes `summary` + `summary_generated_at`.

## Verified through the real MCP protocol, real Postgres, real flow

Not just that each prompt renders — that the Root Summarizer flow actually produces the Q14
behavior it was designed for:

1. Save two Notes into one Notebook.
2. `get_notebook_contents` — confirmed it returns full content, not the 160-char snippets
   `retrieve`'s derived view uses.
3. `save_notebook_summary` with a synthesized summary.
4. `retrieve` the Notebook — got the roll-up back **verbatim**, no delta (nothing stale yet).
5. Saved a third Note into the same Notebook.
6. `retrieve` again — got the **stale roll-up plus a delta section** naming the new Note by
   id and title. This is the exact Q14 property: a stored summary must never silently omit
   a Note added after it was written.

Also checked prompt argument interpolation (`save_session` with/without `notebook_id`,
`recall` with/without `query`, `summarize_notebook`'s id shows up in its instructions) and two
negative cases (blank summary rejected, unowned/missing `notebook_id` rejected).

## Not yet done

- Real Clerk + Claude Code end-to-end for these prompts and the new tools — see
  `.scratch/phase-3-prompts/issues/01`.
- The "Notebook has notes but summary is 0 notes" negative case for `save_notebook_summary`
  wasn't exercised through the protocol (would need a Notebook with zero Notes, which isn't
  reachable through the public tool surface without a delete tool — deliberately absent,
  ADR-0003). The code path exists and was read-reviewed, just not protocol-tested.
