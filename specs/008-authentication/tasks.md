# Tasks: Authentication & Multi-user Support

**Input**: Design documents from `/specs/008-authentication/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth.md

**TDD Note**: Constitution §III mandates Red-Green-Refactor. Test tasks marked with ⚠️ MUST be written first and confirmed failing before the paired implementation tasks begin.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no conflicts)
- **[Story]**: User story this task belongs to (US1–US4)
- Exact file paths included in every task

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies and configure environment variables before any implementation begins.

- [X] T001 Add `python-jose[cryptography]` and `svix` to `[project.dependencies]` in `backend/pyproject.toml` and run `uv sync`
- [X] T002 [P] Add `@clerk/clerk-react` v5+ to `frontend/package.json` and run `npm install`
- [X] T003 [P] Add `CLERK_JWKS_URL`, `CLERK_ISSUER`, and `CLERK_WEBHOOK_SECRET` settings to `backend/src/persona/config.py` (read from env vars, all required, raise on missing)
- [X] T004 [P] Create `frontend/.env.local.example` documenting `VITE_CLERK_PUBLISHABLE_KEY=pk_test_...` alongside existing example env files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema migration, core auth module, and DB upsert/delete helpers. MUST be complete before any user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Implement `migrate_v3_to_v4` in `backend/src/persona/migrations.py`: create `users` table, recreate `resume_version`/`application`/`accomplishment` with `user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE`, copy existing rows with `user_id='legacy'`, drop old tables, rename, recreate all indexes (see data-model.md §Migration: v3→v4)
- [X] T006 [P] Add `upsert_user(conn, user_id, email, display_name)` and `delete_user(conn, user_id)` to `backend/src/persona/database.py`; `upsert_user` uses `INSERT OR REPLACE` (or `INSERT ... ON CONFLICT DO UPDATE`)
- [X] T007 Implement `backend/src/persona/auth.py`: JWKS in-memory cache (1-hour TTL, on-demand refresh when `kid` not found), `verify_clerk_jwt(token) -> dict` using `python-jose`, and `get_current_user(token: HTTPAuthorizationCredentials, conn: DBConnection) -> UserContext` FastAPI dependency that validates token, upserts user row, and returns `UserContext(id, email, display_name)`

**Checkpoint**: `uv run pytest backend/tests/` passes on a clean DB; migration upgrades from v3 to v4 correctly.

---

## Phase 3: User Story 1 — Secure Sign-up and Sign-in (Priority: P1) 🎯 MVP

**Goal**: Users can create an account and sign in via Clerk; unauthenticated requests to any protected route are rejected (backend) or redirected (frontend).

**Independent Test**: Create a new account → sign out → sign back in → reach dashboard. Unauthenticated curl to `GET /api/resumes` returns `401`.

### Tests for US1 ⚠️ Write FIRST — confirm FAILING before T012

- [X] T008 [P] [US1] Write unit tests for JWKS caching logic (cache hit, cache miss, expired TTL, unknown `kid` refresh) and `verify_clerk_jwt` (valid token, expired token, wrong issuer, missing sub) in `backend/tests/unit/test_auth.py`
- [X] T009 [P] [US1] Write contract test: `GET /api/resumes` without `Authorization` header returns `401`; with a valid mock JWT returns `200` in `backend/tests/contract/test_auth_contract.py`

### Implementation for US1

- [X] T010 [US1] Wrap the React app with `<ClerkProvider publishableKey={import.meta.env.VITE_CLERK_PUBLISHABLE_KEY}>` in `frontend/src/main.tsx`
- [X] T011 [US1] Replace current routing in `frontend/src/App.tsx` with Clerk's `<SignedIn>` / `<SignedOut>` / `<RedirectToSignIn>` so unauthenticated users are redirected to the Clerk sign-in page
- [X] T012 [P] [US1] Create `frontend/src/components/AuthGuard/index.tsx`: a reusable wrapper that renders children only when signed in, otherwise renders `<RedirectToSignIn />`
- [X] T013 [US1] Update `frontend/src/services/api.ts` to call `clerk.session?.getToken()` and attach `Authorization: Bearer <token>` header to every API request; handle null token (user signed out) by redirecting
- [X] T014 [US1] Thread `get_current_user` dependency into `create_router` in `backend/src/persona/api/routes.py`: add `current_user: UserContext = Depends(get_current_user)` to every route handler except `GET /health` and `POST /api/webhooks/clerk`

**Checkpoint**: US1 fully functional. A signed-in user reaches the dashboard; `curl GET /api/resumes` without a token returns `401`; `make check` passes.

---

## Phase 4: User Story 2 — Personal Data Isolation (Priority: P1)

**Goal**: Every data read and write is scoped to the authenticated user; cross-user access is denied with `403`; account deletion cascades atomically.

**Independent Test**: Create User A and User B with separate accounts. User A creates a resume. User B's `GET /api/resumes` returns an empty list. User B's `GET /api/resumes/{user_a_resume_id}` returns `403`.

### Tests for US2 ⚠️ Write FIRST — confirm FAILING before T019 (REST) and T024/T025 (MCP tools)

- [X] T015 [P] [US2] Write integration test: two distinct users each create a resume; verify each sees only their own in list responses and receives `403` on cross-user detail access in `backend/tests/integration/test_multi_user.py`
- [X] T016 [P] [US2] Extend `backend/tests/contract/test_auth_contract.py`: `GET /api/resumes/{id}` with a valid JWT for a different user returns `403`; `PUT /api/resumes/{id}` and `DELETE /api/resumes/{id}` also return `403` on wrong owner
- [X] T035 [P] [US2] Write contract tests for MCP read tools in `backend/tests/contract/test_auth_contract.py`: for each read tool (e.g., `read_resume`, `read_applications`) verify (a) a valid `ContextVar` user context returns only that user's data and (b) a missing/empty `ContextVar` returns a structured MCP error with code `401`
- [X] T036 [P] [US2] Write contract tests for MCP write tools in `backend/tests/contract/test_auth_contract.py`: for each write tool (e.g., `write_resume`, `create_application`) verify (a) a valid `ContextVar` user context writes to the correct `user_id` and (b) a missing/empty `ContextVar` returns a structured MCP error with code `401`

### Implementation for US2

- [X] T017 [US2] Update all resume-version DB functions in `backend/src/persona/database.py` to accept `user_id: str` and filter every query (`SELECT`, `UPDATE`, `DELETE`) with `WHERE user_id = ?`; raise `PermissionError` if a fetched row's `user_id` doesn't match
- [X] T018 [P] [US2] Update all application DB functions in `backend/src/persona/database.py` to accept `user_id: str` and apply the same ownership filter and check as T017
- [X] T019 [P] [US2] Update all accomplishment DB functions in `backend/src/persona/database.py` to accept `user_id: str` and apply the same ownership filter and check as T017
- [X] T020 [US2] Update `backend/src/persona/resume_service.py`: add `user_id: str` parameter to `__init__` or each method, pass it through to all `database.*` calls updated in T017
- [X] T021 [P] [US2] Update `backend/src/persona/application_service.py`: same as T020 for all application and contact/communication DB calls updated in T018
- [X] T022 [P] [US2] Update `backend/src/persona/accomplishment_service.py`: same as T020 for all accomplishment DB calls updated in T019
- [X] T023 [US2] In `backend/src/persona/api/routes.py`: pass `current_user.id` from the injected `UserContext` into every service call (resume, application, accomplishment); translate `PermissionError` → `HTTP 403`
- [X] T024 [P] [US2] Update `backend/src/persona/tools/read.py`: store `current_user.id` in a `ContextVar[str]` set by auth middleware; pass it to every DB/service call within each MCP tool handler
- [X] T025 [P] [US2] Update `backend/src/persona/tools/write.py`: same `ContextVar` pattern as T024 for all write tool handlers
- [X] T026 [US2] Implement `POST /api/webhooks/clerk` in `backend/src/persona/api/routes.py`: verify Svix signature headers using `svix` library and `CLERK_WEBHOOK_SECRET`; on `user.deleted` event, call `delete_user(conn, user_id)` which cascades to all owned data; return `400` on invalid signature

**Checkpoint**: US2 fully functional. Two-user isolation confirmed by integration test. Account deletion webhook purges all user data. `make check` passes.

---

## Phase 5: User Story 3 — Social Login Integration (Priority: P2)

**Goal**: Users can sign in with Google or GitHub without creating a separate password.

**Independent Test**: Select "Continue with Google" on the Clerk sign-in page → complete OAuth flow → land on the Persona dashboard.

- [X] T027 [US3] Configure Google and GitHub OAuth social connections in the Clerk dashboard per `specs/008-authentication/quickstart.md` §1; document the exact toggle paths in quickstart.md §1 as a checklist
- [X] T028 [P] [US3] Verify that the `<SignIn />` component rendered via Clerk (added in T011) automatically shows Google and GitHub buttons when social connections are enabled — no code change required; add a manual verification step to `specs/008-authentication/quickstart.md` §4.1

**Checkpoint**: US3 functional. Social login buttons visible; OAuth round-trip completes and lands on dashboard.

---

## Phase 6: User Story 4 — User Profile and Session Management (Priority: P2)

**Goal**: Authenticated users can view their account details and sign out; post-signout, protected routes redirect to sign-in.

**Independent Test**: Click the user avatar → see profile name and email. Click "Sign Out" → redirected to landing page → `GET /api/resumes` returns `401`.

- [X] T029 [P] [US4] Create `frontend/src/components/UserMenu/index.tsx` using Clerk's `<UserButton>` component (provides avatar, profile popup, and sign-out); configure `afterSignOutUrl="/"` to redirect to the landing page
- [X] T030 [US4] Add `<UserMenu />` to the app header/navigation bar in `frontend/src/App.tsx` (or the top-level layout component); ensure it is only rendered inside `<SignedIn>`
- [X] T031 [P] [US4] Add a Vitest component test for `UserMenu` in `frontend/src/__tests__/UserMenu.test.tsx`: verify the component renders when signed in and is absent when signed out (mock `@clerk/clerk-react`)

**Checkpoint**: US4 functional. User avatar visible in header; profile popup shows name/email; sign-out redirects correctly.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final validation, and CI gate.

- [X] T032 [P] Update `README.md`: add a "Authentication Setup" section documenting Clerk prerequisites, required environment variables (`VITE_CLERK_PUBLISHABLE_KEY`, `CLERK_JWKS_URL`, `CLERK_ISSUER`, `CLERK_WEBHOOK_SECRET`), and a link to `specs/008-authentication/quickstart.md`
- [ ] T033 [P] Walk through all four manual test scenarios in `specs/008-authentication/quickstart.md` §4 (web login, API authorization, multi-user isolation, webhook testing) and confirm each passes against a locally running stack (`make run-local`)
- [X] T034 Run `make check` from repository root; confirm lint + typecheck + test pass for both frontend and backend with zero failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — **BLOCKS all user stories**
- **US1 (Phase 3)**: Depends on Phase 2 — BLOCKS US2 (auth middleware must exist before scoping)
- **US2 (Phase 4)**: Depends on Phase 3 (routes must have `current_user` before scoping queries)
- **US3 (Phase 5)**: Depends on Phase 3 (ClerkProvider must be present for social login to render)
- **US4 (Phase 6)**: Depends on Phase 3 (ClerkProvider and `<SignedIn>` routing must be set up)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### Within Each Phase

- Tests (T008, T009, T015, T016, T035, T036) MUST be written and confirmed **FAILING** before paired implementation tasks
- DB layer (T017–T019) before service layer (T020–T022) before route layer (T023)
- `auth.py` (T007) before `routes.py` changes (T014)

### Parallel Opportunities Within Phases

| Phase | Parallel group |
|-------|---------------|
| 1 | T001 ∥ T002 ∥ T003 ∥ T004 |
| 2 | T006 ∥ T007 (after T005 completes) |
| 3 | T008 ∥ T009 (tests); T012 ∥ T013 (after T010); |
| 4 | T015 ∥ T016 ∥ T035 ∥ T036 (tests); T018 ∥ T019 (after T017); T021 ∥ T022 (after T020); T024 ∥ T025 (after T023 + T035 + T036) |
| 5 | T027 ∥ T028 |
| 6 | T029 ∥ T031; then T030 |
| 7 | T032 ∥ T033; then T034 |

---

## Parallel Example: User Story 2 (Data Isolation)

```text
# TDD phase — launch in parallel:
Task: "Write integration test for two-user isolation" → backend/tests/integration/test_multi_user.py
Task: "Extend contract tests for 403 cross-user access" → backend/tests/contract/test_auth_contract.py
Task: "Write contract tests for MCP read tool user-scoping (T035)" → backend/tests/contract/test_auth_contract.py
Task: "Write contract tests for MCP write tool user-scoping (T036)" → backend/tests/contract/test_auth_contract.py

