# Architecture Notes

Design decisions and tradeoff analysis for Persona. Records *why* the architecture looks the way it does, not just *what* it is.

---

## API style: REST vs GraphQL

**Decision: stay with REST.**

### Context

The backend exposes standard CRUD REST across six resources — resumes (with nested sections/entries), applications, accomplishments, notes, contacts, and communications — plus per-resource `tags` endpoints and cross-resource search. Routes live in `backend/src/persona/api/routes.py` (~1000 lines), guarded by Clerk auth middleware.

There are two consumers:

1. The **React SPA** (`frontend/`), which calls REST endpoints via the fetch client in `src/services/api/`.
2. The **MCP tool layer** (`backend/src/persona/tools/`), which an LLM drives directly against the shared service layer.

### GraphQL — pros for this app

- Single endpoint; the client selects exactly the fields it needs. No over- or under-fetching.
- Cross-resource fetches in one round-trip — fits the search/aggregation use case.
- Typed schema is self-documenting and supports frontend type codegen.

### GraphQL — cons for this app

- Requires a new dependency (strawberry/ariadne) plus a rewrite of the working REST layer. Real cost, no user-facing gain.
- N+1 query risk; would need dataloader batching, which the current PostgreSQL layer is not built for.
- Loses HTTP caching. REST `GET`s are cacheable by browser/CDN; GraphQL-over-`POST` is not.
- Per-field auth and rate limiting are harder than per-route. Clerk middleware is already wired to routes.
- The MCP layer **already serves as the flexible-query interface**. The LLM hits `tools/read.py` rather than fixed endpoints, so GraphQL would duplicate that role.

### Implications if we switched

- New schema + resolvers + dataloaders — on the order of weeks.
- Frontend rewrite: fetch calls become a GraphQL client (urql/Apollo), or stay on fetch with raw queries.
- MCP tools either keep calling the service layer directly or proxy through GraphQL — an extra hop with no benefit.
- Error model changes from HTTP status codes to `200` + an `errors` array, forcing rework of toast/error handling.

### Rationale

GraphQL solves problems Persona does not have: many heterogeneous clients, deeply nested object graphs, and over-fetching at scale. Persona has one SPA plus one MCP layer, six flat resources with fixed shapes, and a working API with HTTP caching.

The query-shape flexibility GraphQL sells is already delivered to the LLM by the MCP tools. Adding GraphQL would create a second flexible layer on top of a rewrite cost.

**If specific pain appears** — e.g. the frontend making five round-trips to build one view — fix it surgically with a REST aggregate endpoint. That is far cheaper than a schema migration.
