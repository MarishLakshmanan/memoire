Status: open

# Extract the shared JWT-decode core from the two Clerk verifiers

## Problem Statement

`app/web_auth.py`'s `ClerkSessionVerifier.verify` and `app/auth.py`'s
`ClerkTokenVerifier.verify_token` each independently call `jwt.decode(token, self._public_key,
algorithms=["RS256"], issuer=self._issuer, ...)` wrapped in an identical `try/except
jwt.PyJWTError` that logs a warning and returns `None`. The `options={"require": ["exp", "iss",
"sub"]}` literal is copied verbatim into both files. This is duplicated implementation, not two
thin adapters over one shared core: deleting either verifier and trying to derive it from the
other would require recreating that decode/catch block identically. A bug in how either one
handles a malformed or expired token (or a change to the required-claims list) has to be applied
twice by hand.

## Solution

Factor the decode-and-catch core into one shared function both verifiers call, keeping the parts
that genuinely differ — audience matching and `AccessToken` construction in `ClerkTokenVerifier`,
versus the plain `sub`-only return in `ClerkSessionVerifier` — as the two real adapters at the
point where MCP access tokens and Clerk session tokens actually diverge.

## User Stories

1. As a backend maintainer, I want the JWT decode-and-validate step written once, so that a fix to
   how a malformed or expired token is handled applies to both the MCP access-token path and the
   REST session-token path without editing two files.
2. As a backend maintainer, I want the required-claims list (`exp`, `iss`, `sub`) declared once, so
   that changing it can't be done for one verifier and forgotten for the other.
3. As an MCP client user, I want `ClerkTokenVerifier`'s audience validation, `client_id`/`scopes`
   extraction, and `AccessToken` construction to behave exactly as they do today, so this refactor
   changes no MCP auth behavior.
4. As a frontend user signed in via Clerk, I want `ClerkSessionVerifier` to keep accepting the same
   session tokens and rejecting the same invalid ones it does today, so login and every
   Clerk-session-authenticated REST call keep working unchanged.
5. As a backend maintainer, I want the shared decode function to take the issuer, public key, and
   whether to require/verify an audience as plain parameters, so it has no dependency on either
   `Settings` or the MCP SDK's `AccessToken` type.
6. As a backend maintainer, I want `ClerkTokenVerifier`'s development-mode audience-skip behavior
   (and its startup warning log) to stay exactly where it is, so the shared function doesn't need
   to know about `APP_ENV` or production-vs-development policy.
7. As a security reviewer, I want the shared function to be the single place that logs a rejected
   token, so the two verifiers can't drift into logging different amounts of detail about a
   rejection.
8. As a backend maintainer, I want this refactor to touch no route, no tool registration, and no
   `Settings` field, so it's reviewable purely as consolidating verification logic.
9. As a backend maintainer, I want `app/tools.py`'s `_require_token` reassessed now that this spec
   touches the token-handling code nearby: if `save_note` remains its only caller that needs the
   raw token (for `client_id`), inline the null-check into `save_note` and have `_require_subject`
   perform its own null check directly, removing the now-redundant named indirection — only if this
   doesn't complicate `_require_subject`'s own error message.
10. As a future contributor adding a third Clerk-issued token type, I want one shared decode
    function to extend rather than a third copy of the decode/catch block to write.

## Implementation Decisions

- New shared function (placed in `app/`, alongside `auth.py`/`web_auth.py` — flat layout, no
  feature-folder restructuring) that takes a token string, issuer, public key, and a
  require/verify-audience flag, runs `jwt.decode(...)` with the shared `options={"require": [...]}`
  claims list, and returns the decoded claims dict or `None` (logging the rejection reason exactly
  as today) on `jwt.PyJWTError`.
- `ClerkTokenVerifier.verify_token` calls the shared function, then keeps its existing
  audience-matching (`_matching_audience`), development-mode warning, and `AccessToken`
  construction unchanged.
- `ClerkSessionVerifier.verify` calls the shared function with audience verification off, then
  keeps its existing plain `claims.get("sub")` return unchanged.
- Both verifiers keep their own class, constructor, and public method signatures — callers in
  `app/server.py` (`ClerkTokenVerifier`) and `app/app.py`/`app/api.py`
  (`ClerkSessionVerifier`/`build_require_user_id`) need no changes.
- `_require_token`/`_require_subject` in `app/tools.py`: assessed per user story 9, resolved during
  implementation rather than dictated here, since it's a small, optional cleanup riding along with
  this spec rather than its own line item.

## Testing Decisions

- A good test here confirms both verifiers still accept a validly-signed token and reject an
  expired one, a wrong-issuer one, and one missing a required claim — the same behavior they have
  today, now going through one shared code path.
- No automated test suite exists in this repo and this spec does not introduce one (pytest is
  explicitly not wanted for this MVP-stage project). Verification is manual against the real dev
  stack, matching this project's established approach: run the real Clerk-protected dev server,
  authenticate a real MCP client to exercise `ClerkTokenVerifier`'s full path (valid token, plus
  letting a token expire or editing `APP_ENV` to confirm the production audience-check branch), and
  sign in through the real frontend to exercise `ClerkSessionVerifier`'s path (valid session,
  expired session, signed-out state). See
  `.scratch/phase-0-auth-spike/issues/01-verify-real-clerk-token-end-to-end.md` and
  `.scratch/phase-4-frontend/issues/01-real-browser-clerk-login-end-to-end.md` for prior art on
  this verification style.
- Any one-off verification script belongs in the session scratchpad directory, not the repo.

## Out of Scope

- Introducing pytest or any automated test framework.
- Any change to `Settings`, `APP_ENV`-gated audience policy, or the RFC 9728 protected-resource
  metadata path.
- Any restructuring toward `src/features/<feature>/`-style folders.
- The Notebook/Note view-shaping duplication between `app/api.py` and `app/tools.py` — tracked
  separately in `.scratch/shared-notebook-view-module/spec.md`.

## Further Notes

- This project's issue tracker (`docs/agents/issue-tracker.md`) uses a `Status: open|resolved`
  line rather than a labeling system — no `ready-for-agent` label was applied since that
  vocabulary isn't configured for this project (see `/setup-matt-pocock-skills`).
- Source: architecture review of `D:\Projects\ai-notes`, 2026-09-29, candidate 2 (Strong) plus
  candidate 6's `_require_token` item.