# DB layer — launch in parallel after tests are written:
Task: "Update resume_version DB functions with user_id" → backend/src/persona/database.py
Task: "Update application DB functions with user_id"   → backend/src/persona/database.py
Task: "Update accomplishment DB functions with user_id" → backend/src/persona/database.py

# Service layer — launch in parallel after DB layer:
Task: "Update ResumeService with user_id"        → backend/src/persona/resume_service.py
Task: "Update ApplicationService with user_id"   → backend/src/persona/application_service.py
Task: "Update AccomplishmentService with user_id" → backend/src/persona/accomplishment_service.py

# Tool layer — launch in parallel after service layer:
Task: "Update MCP read tools with ContextVar user_id"  → backend/src/persona/tools/read.py
Task: "Update MCP write tools with ContextVar user_id" → backend/src/persona/tools/write.py
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 — both P1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (migration + auth.py)
3. Complete Phase 3: US1 — single-user auth working end-to-end
4. Complete Phase 4: US2 — data isolation and webhooks
5. **STOP and VALIDATE**: Run multi-user isolation test manually + `make check`
6. Deploy/demo — the core security requirement is met

### Incremental Delivery

1. Setup + Foundational → auth infrastructure ready
2. + US1 → Single user can sign in and use the app (functional MVP)
3. + US2 → Multi-user safe; account deletion works
4. + US3 → Social login (low code effort, high UX value)
5. + US4 → Profile and sign-out polish

### Notes

- `[P]` tasks touch different files — safe to parallelize
- Constitution §III: test tasks must run red before implementation tasks run green
- Commit after each logical group (e.g., after DB layer, after service layer)
- Stop at each **Checkpoint** to validate the story independently before continuing
