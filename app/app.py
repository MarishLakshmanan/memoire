"""FastAPI host for the MCP server and the database engine.

Run with: uv run uvicorn app.app:app --reload
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TypedDict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import build_api_router
from app.config import load_settings
from app.server import build_server
from app.web_auth import ClerkSessionVerifier
from db.session import build_engine, build_session_factory

logging.basicConfig(level=logging.INFO)

settings = load_settings()
engine = build_engine(settings.database_url)
session_factory = build_session_factory(engine)

mcp = build_server(settings, session_factory)
session_verifier = ClerkSessionVerifier(
    issuer=settings.clerk_issuer, public_key=settings.clerk_public_key
)
api_router = build_api_router(session_factory, session_verifier)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    """Run the MCP session manager, and dispose the DB engine on shutdown.

    A mounted sub-application's own lifespan never runs, so without this every request
    to /mcp fails with a RuntimeError.

    Args:
        _ (FastAPI): The host application, unused.

    Yields:
        None: While the session manager is running.
    """
    async with mcp.lifespan():
        yield
    await engine.dispose()


app = FastAPI(title="mémoire", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "DELETE"],
    allow_headers=["Authorization"],
)

app.include_router(api_router)


class HealthStatus(TypedDict):
    """What `/health` returns."""

    status: str
    resource: str


@app.get("/health")
def health() -> HealthStatus:
    """Report that the host app is up, without requiring auth.

    Returns:
        HealthStatus: Status plus the resource identifier this server expects in token audiences.
    """
    return {"status": "ok", "resource": settings.resource_url}


app.mount("/", mcp.asgi_app)
