"""FastAPI host for the spike's MCP server.

Run with: uv run uvicorn spike.app:app --reload
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from spike.config import load_settings
from spike.server import build_server

logging.basicConfig(level=logging.INFO)

settings = load_settings()
mcp_server = build_server(settings)

# Must run before `session_manager` is touched: it raises RuntimeError otherwise.
mcp_app = mcp_server.streamable_http_app()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Run the MCP session manager for the host app's lifetime.

    A mounted sub-application's own lifespan never runs, so without this every request
    to /mcp fails with a RuntimeError.

    Args:
        _ (FastAPI): The host application, unused.

    Yields:
        None: While the session manager is running.
    """
    async with mcp_server.session_manager.run():
        yield


app = FastAPI(title="ai-notes spike", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    """Report that the host app is up, without requiring auth.

    Returns:
        dict: Status plus the resource identifier this server expects in token audiences.
    """
    return {"status": "ok", "resource": settings.resource_url}


app.mount("/", mcp_app)
