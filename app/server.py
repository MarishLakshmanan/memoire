"""Builds the MCP server: Clerk auth plus the Notebook/Note tools and prompts."""

from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.auth import ClerkTokenVerifier
from app.config import Settings
from app.prompts import register_prompts
from app.tools import register_tools


def build_server(settings: Settings, session_factory: async_sessionmaker[AsyncSession]) -> MCPServer:
    """Build the MCP server with Clerk auth and the Notebook/Note tools and prompts.

    Args:
        settings (Settings): Configuration resolved from the environment.
        session_factory (async_sessionmaker[AsyncSession]): Used by tools to open sessions.

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
        name="ai-notes",
        version="0.1.0",
        instructions="Save summaries of AI chat sessions and retrieve them from other AI apps.",
        token_verifier=verifier,
        auth=AuthSettings(
            issuer_url=settings.clerk_issuer,
            resource_server_url=settings.resource_url,
            validate_token_resource=settings.is_production,
        ),
    )

    register_tools(server, session_factory)
    register_prompts(server)

    return server
