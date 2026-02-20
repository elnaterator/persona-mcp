# Implementation Plan: Authentication & Multi-user Support

**Branch**: `008-authentication` | **Date**: 2026-02-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-authentication/spec.md`

## Summary

Introduce Clerk-based authentication and multi-user data isolation to the Persona MCP server. The React frontend uses `@clerk/clerk-react` (v5+) for UI and session management. The backend validates Clerk JWTs on every request via JWKS (python-jose) and uses `svix` exclusively for user lifecycle webhooks. A new `users` table (keyed by Clerk `sub`) is added to SQLite as the foreign-key anchor for all owned tables; the schema advances from v3 → v4 via the existing migration framework.

## Technical Context

**Language/Version**: Python 3.11+ (backend); TypeScript 5.x / React 18 (frontend)
**Primary Dependencies**: FastAPI ≥0.100.0, FastMCP ≥2.3.0, `@clerk/clerk-react` v5+, `python-jose[cryptography]`, `svix`
**Storage**: SQLite (schema v3 → v4); `users` table added as FK anchor for `resume_version`, `application`, `accomplishment`
**Testing**: pytest — unit, contract, integration (backend); Vitest + React Testing Library (frontend)
**Target Platform**: Linux server (Docker) + local macOS/Linux development
**Project Type**: Web application (React SPA + FastAPI/MCP backend)
**Performance Goals**: JWT validation ≤5ms per request (JWKS cached in-memory, 1-hour TTL with on-demand refresh on unknown `kid`)
**Constraints**: Clerk availability is a hard dependency (no offline fallback, per A-002); JWKS must be reachable from backend at runtime (A-004)
**Scale/Scope**: ≥1,000 concurrent authenticated sessions (SC-004); 99.9% auth-service availability via Clerk (SC-005)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol Compliance | PASS | JWT auth added at the FastAPI/FastMCP middleware layer; MCP tool signatures remain unchanged |
| II. Single-Package Distribution via uvx | PASS | `python-jose[cryptography]` and `svix` declared in `pyproject.toml`; no vendoring |
| III. Test-Driven Development (TDD) | PASS | Auth middleware contract tests written before implementation; multi-user isolation integration tests required |
| IV. Minimal Dependencies | PASS | `python-jose[cryptography]` — lightweight JWT validation (no heavy SDK); `svix` — Clerk-recommended for webhook verification |
| V. Explicit Error Handling | PASS | 401 (missing/invalid token) and 403 (valid token, wrong owner) defined in contracts/auth.md; MCP tools translate these to structured MCP error responses |
| README updates | PASS | Task to update README with Clerk setup and new env vars included in tasks.md |

No violations detected. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/008-authentication/
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (/speckit.plan)
├── data-model.md        # Phase 1 output (/speckit.plan)
├── quickstart.md        # Phase 1 output (/speckit.plan)
├── contracts/
│   └── auth.md          # Auth API contracts (/speckit.plan)
└── tasks.md             # Phase 2 output (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
backend/
├── src/persona/
│   ├── auth.py                      # NEW: JWKS cache + JWT validation + get_current_user dependency
│   ├── migrations.py                # UPDATED: migrate_v3_to_v4 (users table + user_id FKs on owned tables)
│   ├── database.py                  # UPDATED: all queries accept user_id param; upsert_user()
│   ├── models.py                    # UPDATED: UserContext; owned models updated where exposed via API
│   ├── config.py                    # UPDATED: CLERK_JWKS_URL, CLERK_ISSUER, CLERK_WEBHOOK_SECRET env vars
│   ├── api/
│   │   └── routes.py                # UPDATED: Depends(get_current_user) on all routes; POST /api/webhooks/clerk
│   └── tools/
│       ├── read.py                  # UPDATED: user_id passed to all DB read queries
│       └── write.py                 # UPDATED: user_id passed to all DB write queries
└── tests/
    ├── unit/
    │   └── test_auth.py             # NEW: JWKS cache, JWT decode, claim validation unit tests
    ├── contract/
    │   └── test_auth_contract.py    # NEW: 401/403 contract tests for all existing + new endpoints
    └── integration/
        └── test_multi_user.py       # NEW: two-user data isolation integration tests

frontend/
└── src/
    ├── main.tsx                     # UPDATED: wrap app with <ClerkProvider publishableKey={...}>
    ├── App.tsx                      # UPDATED: <SignedIn>/<SignedOut> routing + <RedirectToSignIn>
    ├── components/
    │   └── AuthGuard/               # NEW: reusable route-protection wrapper component
    └── services/
        └── api.ts                   # UPDATED: attach Authorization: Bearer header via getToken()
```

**Structure Decision**: Web application layout (frontend + backend). Auth spans both layers; no new top-level directories added.
