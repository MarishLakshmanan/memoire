# Flat Notes rather than a tree

Notes sit as an ordered, flat list inside a Notebook. A Note is never the parent of another Note.

The original design nested Notes arbitrarily: `save` took a `reference_id` pointing at a parent Note, and any Note became a parent the moment a later save named it. The problem is where that id comes from — the saving agent knows only the id of whatever it most recently retrieved, so it passes that. The resulting hierarchy would record *retrieval order*, not any real relationship, and three sibling work-sessions on one project would accrete into an accidental three-deep chain that changes shape depending on what the agent happened to read first.

## Consequences

- The save parameter is named `notebook_id`, not `reference_id`, so its meaning — "which Notebook this Note joins" — cannot be misread as "my parent".
- Genuine sub-branching is not expressible. A Note can reference another Note in its body text as a soft link.
- Reversible: adding a nullable `parent_note_id` later is a migration, not a rewrite.
