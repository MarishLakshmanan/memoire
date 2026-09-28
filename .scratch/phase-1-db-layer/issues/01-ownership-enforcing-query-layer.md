# Build the shared ownership-enforcing query layer before wiring any tool

Status: resolved

Q8 from the plan.md grilling session settled on UUIDv7 primary keys plus "a mandatory owner
filter enforced in one shared query layer rather than per-endpoint" as defense in depth for a
multi-tenant app. The id type alone is not the security boundary.

Phase 1's smoke test queried the database directly with no owner filter at all — acceptable
for proving the schema works, not acceptable for a real tool. `Note.owner_id` is already
denormalized onto the row specifically so this filter never needs a join.

## Do this before phase 2 wires any tool to real user data

One module (e.g. `db/repository.py`) with functions like `list_notebooks(session, owner_id)`
and `get_note(session, owner_id, note_id)` that always filter by `owner_id`, so no tool
implementation can accidentally omit it. Every MCP tool should go through this layer, never
issue its own `select()`.

## Answer

Built in phase 2 as `db/repository.py`; all four tools in `app/tools.py` go through it, none
issue their own `select()`. Verified with a dedicated cross-tenant isolation test (two real
MCP client sessions, two different owners) rather than just trusting the code shape — see
`.scratch/phase-2-tools/spec.md`.
