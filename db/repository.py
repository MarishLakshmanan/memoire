"""All database access for Notebooks and Notes, always filtered by owner.

No MCP tool should issue its own `select()` — going through this module is what makes the
owner filter from Q8 (docs/adr context: defense in depth for a multi-tenant app) structurally
hard to skip, rather than something every tool author must remember.
"""

import uuid
from datetime import datetime

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from db.models import Note, Notebook


async def create_notebook(session: AsyncSession, owner_id: str, title: str) -> Notebook:
    """Create a new, empty Notebook.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The Clerk user id that will own the Notebook.
        title (str): The Notebook's title.

    Returns:
        Notebook: The newly created Notebook, with its id populated.
    """
    notebook = Notebook(owner_id=owner_id, title=title)
    session.add(notebook)
    await session.flush()
    return notebook


async def get_notebook(session: AsyncSession, owner_id: str, notebook_id: uuid.UUID) -> Notebook | None:
    """Fetch a Notebook by id, scoped to its owner.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The caller's Clerk user id. A Notebook owned by anyone else is
            treated as not found, never as a permission error that would leak its existence.
        notebook_id (uuid.UUID): The Notebook's id.

    Returns:
        Notebook | None: The Notebook if it exists and is owned by `owner_id`, else None.
    """
    return await session.get(Notebook, notebook_id) if await _owned_notebook(session, owner_id, notebook_id) else None


async def _owned_notebook(session: AsyncSession, owner_id: str, notebook_id: uuid.UUID) -> bool:
    """Check whether a Notebook exists and belongs to the given owner.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The Clerk user id to check ownership against.
        notebook_id (uuid.UUID): The Notebook's id.

    Returns:
        bool: True if the Notebook exists and is owned by `owner_id`.
    """
    stmt = select(Notebook.id).where(Notebook.id == notebook_id, Notebook.owner_id == owner_id)
    return (await session.exec(stmt)).first() is not None


async def get_note(session: AsyncSession, owner_id: str, note_id: uuid.UUID) -> Note | None:
    """Fetch a Note by id, scoped to its owner.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The caller's Clerk user id.
        note_id (uuid.UUID): The Note's id.

    Returns:
        Note | None: The Note if it exists and is owned by `owner_id`, else None.
    """
    stmt = select(Note).where(Note.id == note_id, Note.owner_id == owner_id)
    return (await session.exec(stmt)).first()


async def add_note(
    session: AsyncSession,
    owner_id: str,
    notebook_id: uuid.UUID,
    title: str,
    summary: str,
    source_app: str,
    tags: list[str],
    chat_link: str | None,
) -> Note | None:
    """Append a Note to an existing Notebook.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The Clerk user id that must already own the target Notebook.
        notebook_id (uuid.UUID): The Notebook to append to.
        title (str): The Note's title.
        summary (str): Markdown summary of the session.
        source_app (str): Which client saved this Note, derived server-side from the caller's token.
        tags (list[str]): Free-text topical labels.
        chat_link (str | None): Optional URL to the original conversation.

    Returns:
        Note | None: The newly created Note, or None if no Notebook with that id is owned by `owner_id`.
    """
    if not await _owned_notebook(session, owner_id, notebook_id):
        return None
    note = Note(
        notebook_id=notebook_id,
        owner_id=owner_id,
        title=title,
        summary=summary,
        source_app=source_app,
        tags=tags,
        chat_link=chat_link,
    )
    session.add(note)
    await session.flush()
    return note


async def list_notes(session: AsyncSession, owner_id: str, notebook_id: uuid.UUID) -> list[Note]:
    """List a Notebook's Notes, oldest first — the flat sibling order from docs/adr/0001.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The caller's Clerk user id.
        notebook_id (uuid.UUID): The Notebook whose Notes to list.

    Returns:
        list[Note]: The Notebook's Notes ordered by `created_at`. Empty if the Notebook
            doesn't exist, isn't owned by `owner_id`, or has no Notes.
    """
    stmt = (
        select(Note)
        .where(Note.notebook_id == notebook_id, Note.owner_id == owner_id)
        .order_by(Note.created_at)
    )
    return list((await session.exec(stmt)).all())


