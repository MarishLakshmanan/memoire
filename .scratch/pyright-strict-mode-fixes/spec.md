Status: open

# Fix the 27 pre-existing pyright strict-mode errors blocking the pre-commit hook

## Problem Statement

The pre-commit setup added in this session wires `pyright` in as a blocking hook, running in the
strict mode `pyrightconfig.json` already specifies. Because pyright had never actually been run as
a gate before, it surfaces 27 pre-existing type errors across `app/api.py`, `app/app.py`,
`app/server.py`, `app/tools.py`, `db/repository.py`, and `db/session.py` — none introduced by the
hook setup itself. Since the hook always type-checks the whole configured project rather than only
the files in a commit, any commit touching anything under `app/` or `db/` fails right now,
regardless of what that commit actually changes. Backend development is effectively blocked until
this backlog is cleared.

## Solution

Fix all 27 pyright findings with no change in runtime behavior, so `uv run pyright` — and
therefore the pre-commit hook — passes with zero errors and stops blocking ordinary backend
commits.

## User Stories

1. As a backend developer, I want `uv run pyright` to pass with zero errors, so that the
   pre-commit hook stops blocking commits unrelated to type-checking.
2. As a backend developer, I want the `/api/notebooks` and `/api/notebooks/{id}` REST responses to
   have precise typed shapes, so that pyright can verify their fields match what the frontend
   actually consumes.
3. As a contributor extending the REST API, I want each response shape declared as a `TypedDict`,
   so that the REST layer follows the same convention CLAUDE.md already mandates for MCP tool
   return types.
4. As a backend developer, I want `_require_subject` to handle a missing access token explicitly,
   so that pyright confirms every caller is protected against a `None` token rather than assuming
   the MCP SDK always supplies one.
5. As an operator running this server, I want `_require_subject` to raise a clear, deliberate
   error when no access token is present, so that an auth misconfiguration fails loudly instead of
   surfacing as an unrelated attribute error.
6. As a backend developer, I want `AuthSettings`'s `issuer_url` and `resource_server_url` built
   from validated `AnyHttpUrl` values, so that a malformed `CLERK_ISSUER` or `MCP_RESOURCE_URL`
   environment variable is caught at startup instead of silently passed through as a raw string.
7. As a backend developer, I want `ClerkTokenVerifier` and `Settings` to keep treating the issuer
   and resource URL as plain strings, so that the string-equality checks in the JWT
   audience/issuer validation logic aren't disturbed by this fix.
8. As a backend developer, I want `Notebook` and `Note` construction to keep not requiring `id`
   and `created_at` to be passed explicitly, so that `repository.create_notebook` and
   `repository.create_note` keep their existing call shape.
9. As a backend developer, I want `Notebook.id`/`Note.id` and `created_at` to still be generated
   exactly as they are today (uuid7 ids, Postgres `now()` timestamps), so that this fix changes
   only what pyright sees, not what the database stores.
10. As a backend developer, I want `Notebook.created_at.desc()` and `Note.created_at` to keep
    working as `order_by(...)` expressions, so that `list_recent_notebooks` and `list_notes` keep
    returning results in the same order.
11. As a backend developer, I want the `session_scope` and FastAPI `lifespan` async context
    managers to use the currently-recommended `AsyncGenerator` return-type annotation, so that
    pyright stops flagging the deprecated `AsyncIterator` annotation style.
12. As a backend developer, I want none of these fixes to change any HTTP status code, MCP tool
    output shape, or database schema, so that the frontend and existing MCP clients need no
    changes.
13. As a reviewer, I want each fix scoped to the smallest change that resolves its specific
    pyright error, so that this cleanup doesn't turn into an unrelated refactor of auth or
    repository logic.
14. As a backend developer, I want `pyrightconfig.json`'s `typeCheckingMode: strict` left
    untouched, so that this fix raises the codebase to meet the existing bar rather than lowering
    the bar to meet the codebase.
15. As a future contributor, I want the fixed models to demonstrate the correct SQLModel
    field-declaration pattern for auto-generated ids and timestamps, so that new models added
    later don't reintroduce the same pyright errors.
16. As a backend developer, I want each fix verified by running the MCP tools and REST endpoints
    against the real Clerk-protected dev server, so that a behavioral regression pyright itself
    can't see (e.g. a `TypedDict` missing a field FastAPI still serializes) gets caught.
17. As a team relying on the pre-commit hook, I want this fix committed as its own change, so that
    `git blame` on `app/`/`db/` isn't cluttered by an unrelated hook-setup commit.
18. As a backend developer, I want the `AccessToken | None` call sites in `tools.py` fixed by
    narrowing at a single seam, so that the fix doesn't need six near-identical inline null checks
    scattered through the module.

## Implementation Decisions

- **`app/api.py`**: introduce `TypedDict`s for every REST response currently typed as a bare
  `dict`/`list[dict]` — a Notebook summary (id, title, note count, created-at, whether it has a
  Roll-up Summary), a Note search hit (id, notebook id, title, snippet, tags, Source App,
  created-at), a Note detail (id, title, summary, tags, Source App, Chat Link, created-at), and a
  Notebook detail (id, title, rendered view, list of Note details). `list_notebooks` returns a
  union of the summary-list and search-hit-list shapes depending on whether `q` is given;
  `get_notebook` returns the Notebook detail shape. Field names and types must match what
  `frontend/src/api.ts`'s existing TypeScript types already expect — no response field is renamed.
- **`app/app.py`**: add a small `TypedDict` for the `/health` endpoint's `status`/`resource` body,
  following the same convention `app/tools.py` already established for MCP tool returns (see
  CLAUDE.md, "Tool return types must be `TypedDict`s").
