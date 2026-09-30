"""Clerk token verification for this MCP resource server."""

import logging

from mcp.server.auth.provider import AccessToken

from app.clerk_jwt import decode_clerk_jwt

logger = logging.getLogger(__name__)


class ClerkTokenVerifier:
    """Verifies Clerk-issued OAuth access tokens presented to the MCP server.

    Clerk is the authorization server; this process is only a resource server, so it
    validates token signatures against Clerk's public key and never issues tokens.

    Args:
        issuer (str): Clerk instance URL that issues tokens, with no trailing slash.
        resource_url (str): This server's resource identifier, compared against the token's `aud`.
        public_key (str): PEM-encoded RSA public key for the Clerk instance.
        require_audience (bool): True to reject any token whose `aud` is absent or wrong.
            Clerk development instances do not stamp `aud`, so this is False in development
            and must be True in production.
    """

    def __init__(
        self, issuer: str, resource_url: str, public_key: str, require_audience: bool
    ) -> None:
        self._issuer = issuer
        self._resource_url = resource_url
        self._public_key = public_key
        self._require_audience = require_audience

        if not require_audience:
            logger.warning(
                "Audience validation is OFF because APP_ENV=development. Clerk development "
                "instances do not stamp `aud`. This MUST be on in production, or a token "
                "minted for another resource in the same Clerk instance will be accepted here."
            )

    async def verify_token(self, token: str) -> AccessToken | None:
        """Check a bearer token's signature, issuer, expiry and audience.

        Args:
            token (str): The raw bearer token from the Authorization header.

        Returns:
            AccessToken | None: Access info with `resource` taken from the token's `aud`,
                or None if the token failed any check.
        """
        claims = decode_clerk_jwt(
            token,
            self._issuer,
            self._public_key,
            require_audience=self._require_audience,
            audience=self._resource_url,
        )
        if claims is None:
            return None

        audience = self._matching_audience(claims.get("aud"))

        # In development `aud` may be absent, but if Clerk did stamp one it must still match.
        if audience is None and claims.get("aud") is not None:
            logger.warning(
                "Token rejected: aud %r is not %r",
                claims.get("aud"),
                self._resource_url,
            )
            return None

        scope = claims.get("scope") or ""
        return AccessToken(
            token=token,
            client_id=claims.get("azp") or claims.get("client_id") or "",
            scopes=scope.split() if isinstance(scope, str) else list(scope),
            expires_at=claims.get("exp"),
            resource=audience,
            subject=claims.get("sub"),
            claims=claims,
        )

    def _matching_audience(self, aud: str | list[str] | None) -> str | None:
        """Pick the audience entry equal to this server's resource identifier.

        Args:
            aud (str | list[str] | None): The token's `aud` claim, which may be a list.

        Returns:
            str | None: This server's resource URL if present in `aud`, otherwise None.
        """
        if aud is None:
            return None
        candidates = aud if isinstance(aud, list) else [aud]
        return self._resource_url if self._resource_url in candidates else None
