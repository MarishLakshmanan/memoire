# 01: Extract the shared Clerk JWT decode core

**What to build:** A shared function, placed in `app/` alongside `auth.py`/`web_auth.py`, that
takes a token string, issuer, public key, and a require/verify-audience flag, runs `jwt.decode`
with the shared `options={"require": ["exp", "iss", "sub"]}` claims list, and returns the decoded
claims dict or `None` (logging the rejection reason) on `jwt.PyJWTError`. Purely additive: neither
verifier calls it yet.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] New function (`app/clerk_jwt.py`, `decode_clerk_jwt`) takes the token, issuer, public key,
      an audience-require flag, and an optional `audience` value as plain parameters — no
      dependency on `Settings` or the MCP SDK's `AccessToken` type. `audience` was added beyond
      the original ticket scope once implementation showed `ClerkTokenVerifier` needs to pass a
      specific value to `jwt.decode`'s own `audience=` check, not just a boolean.
- [x] Returns decoded claims on success, `None` on `jwt.PyJWTError`, logging a warning exactly as
      today's two call sites do
- [x] `uv run pyright` reports zero errors
- [x] Verified with a locally-signed RSA test token: valid, expired, wrong issuer, missing `sub`,
      matching audience, mismatched audience, and audience-required-but-absent all
      accepted/rejected as expected (7/7 cases)
