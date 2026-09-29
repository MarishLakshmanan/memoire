"""The browser-facing REST API: list/view/delete, backing the phase 4 frontend.

Everything here goes through db/repository.py, same as the MCP tools, so the owner filter
can't be skipped. Unlike tools.py, this module also deletes — the MCP server deliberately
has no delete tool (docs/adr/0003), so deletion only exists on this path.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.notebook_view import render_notebook_view, snippet
from app.web_auth import ClerkSessionVerifier, build_require_user_id
from db import repository
from db.session import session_scope


def build_api_router(
    session_factory: async_sessionmaker[AsyncSession], verifier: ClerkSessionVerifier
) -> APIRouter:
    """Build the `/api` router.

    Args:
        session_factory (async_sessionmaker[AsyncSession]): Used to open one session per request.
        verifier (ClerkSessionVerifier): Verifies each request's Clerk session token.

    Returns:
        APIRouter: Routes for listing, viewing and deleting Notebooks and Notes.
    """
    router = APIRouter(prefix="/api")
    require_user_id = build_require_user_id(verifier)

    @router.get("/notebooks")
    async def list_notebooks(q: str | None = None, owner_id: str = Depends(require_user_id)) -> list[dict]:
        """List the caller's Notebooks, or search their Notes if `q` is given.

        Args:
            q (str, optional): Free-text search query. Defaults to None (plain listing).
            owner_id (str): Injected from the verified session token.

        Returns:
            list[dict]: Notebook summaries (no `q`), or matching Note hits (with `q`).
        """
        async with session_scope(session_factory) as session:
            if q:
                notes = await repository.search_notes(session, owner_id, q, limit=20)
                return [
                    {
                        "id": str(note.id),
                        "notebook_id": str(note.notebook_id),
                        "title": note.title,
                        "snippet": snippet(note.summary, 200),
                        "tags": note.tags,
                        "source_app": note.source_app,
                        "created_at": note.created_at.isoformat(),
                    }
                    for note in notes
                ]

            notebooks = await repository.list_recent_notebooks(session, owner_id, limit=10)
            return [
                {
                    "id": str(nb.id),
                    "title": nb.title,
                    "note_count": await repository.count_notes(session, nb.id),
                    "created_at": nb.created_at.isoformat(),
                    "has_summary": nb.summary is not None,
                }
                for nb in notebooks
            ]

    @router.get("/notebooks/{notebook_id}")
    async def get_notebook(notebook_id: str, owner_id: str = Depends(require_user_id)) -> dict:
        """Fetch a Notebook's rendered view plus every one of its Notes in full.

        Args:
            notebook_id (str): The Notebook to fetch.
            owner_id (str): Injected from the verified session token.

        Returns:
            dict: `id`, `title`, `view` (the retrieve-style rendered text) and `notes`.

        Raises:
            HTTPException: 404 if no such Notebook is owned by the caller.
        """
        parsed_id = _parse_uuid(notebook_id)
        async with session_scope(session_factory) as session:
            notebook = await repository.get_notebook(session, owner_id, parsed_id)
            if notebook is None:
                raise HTTPException(status_code=404, detail="Notebook not found.")

            notes = await repository.list_notes(session, owner_id, parsed_id)
            return {
                "id": str(notebook.id),
                "title": notebook.title,
                "view": render_notebook_view(notebook, notes),
                "notes": [
                    {
                        "id": str(note.id),
                        "title": note.title,
                        "summary": note.summary,
                        "tags": note.tags,
                        "source_app": note.source_app,
                        "chat_link": note.chat_link,
                        "created_at": note.created_at.isoformat(),
                    }
                    for note in notes
                ],
            }

    @router.delete("/notebooks/{notebook_id}", status_code=204)
    async def delete_notebook(notebook_id: str, owner_id: str = Depends(require_user_id)) -> None:
        """Delete a Notebook and all of its Notes.

        Args:
            notebook_id (str): The Notebook to delete.
            owner_id (str): Injected from the verified session token.

        Raises:
            HTTPException: 404 if no such Notebook is owned by the caller.
        """
        async with session_scope(session_factory) as session:
            deleted = await repository.delete_notebook(session, owner_id, _parse_uuid(notebook_id))
        if not deleted:
            raise HTTPException(status_code=404, detail="Notebook not found.")

    @router.delete("/notebooks/{notebook_id}/notes/{note_id}", status_code=204)
    async def delete_note(notebook_id: str, note_id: str, owner_id: str = Depends(require_user_id)) -> None:
        """Delete a single Note out of a Notebook.

        `notebook_id` is only used to keep the URL shape consistent with `get_notebook`;
        deletion itself is scoped by `note_id` and `owner_id`.

        Args:
            notebook_id (str): The Note's Notebook. Not otherwise checked.
            note_id (str): The Note to delete.
            owner_id (str): Injected from the verified session token.

        Raises:
            HTTPException: 404 if no such Note is owned by the caller.
        """
        _parse_uuid(notebook_id)
        async with session_scope(session_factory) as session:
            deleted = await repository.delete_note(session, owner_id, _parse_uuid(note_id))
        if not deleted:
            raise HTTPException(status_code=404, detail="Note not found.")

    return router


def _parse_uuid(value: str) -> uuid.UUID:
    """Parse a path parameter into a UUID, raising a client-friendly error on failure.

    Args:
        value (str): The string to parse.

    Returns:
        uuid.UUID: The parsed UUID.

    Raises:
        HTTPException: 404 if `value` is not a valid UUID — treated as not-found rather
            than a validation error, so malformed ids don't leak anything about real ones.
    """
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Not found.") from exc
