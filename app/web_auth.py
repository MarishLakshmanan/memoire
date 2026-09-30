"""Clerk session verification for the browser-facing REST API.

Distinct from app/auth.py: that module verifies OAuth *access* tokens from MCP clients,
checked against this server's resource identifier. The browser instead holds a Clerk
*session* token from @clerk/clerk-react — same signer and public key, but no
`client_id`/`scopes`/`resource` and no audience to check, since it isn't scoped to this
resource the way an MCP access token is. Both token kinds carry the same Clerk user id in
`sub`, so ownership rows written through either path line up under one `owner_id` space.
"""

from collections.abc import Callable

from fastapi import Header, HTTPException

from app.clerk_jwt import decode_clerk_jwt


class ClerkSessionVerifier:
    """Verifies Clerk session tokens presented by the frontend.

    Args:
        issuer (str): Clerk instance URL that issues tokens, with no trailing slash.
        public_key (str): PEM-encoded RSA public key for the Clerk instance.
    """

    def __init__(self, issuer: str, public_key: str) -> None:
        self._issuer = issuer
        self._public_key = public_key

    def verify(self, token: str) -> str | None:
        """Check a session token's signature, issuer and expiry, and return its subject.

        Args:
            token (str): The raw bearer token from the Authorization header.

        Returns:
            str | None: The Clerk user id from `sub`, or None if the token failed any check.
        """
        claims = decode_clerk_jwt(token, self._issuer, self._public_key, require_audience=False)
        return claims.get("sub") if claims is not None else None


def build_require_user_id(verifier: ClerkSessionVerifier) -> Callable[..., str]:
    """Build a FastAPI dependency that resolves the caller's Clerk user id.

    Args:
        verifier (ClerkSessionVerifier): The verifier to check each request's token against.

    Returns:
        Callable[..., str]: A dependency function returning the authenticated user id.
    """

    def require_user_id(authorization: str | None = Header(default=None)) -> str:
        """Resolve the caller's Clerk user id from the request's session token.

        Args:
            authorization (str, optional): The raw `Authorization` header. Defaults to None.

        Returns:
            str: The authenticated caller's Clerk user id.

        Raises:
            HTTPException: 401 if the header is missing, malformed, or the token is invalid.
        """
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token.")
        user_id = verifier.verify(authorization.removeprefix("Bearer "))
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid or expired session token.")
        return user_id

    return require_user_id
