"""Shapes Notebook/Note rows into the listing/search/detail views shared by REST and MCP.

Sibling of app/notebook_view.py: that module renders `retrieve`'s text view identically for
both `app/api.py`'s `get_notebook` and `app/tools.py`'s `retrieve`. This module extends the
same shared-implementation-behind-two-seams pattern to the structured (TypedDict) shapes both
surfaces used to define and build independently.
"""

import uuid
from typing import TypedDict

from db.models import Note, Notebook


class NotebookSummary(TypedDict):
    """One entry in a Notebook listing."""

    id: str
    title: str
    note_count: int
    created_at: str
    has_summary: bool


class NoteHit(TypedDict):
    """One entry in a Note search result."""

    id: str
    notebook_id: str
    title: str
    snippet: str
    tags: list[str]
    source_app: str
    created_at: str


class NoteFull(TypedDict):
    """One Note's full content, not a truncated snippet."""

    id: str
    title: str
    summary: str
    tags: list[str]
    source_app: str
    created_at: str


def to_notebook_summary(notebook: Notebook, note_count: int) -> NotebookSummary:
    """Build a `NotebookSummary` from a Notebook row and its Note count.

    Args:
        notebook (Notebook): The Notebook to summarize.
        note_count (int): How many Notes it has.

    Returns:
        NotebookSummary: id, title, note_count, created_at, has_summary.
    """
    return {
        "id": str(notebook.id),
        "title": notebook.title,
        "note_count": note_count,
        "created_at": notebook.created_at.isoformat(),
        "has_summary": notebook.summary is not None,
    }


def to_note_hit(note: Note, snippet: str) -> NoteHit:
    """Build a `NoteHit` from a Note row and its precomputed snippet.

    Args:
        note (Note): The matching Note.
        snippet (str): A truncated preview of the Note's summary (see
            `app.notebook_view.snippet`).

    Returns:
        NoteHit: id, notebook_id, title, snippet, tags, source_app, created_at.
    """
    return {
        "id": str(note.id),
        "notebook_id": str(note.notebook_id),
        "title": note.title,
        "snippet": snippet,
        "tags": note.tags,
        "source_app": note.source_app,
        "created_at": note.created_at.isoformat(),
    }


def to_note_full(note: Note) -> NoteFull:
    """Build a `NoteFull` from a Note row.

    Args:
        note (Note): The Note to render in full.

    Returns:
        NoteFull: id, title, summary, tags, source_app, created_at.
    """
    return {
        "id": str(note.id),
        "title": note.title,
        "summary": note.summary,
        "tags": note.tags,
        "source_app": note.source_app,
        "created_at": note.created_at.isoformat(),
    }


def parse_id(value: str) -> uuid.UUID:
    """Parse a string into a UUID.

    Args:
        value (str): The string to parse.

    Returns:
        uuid.UUID: The parsed UUID.

    Raises:
        ValueError: If `value` is not a valid UUID. Each caller translates this into its own
            transport's error (an HTTP 404 for REST, a re-raised `ValueError` for MCP tools).
    """
    return uuid.UUID(value)
