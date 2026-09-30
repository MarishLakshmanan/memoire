"""Shared JWT decode-and-validate core for the two Clerk verifiers.

app/auth.py's ClerkTokenVerifier (MCP OAuth access tokens) and app/web_auth.py's
ClerkSessionVerifier (browser Clerk session tokens) both need to decode a Clerk-signed RS256
JWT, requiring the same exp/iss/sub claims and logging the same way on rejection. What
genuinely differs between them — audience matching and AccessToken construction versus a
plain `sub` return — stays in each verifier; only the decode-and-catch step lives here.
"""

import logging
from typing import Any

import jwt

logger = logging.getLogger(__name__)


def decode_clerk_jwt(
    token: str,
    issuer: str,
    public_key: str,
    require_audience: bool,
    audience: str | None = None,
) -> dict[str, Any] | None:
    """Check a Clerk-issued JWT's signature, issuer and expiry, returning its claims.

    Args:
        token (str): The raw bearer token from the Authorization header.
        issuer (str): Clerk instance URL that issued the token, with no trailing slash.
        public_key (str): PEM-encoded RSA public key for the Clerk instance.
        require_audience (bool): True to have PyJWT itself verify `aud` against `audience`.
            False to skip audience verification here entirely (a caller that still needs to
            inspect `aud` does so on the returned claims).
        audience (str, optional): The value `aud` must match, when `require_audience` is True.
            Defaults to None (only valid when `require_audience` is False).

    Returns:
        dict[str, Any] | None: The decoded claims if the token is validly signed, unexpired,
            issued by `issuer`, and carries `exp`/`iss`/`sub`; otherwise None.
    """
    try:
        return jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer=issuer,
            audience=audience if require_audience else None,
            options={"require": ["exp", "iss", "sub"], "verify_aud": require_audience},
        )
    except jwt.PyJWTError as exc:
        logger.warning("Token rejected: %s", exc)
        return None
