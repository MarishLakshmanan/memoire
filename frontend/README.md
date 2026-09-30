# ai-notes frontend

React + Vite + TypeScript + Tailwind v4 + Clerk. Lists Notebooks, shows a Notebook's Notes, and
handles deletion — the only place anything gets deleted (see [ADR-0003](../docs/adr/0003-no-delete-tool-on-the-mcp-server.md)).

See the [repo root README](../README.md) for what this project is and how to run the whole stack.

## Dev setup

```
cp .env.example .env   # fill in your Clerk publishable key
npm install
npm run dev             # http://localhost:5173
```