- **`app/server.py`**: at the single `AuthSettings(...)` construction inside `build_server`, wrap
  `settings.clerk_issuer` and `settings.resource_url` in `AnyHttpUrl(...)` only for that call.
  `app/config.py`'s `Settings` fields and `app/auth.py`'s `ClerkTokenVerifier` keep their current
  plain-`str` typing and string-equality comparisons — the conversion is local to this one call
  site, not a change to how the value is stored or compared elsewhere.
- **`app/tools.py`**: widen `_require_subject`'s parameter type from `AccessToken` to
  `AccessToken | None`, and have it raise when the token is `None`, before extracting the subject
  claim. All six call sites keep calling `_require_subject(get_access_token())` unchanged — only
  `_require_subject` itself changes, becoming the single point where a missing access token is a
  checked, explicit failure instead of an unchecked assumption.
- **`db/models.py`**: move `Notebook.id`/`Note.id` and `Notebook.created_at`/`Note.created_at` off
  a raw `sa_column=Column(...)` declaration and onto SQLModel's own `Field(default_factory=...,
  sa_column_kwargs={...})` form (keeping `primary_key=True` for `id`; keeping
  `server_default=sa_func.now()`/`nullable=False` for `created_at` via `sa_column_kwargs`). This is
  the root cause of both `db/repository.py` error classes: SQLModel's synthesized constructor and
  its class-level attribute typing (which `.desc()` in `order_by(...)` depends on) only pick up
  field defaults declared this way, not ones buried inside an explicit `sa_column=Column(...)`. No
  column type, nullability, default value, or generated value changes at the database level — only
  how the same defaults are declared to SQLModel and pyright.
- **`db/repository.py`**: no call-site changes expected once `db/models.py` is fixed —
  `create_notebook`, `create_note`, `list_recent_notebooks`, and `list_notes` keep their current
  construction and `order_by(...)` calls.
- **`app/app.py`, `db/session.py`**: change the `@asynccontextmanager`-decorated functions' return
  type from `AsyncIterator[Foo]` to `AsyncGenerator[Foo]` (importing `AsyncGenerator` from
  `collections.abc`), per pyright's `reportDeprecated` guidance. No change to the generator body.
- No change to `pyrightconfig.json` (`typeCheckingMode: strict` stays), `.pre-commit-config.yaml`,
  any MCP tool signature, any HTTP route path/status code, or the database schema/migrations.

## Testing Decisions

- A good test here only confirms two things: pyright reports zero errors, and nothing that
  previously worked now behaves differently — it should not pin down implementation details like
  the exact `TypedDict` field order.
- No automated test suite exists in this repo yet (no pytest, no `tests/` directory). The
  automated seam is `uv run pyright` itself — the same command the pre-commit hook already runs —
  and "0 errors, 0 warnings, 0 informations" is the pass/fail criterion.
- Behavior-preservation is verified manually against the real dev stack, the same way prior phases
  were verified: run `uv run uvicorn app.app:app --reload`, exercise each of the six MCP tools once
  through a real Clerk-authenticated client, and exercise `GET /api/notebooks`,
  `GET /api/notebooks/{id}`, and the two delete routes through the real frontend or a REST client
  carrying a real Clerk session token.
- No new test infrastructure (pytest, fixtures, mocks) is introduced as part of this fix — the
  user explicitly deferred that as a separate decision.
- Prior art for this verification style:
  `.scratch/phase-2-tools/issues/01-real-clerk-end-to-end-for-real-tools.md` and
  `.scratch/phase-4-frontend/issues/01-real-browser-clerk-login-end-to-end.md`.

## Out of Scope

- Introducing pytest or any automated test framework.
- Any change to `pyrightconfig.json`'s strict mode, `.pre-commit-config.yaml`, or the ruff/bandit
  hook configuration already committed.
- Any change to the REST API's URL paths, status codes, or the MCP tools' external
  behavior/signatures.
- Any database schema or migration change — id/created_at generation, types, and constraints stay
  identical at the Postgres level.
- Committing the pre-existing, currently-uncommitted changes to `pyproject.toml`, `uv.lock`,
  `app/tools.py`, `migrations/env.py`, the two migration version files, and `skills-lock.json` that
  predate this spec — those are tracked separately.
- Broader auth or repository refactors beyond what's needed to satisfy pyright.

## Further Notes

- This spec exists because `.pre-commit-config.yaml` (added earlier in this working session) wires
  `pyright` in as a blocking hook against the project's already-strict `pyrightconfig.json`; see
  CLAUDE.md's "Running it" section.
- The new `app/api.py` TypedDicts should be cross-checked against `frontend/src/api.ts`'s existing
  TypeScript types once implemented, since the two aren't type-shared today (no
  `packages/contracts` in this single-repo layout) and could silently drift.
- The `AccessToken | None` fix in `app/tools.py` is worth double-checking against the MCP Python
  SDK's actual runtime guarantee — confirm `get_access_token()` really returns `None` only when
  called outside an authenticated request context — so the raised error message is accurate.
- `db/models.py` and `db/repository.py` currently carry only the ruff line-wrap fixes from the
  pre-commit-hooks commit (held back from that commit specifically to avoid tripping the blocking
  pyright hook). This fix's changes to those same two files should land together with that
  held-back diff rather than as a separate, conflicting change.
- This project's issue tracker (`docs/agents/issue-tracker.md`) uses a `Status: open|resolved`
  line rather than a labeling system — no `ready-for-agent` label was applied since that
  vocabulary isn't configured for this project (see `/setup-matt-pocock-skills`).
