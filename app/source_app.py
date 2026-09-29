"""Maps an authenticated OAuth client to the Source App label stored on a Note.

CONTEXT.md defines Source App as "a closed set" established server-side, never model-supplied.
In practice the set is curated here and grows as new MCP clients are confirmed working — see
docs/adr and the CIMD research from the auth spike for why a client's CIMD document URL is a
trustworthy, unspoofable identifier.
"""

import logging

logger = logging.getLogger(__name__)

# Verified client_id values, one per confirmed-working MCP client. Extend this as new clients
# are tested end-to-end, the same way the phase 0 spike verified Claude Code.
_KNOWN_CLIENTS: dict[str, str] = {
    "https://claude.ai/oauth/claude-code-client-metadata": "claude-code",
}


def resolve_source_app(client_id: str) -> str:
    """Turn an OAuth client_id into a Source App label.

    Args:
        client_id (str): The `client_id` from the caller's verified access token.

    Returns:
        str: The known label for this client, or the raw `client_id` itself if the client
            hasn't been added to `_KNOWN_CLIENTS` yet — still accurate and traceable, just
            not the friendly form. A save should never fail just because a new client showed up.
    """
    label = _KNOWN_CLIENTS.get(client_id)
    if label is None:
        logger.warning(
            "Unrecognized MCP client_id %r — add it to _KNOWN_CLIENTS once confirmed working.",
            client_id,
        )
        return client_id
    return label
