"""The MCP tools: save_note, retrieve, list_notebooks, search_notes, and the pair
get_notebook_contents / save_notebook_summary used by the summarize_notebook prompt.

Every tool resolves `owner_id` from the verified access token (never from a parameter — a
model could never be trusted to supply it), and goes through db/repository.py rather than
querying directly, so the owner filter from Q8 can't be forgotten per-tool.
"""

import uuid
from datetime import UTC, datetime
from typing import TypedDict

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.mcpserver import MCPServer
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.notebook_view import render_notebook_view, snippet
from app.source_app import resolve_source_app
from db import repository
from db.session import session_scope


class SaveNoteResult(TypedDict):
    """What `save_note` returns."""

    notebook_id: str
    note_id: str
    notebook_created: bool
    title: str


class NotebookSummary(TypedDict):
    """One entry in `list_notebooks`'s result."""

    id: str
    title: str
    note_count: int
    created_at: str
    has_summary: bool


class NoteHit(TypedDict):
    """One entry in `search_notes`'s result."""

    id: str
    notebook_id: str
    title: str
    snippet: str
    tags: list[str]
    source_app: str
    created_at: str


class NoteFull(TypedDict):
    """One entry in `get_notebook_contents`'s result — full content, not a snippet."""

    id: str
    title: str
    summary: str
    tags: list[str]
    source_app: str
    created_at: str


class SaveSummaryResult(TypedDict):
    """What `save_notebook_summary` returns."""

    notebook_id: str
    summary_generated_at: str


