# Implementation Plan: MCP Server Connection Instructions & API Key Management

**Branch**: `011-mcp-instructions` | **Date**: 2026-02-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-mcp-instructions/spec.md`

## Summary

Add a "Connect" tab to the Persona web UI that gives users step-by-step instructions for connecting any of four supported AI coding assistants (Claude Code, Cursor, GitHub Copilot, Amazon Kiro) to the Persona MCP server. API key management is handled by Clerk's native API key feature via the prebuilt `<APIKeys />` React component. Users paste their key into a local input field to auto-populate config commands. On the backend, `UserContextMiddleware` is extended to accept Clerk native API keys (opaque `ak_` tokens) in addition to the existing Clerk session JWT support, enabling machine-auth access to MCP tools without a browser session.

## Technical Context

**Language/Version**: Python 3.11+ (backend); TypeScript 5.x / React 18 (frontend)
**Primary Dependencies**: FastAPI ≥0.100.0, FastMCP ≥2.3.0, `clerk-backend-api ≥1.0.0` (new — Python SDK for dual auth), `@clerk/clerk-react` v5+ (existing), `python-jose[cryptography]` (existing — retained for REST API JWT path)
**Storage**: PostgreSQL 16+ (no schema changes required)
**Testing**: pytest (backend unit + contract + integration), Vitest 2 + React Testing Library (frontend)
**Target Platform**: Linux server (Docker/AWS); browser (React SPA)
**Project Type**: Web application (existing frontend + backend monorepo)
**Performance Goals**: `/mcp` API key auth < 500ms P95 (network call to Clerk); Connect section UI loads < 2s
**Constraints**: Plaintext API key NEVER stored or logged; `CLERK_SECRET_KEY` required at runtime; one active key per user; no new DB tables or schema migrations
**Scale/Scope**: All authenticated users; stateless key verification via Clerk; 4 assistants at launch

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. MCP Protocol Compliance | ✅ PASS | `/mcp` endpoint remains MCP-compliant; auth check is in middleware before MCP handling, not inside MCP protocol |
| II. Single-Package Distribution | ✅ PASS | `clerk-backend-api` added as a standard `pyproject.toml` dependency; `uvx` install path unchanged |
| III. TDD | ✅ PASS | New auth paths (API key verification in `UserContextMiddleware`) require contract tests written before implementation; frontend Connect component requires Vitest tests |
| IV. Minimal Dependencies | ✅ PASS | `clerk-backend-api` justified: opaque `ak_` tokens cannot be verified without a network call to Clerk; no stdlib alternative; same vendor as existing auth layer. See `research.md` Decision 8. |
| V. Explicit Error Handling | ✅ PASS | Auth failures return 401 HTTPException (existing pattern); Clerk SDK always returns `RequestState` (never throws); error logged server-side, only message surfaced to client |

**Post-design re-check**: All gates remain passing. No schema changes, no new REST endpoints, no new projects. Architecture stays within existing frontend/backend split.

## Project Structure

### Documentation (this feature)

```text
specs/011-mcp-instructions/
├── plan.md              # This file
├── research.md          # Phase 0: decisions on Clerk SDK, config formats, component limitations
├── data-model.md        # Phase 1: API Key entity, auth context, no DB changes
├── quickstart.md        # Phase 1: local dev setup guide
├── contracts/
│   └── mcp-dual-auth.md # Phase 1: /mcp endpoint dual auth contract + test scenarios
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml                          # Add clerk-backend-api>=1.0.0
└── src/persona/
│   ├── auth.py                             # Add verify_clerk_api_key() / extend middleware helper
│   ├── config.py                           # Add resolve_clerk_secret_key()
│   └── server.py                           # Update UserContextMiddleware for dual auth
└── tests/
    ├── unit/
    │   └── test_auth.py                    # Add API key verification unit tests
    └── contract/
        └── test_auth_contract.py           # Add T-MCP-01 through T-MCP-05 dual auth scenarios

frontend/
├── .env.local                              # Add VITE_MCP_SERVER_URL=
└── src/
    ├── App.tsx                             # Add 'connect' to View union + NavSection type
    ├── components/
    │   ├── Navigation.tsx                  # Add 4th "Connect" tab button
    │   ├── Navigation.module.css           # No changes expected
    │   └── ConnectView/
    │       ├── index.tsx                   # New: Connect tab content component (includes save-key warning banner)
    │       └── ConnectView.module.css      # New: styles for Connect tab (includes warning banner styles)
    └── __tests__/
        └── ConnectView.test.tsx            # New: Vitest tests for Connect component
```

**Structure Decision**: Web application (Option 2 from template). Frontend and backend are separate subdirectories with independent build tools. Only files listed above are modified or created; no new projects, packages, or directories beyond `ConnectView/`.

## Complexity Tracking

> No constitution violations. No complexity tracking required.
