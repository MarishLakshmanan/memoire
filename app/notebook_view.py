"""Renders what `retrieve` returns for a Notebook.

Implements the Q3/Q14 decisions from the plan.md grilling session: retrieve must never return
an empty string, and a stale Roll-up Summary must never silently omit newer Notes.
"""

from db.models import Note, Notebook


def render_notebook_view(notebook: Notebook, notes: list[Note]) -> str:
    """Build the text `retrieve` returns for a Notebook.

    Args:
        notebook (Notebook): The Notebook being rendered.
        notes (list[Note]): The Notebook's Notes, ordered oldest first.

    Returns:
        str: The Roll-up Summary if one exists and covers every Note, with newer Notes
            appended as a Derived Summary delta if it doesn't (Q14); otherwise a full
            Derived Summary assembled from all Notes (Q3). Never empty.
    """
    if not notes:
        return f"Notebook: {notebook.title} — no notes yet."

    if notebook.summary is None:
        header = f"Notebook: {notebook.title} — {len(notes)} note(s), no roll-up summary yet."
        return f"{header}\n\n{_format_note_index(notes)}"

    newer = [
        note
        for note in notes
        if notebook.summary_generated_at is None or note.created_at > notebook.summary_generated_at
    ]
    if not newer:
        return notebook.summary

    addendum = f"{len(newer)} note(s) added since this summary was written:\n\n{_format_note_index(newer)}"
    return f"{notebook.summary}\n\n---\n\n{addendum}"


def _format_note_index(notes: list[Note]) -> str:
    """Format a numbered list of Notes with ids, titles and snippets, for drill-down.

    Args:
        notes (list[Note]): The Notes to list, in the order they should appear.

    Returns:
        str: One numbered entry per Note.
    """
    lines = [f"{i}. [{note.id}] {note.title}\n   {snippet(note.summary)}" for i, note in enumerate(notes, start=1)]
    return "\n".join(lines)


def snippet(text: str, max_len: int = 160) -> str:
    """Take the first line of a summary, truncated, for a compact listing.

    Args:
        text (str): The full text to summarize.
        max_len (int, optional): Maximum snippet length. Defaults to 160.

    Returns:
        str: The truncated first line, or an empty string if `text` is blank.
    """
    stripped = text.strip()
    if not stripped:
        return ""
    first_line = stripped.splitlines()[0]
    if len(first_line) <= max_len:
        return first_line
    return first_line[: max_len - 1].rstrip() + "…"
