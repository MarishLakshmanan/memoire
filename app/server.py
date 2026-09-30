"""Builds the MCP server: Clerk auth plus the Notebook/Note tools and prompts."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.applications import Starlette

from app.auth import ClerkTokenVerifier
from app.config import Settings
from app.prompts import register_prompts
from app.tools import register_tools


@dataclass
class MountedMCPServer:
    """The MCP server's ASGI app, already built in the order the SDK requires.

    `MCPServer.streamable_http_app()` must be called before `session_manager` is ever touched
    — calling them out of order raises `RuntimeError`. `build_server` calls
    `streamable_http_app()` itself before returning, so this ordering is guaranteed by the time
    a host app has anything to hold onto; the host only needs to mount `asgi_app` and enter
    `lifespan()` for the app's lifetime, in either order, whenever it likes.
    """

    asgi_app: Starlette
    _server: MCPServer

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[None]:
        """Run the MCP session manager for the lifetime of the host app.

        A mounted sub-application's own lifespan never runs, so a host app must enter this
        itself — otherwise every request to the mounted MCP routes fails with `RuntimeError`.

        Yields:
            None: While the session manager is running.
        """
        async with self._server.session_manager.run():
            yield


def build_server(
    settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> MountedMCPServer:
    """Build the MCP server with Clerk auth and the Notebook/Note tools and prompts.

    Args:
        settings (Settings): Configuration resolved from the environment.
        session_factory (async_sessionmaker[AsyncSession]): Used by tools to open sessions.

    Returns:
        MountedMCPServer: The server's ASGI app, ready to mount, plus its lifespan.
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
        # Passed as plain strings, not pre-wrapped in AnyHttpUrl: pydantic validates and
        # coerces them using AuthSettings' own field config (url_preserve_empty_path=True,
        # required for exact RFC 8414 issuer-string matching). A bare AnyHttpUrl(...)
        # constructed outside that model applies different defaults and silently appends a
        # trailing slash to a path-less issuer, corrupting it — this is deliberately not that.
        auth=AuthSettings(
            issuer_url=settings.clerk_issuer,  # pyright: ignore[reportArgumentType]
            resource_server_url=settings.resource_url,  # pyright: ignore[reportArgumentType]
            validate_token_resource=settings.is_production,
        ),
    )

    register_tools(server, session_factory)
    register_prompts(server)

    return MountedMCPServer(asgi_app=server.streamable_http_app(), _server=server)
