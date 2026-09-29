# 06: Confirm the pre-commit hook is fully green

**What to build:** The actual outcome the spec exists for: the pyright pre-commit hook stops
blocking ordinary backend commits, because the whole project — not just the files touched by
tickets 01–05 — passes strict-mode pyright with zero errors.

**Blocked by:** 01, 02, 03, 04, 05

**Status:** resolved

- [x] `uv run pyright` (whole project, no path arguments) reports 0 errors, 0 warnings,
      0 informations
- [x] `uv run pre-commit run --all-files` passes every hook: ruff lint, ruff format, pyright,
      bandit, eslint, tsc, npm audit, and the hygiene hooks (trailing-whitespace,
      end-of-file-fixer, check-added-large-files, check-merge-conflict)
- [x] `db/models.py` and `db/repository.py` — now carrying both the pre-existing ruff fixes and
      ticket 05's typing fixes — are committed
- [x] A backend commit touching `app/` or `db/` (e.g. a trivial, reverted comment change) succeeds
      locally without the pyright hook blocking it
