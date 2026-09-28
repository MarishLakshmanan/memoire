"""SQLModel table definitions for Notebooks and Notes.

Vocabulary and relationships follow CONTEXT.md and docs/adr/0001 (flat Notes, no tree).
"""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Column, DateTime, ForeignKey, String
from sqlalchemy import func as sa_func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel
from uuid6 import uuid7


class Notebook(SQLModel, table=True):
    """The top-level container for one project or topic (see CONTEXT.md).

    `summary` is the Roll-up Summary and is null until a user explicitly requests one;
    retrieval falls back to a Derived Summary assembled from child Notes when it's absent
    or stale. That fallback is computed at query time, not stored here.
    """

    id: uuid.UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid7))
    owner_id: str = Field(index=True, description="Clerk user id that owns this Notebook.")
    title: str

    summary: str | None = Field(default=None, description="Roll-up Summary, markdown. Null until generated.")
    summary_generated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
        description="When `summary` was written. Compared against notes' created_at to detect staleness.",
    )

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=sa_func.now(), nullable=False)
    )

    notes: list["Note"] = Relationship(
        back_populates="notebook",
        # Deletion is enforced by the FK's ON DELETE CASCADE in Postgres, not by the ORM:
        # without passive_deletes, SQLAlchemy's default behavior on parent delete is to
        # UPDATE children's notebook_id to NULL first, which violates its NOT NULL constraint.
        sa_relationship_kwargs={"passive_deletes": True},
    )


class Note(SQLModel, table=True):
    """A summary of a single AI chat session, saved into a Notebook (see CONTEXT.md).

    Notes are flat siblings ordered by `created_at` — no Note is ever the parent of
    another (docs/adr/0001-flat-notes-rather-than-a-tree.md).
    """

    id: uuid.UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid7))
    notebook_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True), ForeignKey("notebook.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    owner_id: str = Field(
        index=True,
        description="Denormalized from the owning Notebook so ownership can be checked "
        "without a join, per the defense-in-depth id decision.",
    )

    title: str
    summary: str = Field(description="Markdown summary of the session. Never empty.")

    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String), nullable=False, server_default="{}"),
        description="Free-text topical labels, model-supplied at save time.",
    )
    source_app: str = Field(
        description="Which OAuth-authenticated client saved this Note. Derived server-side "
        "from the token's client_id at save time, never model-supplied — see CONTEXT.md's "
        "Source App vs Tag distinction. Plain string, not a DB enum: the set of MCP clients "
        "is expected to grow and isn't fully known yet."
    )
    chat_link: str | None = Field(
        default=None, description="Optional URL to the original conversation. User-supplied only."
    )

    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), server_default=sa_func.now(), nullable=False)
    )

    notebook: Notebook = Relationship(back_populates="notes")