def register_tools(server: MCPServer, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Register the four Notebook/Note tools on an MCPServer.

    Args:
        server (MCPServer): The server to register tools on.
        session_factory (async_sessionmaker[AsyncSession]): Used to open one session per tool call.
    """

    @server.tool()
    async def save_note(
        summary: str,
        title: str,
        notebook_id: str | None = None,
        notebook_title: str | None = None,
        tags: list[str] | None = None,
        chat_link: str | None = None,
    ) -> SaveNoteResult:
        """Save a summary of the current chat session as a Note.

        Args:
            summary (str): Markdown summary of the CURRENT session only — don't re-summarize
                or distill previous sessions, and don't fabricate anything not in this chat.
            title (str): A short, descriptive title for this Note.
            notebook_id (str, optional): An existing Notebook's id to append to. Defaults to
                None, which starts a new Notebook.
            notebook_title (str, optional): Title for a new Notebook. Only used when
                `notebook_id` is None. Defaults to None, which reuses `title`.
            tags (list[str], optional): Free-text topical labels. Defaults to None (no tags).
            chat_link (str, optional): URL to this conversation, only if you actually know
                it — never invent one. Defaults to None.

        Returns:
            SaveNoteResult: `notebook_id`, `note_id`, `notebook_created` (bool), and `title`.

        Raises:
            ValueError: If `notebook_id` is given but not a valid id, or doesn't exist, or
                isn't owned by the caller.
        """
        token = _require_token(get_access_token())
        owner_id = _require_subject(token)
        source_app = resolve_source_app(token.client_id)

        async with session_scope(session_factory) as session:
            if notebook_id is None:
                notebook = await repository.create_notebook(
                    session, owner_id, notebook_title or title
                )
                target_notebook_id = notebook.id
                created = True
            else:
                target_notebook_id = _parse_uuid(notebook_id, "notebook_id")
                created = False

            note = await repository.add_note(
                session,
                owner_id,
                target_notebook_id,
                title=title,
                summary=summary,
                source_app=source_app,
                tags=tags or [],
                chat_link=chat_link,
            )
            if note is None:
                raise ValueError(f"No Notebook {notebook_id!r} found for this account.")

            return {
                "notebook_id": str(target_notebook_id),
                "note_id": str(note.id),
                "notebook_created": created,
                "title": note.title,
            }

    @server.tool()
    async def retrieve(id: str) -> str:
        """Retrieve a Notebook or a Note by id.

        Args:
            id (str): A Notebook id or Note id, from a previous save_note, list_notebooks,
                or search_notes call.

        Returns:
            str: For a Notebook id — its Roll-up Summary if one exists and is current,
                otherwise a Derived Summary listing its Notes (with their ids, so you can
                retrieve any one of them directly). For a Note id — that Note's full content.

        Raises:
            ValueError: If `id` isn't a valid id, or matches neither a Notebook nor a Note
                owned by the caller.
        """
        token = get_access_token()
        owner_id = _require_subject(token)
        parsed_id = _parse_uuid(id, "id")

        async with session_scope(session_factory) as session:
            notebook = await repository.get_notebook(session, owner_id, parsed_id)
            if notebook is not None:
                notes = await repository.list_notes(session, owner_id, parsed_id)
                return render_notebook_view(notebook, notes)

            note = await repository.get_note(session, owner_id, parsed_id)
            if note is not None:
                return (
                    f"# {note.title}\n\n"
                    f"Notebook: {note.notebook_id}\n"
                    f"Source: {note.source_app}\n"
                    f"Tags: {', '.join(note.tags) or 'none'}\n"
                    f"Chat link: {note.chat_link or 'none'}\n"
                    f"Saved: {note.created_at.isoformat()}\n\n"
                    f"{note.summary}"
                )

            raise ValueError(f"No Notebook or Note found with id {id!r}.")

    @server.tool()
    async def list_notebooks(limit: int = 10) -> list[NotebookSummary]:
        """List the caller's most recently created Notebooks.

        Args:
            limit (int, optional): Maximum number of Notebooks to return. Defaults to 10.

        Returns:
            list[NotebookSummary]: Newest first.
        """
        token = get_access_token()
        owner_id = _require_subject(token)

        async with session_scope(session_factory) as session:
            notebooks = await repository.list_recent_notebooks(session, owner_id, limit)
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

    @server.tool()
    async def search_notes(query: str, limit: int = 20) -> list[NoteHit]:
        """Full-text search the caller's Notes by title and summary.

        Args:
            query (str): Free-text search terms.
            limit (int, optional): Maximum number of results. Defaults to 20.

        Returns:
            list[NoteHit]: Best match first.
        """
        token = get_access_token()
        owner_id = _require_subject(token)

        async with session_scope(session_factory) as session:
            notes = await repository.search_notes(session, owner_id, query, limit)
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

    @server.tool()
    async def get_notebook_contents(notebook_id: str) -> list[NoteFull]:
        """Fetch every Note in a Notebook in full — not truncated snippets.

        For writing a Roll-up Summary: read the full content this returns, then call
        `save_notebook_summary`. Not meant for casual browsing — use `retrieve` for that.

        Args:
            notebook_id (str): The Notebook to fetch.

        Returns:
            list[NoteFull]: Every Note, oldest first.

        Raises:
            ValueError: If `notebook_id` isn't a valid id, or isn't owned by the caller.
        """
        token = get_access_token()
        owner_id = _require_subject(token)
        parsed_id = _parse_uuid(notebook_id, "notebook_id")

        async with session_scope(session_factory) as session:
            notebook = await repository.get_notebook(session, owner_id, parsed_id)
            if notebook is None:
                raise ValueError(f"No Notebook found with id {notebook_id!r}.")

            notes = await repository.list_notes(session, owner_id, parsed_id)
            return [
                {
                    "id": str(note.id),
                    "title": note.title,
                    "summary": note.summary,
                    "tags": note.tags,
                    "source_app": note.source_app,
                    "created_at": note.created_at.isoformat(),
                }
                for note in notes
            ]

    @server.tool()
    async def save_notebook_summary(notebook_id: str, summary: str) -> SaveSummaryResult:
        """Save a Roll-up Summary for a Notebook, synthesized across all its Notes.

        Call `get_notebook_contents` first to read what you're summarizing.

        Args:
            notebook_id (str): The Notebook to save the summary to.
            summary (str): The synthesized summary, markdown. Should read as one narrative
                across sessions, not a concatenation of the individual Note summaries.

        Returns:
            SaveSummaryResult: `notebook_id` and `summary_generated_at` (ISO 8601).

        Raises:
            ValueError: If `notebook_id` isn't valid or owned, `summary` is blank, or the
                Notebook has no Notes yet (nothing to summarize).
        """
        if not summary.strip():
            raise ValueError("summary is blank.")

        token = get_access_token()
        owner_id = _require_subject(token)
        parsed_id = _parse_uuid(notebook_id, "notebook_id")

        async with session_scope(session_factory) as session:
            notes = await repository.list_notes(session, owner_id, parsed_id)
            if not notes:
                notebook = await repository.get_notebook(session, owner_id, parsed_id)
                if notebook is None:
                    raise ValueError(f"No Notebook found with id {notebook_id!r}.")
                raise ValueError(
                    f"Notebook {notebook_id!r} has no Notes yet; nothing to summarize."
                )

            generated_at = datetime.now(UTC)
            notebook = await repository.save_notebook_summary(
                session, owner_id, parsed_id, summary, generated_at
            )
            if notebook is None:
                raise ValueError(f"No Notebook found with id {notebook_id!r}.")

            return {
                "notebook_id": str(parsed_id),
                "summary_generated_at": generated_at.isoformat(),
            }


def _require_token(token: AccessToken | None) -> AccessToken:
    """Guarantee an access token is present in context.

    The single place that turns a missing token into a checked failure, so callers that
    need the token itself (not just its subject) can narrow it without repeating this check.

    Args:
        token (AccessToken | None): The access token returned by `get_access_token()`.

    Returns:
        AccessToken: The same token, narrowed to non-`None`.

    Raises:
        ValueError: If there is no token in context.
    """
    if token is None:
        raise ValueError("No access token in context; cannot determine the owner.")
    return token


def _require_subject(token: AccessToken | None) -> str:
    """Extract the Clerk user id from a verified access token.

    Args:
        token (AccessToken | None): The access token returned by `get_access_token()`.

    Returns:
        str: The token's `subject` claim, used as `owner_id` everywhere.

    Raises:
        ValueError: If there is no token, or it has no `subject` — a Clerk token always
            should, so either signals a misconfigured verifier rather than a normal
            runtime condition.
    """
    subject = _require_token(token).subject
    if not subject:
        raise ValueError("Access token has no subject; cannot determine the owner.")
    return subject


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    """Parse a string into a UUID, raising a caller-friendly error on failure.

    Args:
        value (str): The string to parse.
        field_name (str): Which parameter this came from, for the error message.

    Returns:
        uuid.UUID: The parsed UUID.

    Raises:
        ValueError: If `value` is not a valid UUID.
    """
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise ValueError(f"{field_name!r} is not a valid id: {value!r}") from exc
