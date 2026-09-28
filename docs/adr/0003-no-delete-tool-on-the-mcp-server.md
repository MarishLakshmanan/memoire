# No delete tool on the MCP server

The MCP tool surface is read-and-append-only. Deletion happens exclusively in the web UI, behind a human click.

Recursive deletion driven by an LLM carries a large blast radius: one misread id destroys a Notebook, and there is no undo an agent can offer. The conventional mitigation is a `destructiveHint` tool annotation, but the MCP specification requires clients to treat annotations as untrusted, and Claude Code's permission engine reportedly treats all MCP tool calls uniformly rather than acting on the hint — worse, answering "don't ask again" writes a blanket allow rule covering every future argument. Removing the capability is the only guard that does not depend on client behaviour.

## Consequences

- Until the web UI ships, there is no supported way to delete anything. Use direct database access during development, and do not let that grow into a feature.
- Do not add a delete tool later to restore convenience. If deletion over MCP is ever genuinely needed, supersede this ADR deliberately rather than quietly.
