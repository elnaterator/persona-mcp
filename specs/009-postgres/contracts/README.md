# Contracts: PostgreSQL Migration (009-postgres)

**Date**: 2026-02-20

## No API Contract Changes

This feature is **purely infrastructure**. The PostgreSQL migration introduces no changes to:

- REST API endpoints (paths, methods, request/response schemas)
- MCP tool names, input schemas, or output schemas
- Authentication/authorization behavior
- Webhook handling

All existing API contracts defined by the REST routes in `backend/src/persona/api/routes.py` and the MCP tools in `backend/src/persona/tools/` remain identical.

## Environment Variable Changes

One new environment variable is introduced (behavioral change for operators):

| Variable | Old | New | Required |
|---------|-----|-----|---------|
| `PERSONA_DATA_DIR` | Required (SQLite file location) | Optional (no longer used for DB) | No |
| `PERSONA_DB_URL` | Not present | PostgreSQL connection URL | Yes (in HTTP mode) |
| `PERSONA_DB_POOL_MIN` | Not present | Min pool size (default: 1) | No |
| `PERSONA_DB_POOL_MAX` | Not present | Max pool size (default: 10) | No |

### `PERSONA_DB_URL` format

```
postgresql://[user]:[password]@[host]:[port]/[dbname]
```

**Default for docker-compose**: `postgresql://persona:persona@postgres:5432/persona`

**Local dev (outside Docker)**: `postgresql://persona:persona@localhost:5432/persona`

## Health Check

The existing `/health` endpoint is unchanged. It returns 200 OK when the server is running. No DB liveness check is added to `/health` in this feature (out of scope).