async def list_recent_notebooks(session: AsyncSession, owner_id: str, limit: int) -> list[Notebook]:
    """List the owner's most recently created Notebooks.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The caller's Clerk user id.
        limit (int): Maximum number of Notebooks to return.

    Returns:
        list[Notebook]: Notebooks owned by `owner_id`, newest first.
    """
    stmt = select(Notebook).where(Notebook.owner_id == owner_id).order_by(Notebook.created_at.desc()).limit(limit)
    return list((await session.exec(stmt)).all())


async def count_notes(session: AsyncSession, notebook_id: uuid.UUID) -> int:
    """Count how many Notes a Notebook has.

    Args:
        session (AsyncSession): The active database session.
        notebook_id (uuid.UUID): The Notebook to count Notes for.

    Returns:
        int: The number of Notes in the Notebook.
    """
    stmt = select(func.count()).select_from(Note).where(Note.notebook_id == notebook_id)
    return (await session.exec(stmt)).one()


async def save_notebook_summary(
    session: AsyncSession, owner_id: str, notebook_id: uuid.UUID, summary: str, generated_at: datetime
) -> Notebook | None:
    """Store a Roll-up Summary for a Notebook.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The caller's Clerk user id.
        notebook_id (uuid.UUID): The Notebook to update.
        summary (str): The generated roll-up summary, markdown.
        generated_at (datetime): When the summary was generated, used later to detect staleness.

    Returns:
        Notebook | None: The updated Notebook, or None if no Notebook with that id is owned by `owner_id`.
    """
    notebook = await get_notebook(session, owner_id, notebook_id)
    if notebook is None:
        return None
    notebook.summary = summary
    notebook.summary_generated_at = generated_at
    session.add(notebook)
    await session.flush()
    return notebook


async def delete_notebook(session: AsyncSession, owner_id: str, notebook_id: uuid.UUID) -> bool:
    """Delete a Notebook and all of its Notes.

    Not used by any MCP tool (docs/adr/0003) — only the web API's delete UI calls this.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The caller's Clerk user id.
        notebook_id (uuid.UUID): The Notebook to delete.

    Returns:
        bool: True if a Notebook was found and deleted, False if none was owned by `owner_id`.
    """
    notebook = await get_notebook(session, owner_id, notebook_id)
    if notebook is None:
        return False
    await session.delete(notebook)
    await session.flush()
    return True


async def delete_note(session: AsyncSession, owner_id: str, note_id: uuid.UUID) -> bool:
    """Delete a single Note out of its Notebook.

    Not used by any MCP tool (docs/adr/0003) — only the web API's delete UI calls this.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The caller's Clerk user id.
        note_id (uuid.UUID): The Note to delete.

    Returns:
        bool: True if a Note was found and deleted, False if none was owned by `owner_id`.
    """
    note = await get_note(session, owner_id, note_id)
    if note is None:
        return False
    await session.delete(note)
    await session.flush()
    return True


async def search_notes(session: AsyncSession, owner_id: str, query: str, limit: int) -> list[Note]:
    """Full-text search a caller's Notes by title and summary.

    Args:
        session (AsyncSession): The active database session.
        owner_id (str): The caller's Clerk user id.
        query (str): Free-text search query.
        limit (int): Maximum number of results.

    Returns:
        list[Note]: Matching Notes, best match first. Requires the GIN index from
            migration f8c1ce335c87; without it this still works, just as a sequential scan.
    """
    tsquery = func.plainto_tsquery("english", query)
    document = func.to_tsvector("english", Note.title + " " + Note.summary)
    stmt = (
        select(Note)
        .where(Note.owner_id == owner_id, document.op("@@")(tsquery))
        .order_by(func.ts_rank(document, tsquery).desc())
        .limit(limit)
    )
    return list((await session.exec(stmt)).all())
