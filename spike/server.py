"""The MCP server for the phase 0 spike: one diagnostic tool, no domain logic."""

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer

from spike.auth import ClerkTokenVerifier
from spike.config import Settings


def build_server(settings: Settings) -> MCPServer:
    """Build the MCP server with Clerk auth and a single `ping` tool.

    Args:
        settings (Settings): Configuration resolved from the environment.

    Returns:
        MCPServer: A server configured as an OAuth protected resource, not yet mounted.
    """
    verifier = ClerkTokenVerifier(
        issuer=settings.clerk_issuer,
        resource_url=settings.resource_url,
        public_key=settings.clerk_public_key,
        require_audience=settings.is_production,
    )

    server = MCPServer(
        name="ai-notes-spike",
        version="0.0.1",
        instructions="Phase 0 spike. Proves Clerk auth and MCP mounting work end to end.",
        token_verifier=verifier,
        auth=AuthSettings(
            issuer_url=settings.clerk_issuer,
            resource_server_url=settings.resource_url,
            validate_token_resource=settings.is_production,
        ),
    )

    @server.tool()
    def ping() -> dict:
        """Report who the authenticated caller is, to prove the auth chain works.

        Returns:
            dict: The caller's subject and client id, the audience the token was issued
                for, and its scopes. `audience` is None on Clerk development instances.
        """
        token = get_access_token()
        return {
            "ok": True,
            "subject": token.subject,
            "client_id": token.client_id,
            "audience": token.resource,
            "scopes": token.scopes,
        }

    return server
