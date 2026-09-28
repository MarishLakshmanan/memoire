# Postgres rather than Neo4j

Notes form a flat list inside a Notebook (ADR-0001), so the deepest query in the system is `WHERE notebook_id = ?`. Neo4j earns its cost on variable-depth traversal and pathfinding across densely connected data, none of which exists here.

Postgres also supplies three things this project needs directly: full-text search over Note titles and summaries in the same database as the data, a `pgvector` upgrade path if semantic search is wanted later, and ordinary relational ownership columns for Clerk-backed multi-tenancy.

## Considered options

Neo4j was the original plan, chosen while the data model was described as a graph. That description did not survive scrutiny: single-parent edges make a tree rather than a graph, and ADR-0001 then flattened the tree into a list. The graph database was solving for a shape the project never had.
