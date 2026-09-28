"""FastAPI host for the MCP server and the database engine.

Run with: uv run uvicorn app.app:app --reload
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import load_settings
from app.server import build_server
from db.session import build_engine, build_session_factory

logging.basicConfig(level=logging.INFO)

settings = load_settings()
engine = build_engine(settings.database_url)
session_factory = build_session_factory(engine)

mcp_server = build_server(settings, session_factory)

# Must run before `session_manager` is touched: it raises RuntimeError otherwise.
mcp_app = mcp_server.streamable_http_app()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Run the MCP session manager, and dispose the DB engine on shutdown.

    A mounted sub-application's own lifespan never runs, so without this every request
    to /mcp fails with a RuntimeError.

    Args:
        _ (FastAPI): The host application, unused.

    Yields:
        None: While the session manager is running.
    """
    async with mcp_server.session_manager.run():
        yield
    await engine.dispose()


app = FastAPI(title="ai-notes", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    """Report that the host app is up, without requiring auth.

    Returns:
        dict: Status plus the resource identifier this server expects in token audiences.
    """
    return {"status": "ok", "resource": settings.resource_url}


app.mount("/", mcp_app)
