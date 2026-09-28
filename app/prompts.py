"""The four prompts: save_session, summarize_notebook, recall, how_to.

Each returns plain instructional text for the connected model to act on — they don't touch
the database themselves, only tell the model which tools to call and how to use them well.
"""

from mcp.server.mcpserver import MCPServer


def register_prompts(server: MCPServer) -> None:
    """Register the four prompts on an MCPServer.

    Args:
        server (MCPServer): The server to register prompts on.
    """

    @server.prompt()
    def save_session(notebook_id: str | None = None) -> str:
        """Summarize this conversation and save it as a Note.

        Args:
            notebook_id (str, optional): An existing Notebook to append to. Defaults to
                None, which starts a new Notebook.

        Returns:
            str: Instructions for the model.
        """
        target_line = (
            f'- Save it to the existing Notebook "{notebook_id}" (pass this as `notebook_id`).'
            if notebook_id
            else "- Don't ask which Notebook to use unless the user has clearly said this "
            "continues an earlier one — otherwise let a new Notebook be created automatically."
        )
        return f"""Summarize the current conversation and save it to the user's ai-notes app.

Rules:
- Summarize ONLY this session. You may reference earlier sessions briefly (e.g. "continuing
  the auth research from before") but don't re-summarize or repeat their content.
- Write in markdown. Preserve real detail — decisions made, code changed, open questions,
  outcomes. Don't over-compress into a vague one-liner.
- Give it a short, specific title you'd still recognize months from now — not "Chat session"
  or "Notes".
- Add a few free-text tags if an obvious topic stands out (e.g. "auth", "database").
- Only pass a `chat_link` if the user has given you an actual URL for this conversation.
  Never invent one.
{target_line}

Once you've written the summary, call the save_note tool with it."""

    @server.prompt()
    def summarize_notebook(notebook_id: str) -> str:
        """Write and save a Roll-up Summary across every Note in a Notebook.

        Args:
            notebook_id (str): The Notebook to summarize.

        Returns:
            str: Instructions for the model.
        """
        return f"""Write a roll-up summary for Notebook "{notebook_id}" and save it.

Steps:
1. Call get_notebook_contents with notebook_id="{notebook_id}" to fetch every Note in this
   Notebook, in full.
2. Read all of them and write ONE cohesive summary in markdown — don't just concatenate the
   individual Note summaries. Synthesize the throughline: what this Notebook is actually
   about, the key decisions and turns across sessions, and where things currently stand.
   If the sessions genuinely cover different topics, say so rather than forcing a narrative
   that isn't there.
3. Call save_notebook_summary with notebook_id="{notebook_id}" and your summary."""

    @server.prompt()
    def recall(query: str | None = None) -> str:
        """Bring in context the user saved from a previous AI session.

        Args:
            query (str, optional): What the user is looking for. Defaults to None.

        Returns:
            str: Instructions for the model.
        """
        looking_for = f'They are looking for: "{query}".\n\n' if query else ""
        return f"""The user wants to bring in context they saved from a previous AI session,
via their ai-notes app — an external memory store that carries context between different
AI assistants.

{looking_for}Steps:
1. Find the right Notebook: call search_notes with relevant keywords, or list_notebooks to
   browse the most recent ones.
2. Call retrieve with that Notebook's id. This returns either a synthesized roll-up summary
   of the whole Notebook, or — if no roll-up exists yet — a list of its individual sessions
   (Notes), each with its own id and a short snippet.
3. If you need more detail on one specific session, call retrieve again with that Note's id
   to get its full content.
4. Tell the user this context came from their ai-notes app, and mention if there's more depth
   available (other Notes in the Notebook) that you haven't pulled in."""

    @server.prompt()
    def how_to() -> str:
        """Explain what ai-notes is and how to use it.

        Returns:
            str: A short overview of the tools and prompts.
        """
        return """# ai-notes

ai-notes lets you carry context between different AI assistants. Summarize a session here,
then reference it later from a different AI app that can't otherwise see that conversation.

## Structure

- A **Notebook** holds all the sessions for one project or topic.
- A **Note** is the summary of one session inside a Notebook.

## Tools

- `save_note` — save a summary of the current session as a Note.
- `retrieve` — get a Notebook's summary, or a Note's full content, by id.
- `list_notebooks` — list your most recent Notebooks.
- `search_notes` — full-text search your Notes.
- `get_notebook_contents` / `save_notebook_summary` — used by summarize_notebook, below.

## Prompts

- `save_session` — summarize this conversation and save it.
- `summarize_notebook` — write a roll-up summary across an entire Notebook.
- `recall` — bring in context from a previous session.
- `how_to` — this."""
