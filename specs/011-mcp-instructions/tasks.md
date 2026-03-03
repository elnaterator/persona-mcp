# Tasks: MCP Server Connection Instructions & API Key Management

**Input**: Design documents from `/specs/011-mcp-instructions/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/mcp-dual-auth.md ✅, quickstart.md ✅

**Tests**: Included per plan.md TDD requirement (Constitution Principle III): contract tests before backend implementation; Vitest tests before frontend implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependency, configure required environment variables, and prepare the project for dual-auth implementation.

- [x] T001 Add `clerk-backend-api>=1.0.0` to `backend/pyproject.toml` and run `uv add clerk-backend-api` to update `backend/uv.lock`
- [x] T002 [P] Add `VITE_MCP_SERVER_URL=http://localhost:8000/mcp` to `frontend/.env.local` (create if missing; for production, document that this should be set to the deployed `/mcp` URL)
- [x] T003 [P] Add `CLERK_SECRET_KEY=` placeholder to `backend/.env.local` (create if missing) with a comment explaining it is required for dual auth at `/mcp`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend auth infrastructure that MUST be complete before US1 implementation can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Add `resolve_clerk_secret_key()` function to `backend/src/persona/config.py` — reads `CLERK_SECRET_KEY` env var and raises `RuntimeError` with a clear message if unset; used by `UserContextMiddleware`
- [x] T005 Add `build_clerk_client()` factory and `authenticate_mcp_request()` helper to `backend/src/persona/auth.py` — initialises `clerk_backend_api.Clerk(secret_key=...)` and wraps the incoming FastAPI `Request` as `httpx.Request` before calling `clerk_client.authenticate_request(httpx_req, AuthenticateRequestOptions(accepts_token=["session_token", "api_key"]))`

**Checkpoint**: Backend auth helpers are ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Generate API Key and Connect a New Assistant (Priority: P1) 🎯 MVP

**Goal**: New user can generate a Clerk API key, paste it into the Connect tab, and immediately see copy-ready config commands for all 4 AI coding assistants. Backend `/mcp` endpoint accepts both session JWTs and API keys.

**Independent Test**: Brand-new user with no API key can: (1) click "Connect" tab, (2) generate a key via `<APIKeys />`, (3) paste the key into the input field, (4) copy the Claude Code CLI command, (5) configure Claude Code, (6) verify connection via `claude mcp list`. Backend: `POST /mcp` with a valid `ak_...` token returns 200; with no token returns 401.

### Tests for User Story 1 ⚠️ Write FIRST — verify they FAIL before implementation

- [x] T006 [P] Write contract tests T-MCP-01 through T-MCP-05 in `backend/tests/contract/test_auth_contract.py` (valid JWT → 200, valid API key → 200, no header → 401, expired/invalid token → 401, malformed token → 401); verify all FAIL before T009
- [x] T007 [P] Write unit tests for `authenticate_mcp_request()` and `build_clerk_client()` in `backend/tests/unit/test_auth.py` (mock `Clerk.authenticate_request` return values for `is_signed_in=True/False`); verify they FAIL before T009
- [x] T008 [P] Write Vitest tests for ConnectView in `frontend/src/__tests__/ConnectView.test.tsx`: renders Connect tab content, renders `<APIKeys />` placeholder, renders paste-input field, renders placeholder `YOUR_API_KEY` in all 4 snippets when input is empty, substitutes real key when input is populated; **assert warning banner with text "Copy your API key now" is visible when `keyJustCreated` state is true and absent when false**; assert warning banner is dismissable (clicking close hides it); **include regression assertions that Resumes, Applications, and Accomplishments tab buttons in `Navigation.tsx` still render their respective views (FR-012)**; use label/role-based queries (`getByRole`, `getByLabelText`) rather than structure-specific selectors so tests survive the tab/accordion refactor in T018; verify they FAIL before T013

### Implementation for User Story 1

- [x] T009 Update `UserContextMiddleware` in `backend/src/persona/server.py` to use `authenticate_mcp_request()` (from T005) instead of the existing JWT-only verification function (**confirm exact function name in `server.py` before editing — referred to here as `verify_clerk_jwt()` but may differ**); extract `user_id` via `to_auth()` for both `session_token` and `api_key` token types; call `upsert_user(conn, clerk_id=user_id, email=email_or_none)` on both paths; retain 401 on `is_signed_in == False`
- [x] T010 [P] Add `'connect'` to the `View` union type and add a `ConnectSection` render branch to the main content area in `frontend/src/App.tsx`
- [x] T011 [P] Add a fourth "Connect" tab button to `frontend/src/components/Navigation.tsx` (matches existing tab button pattern; navigates to `'connect'` view)
- [x] T012 Create `frontend/src/components/ConnectView/ConnectView.module.css` with layout styles for the Connect tab: two-column or stacked layout for `<APIKeys />` section and config snippets section, paste-input field styling, code block styling for config snippets; **warning banner styles — visually prominent (amber/yellow background, bold text, warning icon) with sufficient contrast so the "copy your key now" message cannot be overlooked**
- [x] T013 Create `frontend/src/components/ConnectView/index.tsx`: **verify at implementation time** that `<APIKeys />` is exported from the installed `@clerk/clerk-react` v5 package; if available, render `<APIKeys />`; if unavailable, implement the fallback using `useClerk().apiKeys.create()` with custom one-time display logic satisfying FR-004 (show secret once unmasked) and FR-005 (mask on subsequent views) — add Vitest tests covering the fallback path; render a **Persona-owned warning banner** (controlled by `keyJustCreated` boolean state, default `false`) immediately above the `<APIKeys />` component — banner text: "Copy your API key now — this is the only time you will see it in full. If you lose it, you will need to generate a new one." — banner includes a dismiss button that sets `keyJustCreated` to `false`; set `keyJustCreated = true` after each successful key creation or regeneration event; render paste-input field with `apiKey` local state; render config snippet blocks for all 4 assistants (Claude Code CLI, Cursor `.cursor/mcp.json`, GitHub Copilot `.vscode/mcp.json`, Amazon Kiro `.kiro/settings/mcp.json`) substituting `apiKey` state or `VITE_MCP_SERVER_URL` env var (defaulting to `https://your-persona-server.com/mcp` when unset); **handle key creation error state** by displaying an inline error message when the Clerk key creation call fails (network error, Clerk API error)

**Checkpoint**: User Story 1 is fully functional — new user can generate a key, paste it, and see all config commands. Backend accepts API key tokens at `/mcp`.

---

## Phase 4: User Story 2 — Copy a Config Command with Existing API Key (Priority: P2)

**Goal**: Returning user with an existing API key can copy a working config command for any assistant directly from the Connect tab, even with the key currently masked in the `<APIKeys />` display.

**Independent Test**: A user with an existing API key: (1) views Connect tab (key is masked), (2) clicks the copy button next to any assistant, (3) pastes result — clipboard contains the full valid command with the real `ak_...` key embedded.

- [x] T014 Add per-assistant copy-to-clipboard handler in `frontend/src/components/ConnectView/index.tsx` using `navigator.clipboard.writeText(fullCommand)` where `fullCommand` is built from `apiKey` local state value (from paste-input, not from `<APIKeys />` display mask state) — applies to all 4 assistant snippets
- [x] T015 [P] Add copy button element to each config snippet block in `frontend/src/components/ConnectView/index.tsx` (one `<button>` per assistant) with appropriate accessible label (e.g., `aria-label="Copy Claude Code config"`); add copied-feedback state (e.g., button text briefly changes to "Copied!")

**Checkpoint**: User Story 2 complete — copy buttons work with real key regardless of `<APIKeys />` mask state.

---

## Phase 5: User Story 3 — Regenerate an API Key (Priority: P3)

**Goal**: A user can regenerate their API key. The old key is immediately rejected by the MCP server. The new key is displayed unmasked once by `<APIKeys />`.

**Independent Test**: (1) User has an existing `ak_...` key and uses it to successfully call `/mcp`. (2) User clicks "Regenerate" in `<APIKeys />`, confirms, and new key is shown. (3) Old key now returns 401 from `/mcp`. (4) New key (pasted into input) returns 200 from `/mcp`.

- [x] T016 Verify `<APIKeys />` component includes a built-in confirmation step before revocation; if not, add a React state-managed confirmation step to `frontend/src/components/ConnectView/index.tsx` using a `confirmingRegeneration` boolean state — render an inline confirmation UI (a visible prompt within the component, **not** `window.confirm()`) that warns "Your existing key will stop working immediately" and requires an explicit "Confirm" button click before invoking the Clerk revoke action
- [x] T017 Add contract test T-MCP-06 to `backend/tests/contract/test_auth_contract.py`: simulate revoked API key (mock `is_signed_in=False` with a previously-valid `ak_` token) → assert 401 response, confirming `UserContextMiddleware` correctly rejects revoked keys

**Checkpoint**: User Story 3 complete — key regeneration flow is guarded and old keys are immediately rejected.

---

## Phase 6: User Story 4 — View Instructions for Multiple AI Coding Assistants (Priority: P4)

**Goal**: Users can easily browse per-assistant setup instructions in a tab or accordion layout, without needing to know config file paths or formats.

**Independent Test**: A user opens the Connect tab, selects each of the 4 assistant options, and verifies: (1) the correct config file path is shown, (2) the config snippet is syntactically complete for that assistant's format, (3) no placeholders remain except `YOUR_API_KEY` (before key is pasted) and the server URL (when env var is unset).

- [x] T018 Refactor the 4 assistant config snippet blocks in `frontend/src/components/ConnectView/index.tsx` from a flat list into a tab or accordion component with one panel per assistant (Claude Code, Cursor, GitHub Copilot, Amazon Kiro); each panel shows the target config file path, a human-readable description, and the config snippet/command; **update existing T008 Vitest tests** to expect tab/accordion structure — use `getByRole('tab')` or `getByLabelText` queries so assertions remain valid after this refactor
- [x] T019 [P] Add tab/accordion styles and active-tab indicator styles to `frontend/src/components/ConnectView/ConnectView.module.css` to visually distinguish the selected assistant panel
- [x] T020 [P] Add Vitest tests for tab/accordion navigation in `frontend/src/__tests__/ConnectView.test.tsx`: clicking each assistant tab renders the correct config snippet and file path hint

**Checkpoint**: All 4 user stories are independently functional and testable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Startup validation, documentation accuracy, and end-to-end verification.

- [x] T021 [P] Add startup validation for `CLERK_SECRET_KEY` in `backend/src/persona/server.py` — call `resolve_clerk_secret_key()` at server startup (not lazily on first request) so a missing key surfaces immediately at boot rather than on first MCP call
- [x] T022 [P] Update `CLAUDE.md` Active Technologies section to include `clerk-backend-api ≥1.0.0` entry under the `011-mcp-instructions` feature bullet (already present as placeholder — confirm accuracy)
- [ ] T023 Run quickstart.md steps end-to-end in local dev environment (`make run-local`, log in, Connect tab, generate key, paste key, copy Claude Code command, verify `claude mcp list` shows `persona`); **time the Connect section load and manually verify it renders in under 2 seconds (SC-005)**
- [x] T024 [P] Update `README.md` to document: the new Connect tab and its purpose, `CLERK_SECRET_KEY` as a required backend environment variable, `VITE_MCP_SERVER_URL` as a required frontend build-time environment variable, and MCP dual-auth support (API key + session JWT) in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T002 and T003 can run in parallel
- **Foundational (Phase 2)**: Depends on T001 (clerk-backend-api installed); T004 and T005 can run in parallel
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) complete; T006, T007, T008 can run in parallel (test files); T010, T011, T012 can run in parallel; T013 depends on T012
- **User Story 2 (Phase 4)**: Depends on T013 (ConnectView exists); T014 before T015
- **User Story 3 (Phase 5)**: T016 depends on T013; T017 is independent (contract test, runs in parallel with T016)
- **User Story 4 (Phase 6)**: Depends on T013 (ConnectView exists); T018 before T019/T020; T019 and T020 can run in parallel
- **Polish (Phase 7)**: Depends on all user stories complete; T021, T022, and T024 can run in parallel

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (Phase 2) — no dependency on other user stories
- **US2 (P2)**: Depends on US1 ConnectView (T013) existing — independently testable
- **US3 (P3)**: Depends on US1 middleware (T009) and ConnectView (T013) — independently testable (old key rejection is automatic via Clerk)
- **US4 (P4)**: Depends on US1 ConnectView (T013) — refactors layout only, independently testable

### Within Each User Story

- Tests MUST be written first and FAIL before implementation begins (TDD)
- Backend helpers (T004, T005) before middleware (T009)
- Middleware (T009) before contract tests pass
- Config/env tasks before component rendering tasks

---

## Parallel Examples

### Phase 3 (US1) — Launch All Tests in Parallel

```bash
# Write all 3 test files simultaneously (different files, no deps):
Task: "Write contract tests T-MCP-01 to T-MCP-05 in backend/tests/contract/test_auth_contract.py"
Task: "Write unit tests for authenticate_mcp_request() in backend/tests/unit/test_auth.py"
Task: "Write Vitest tests for ConnectView in frontend/src/__tests__/ConnectView.test.tsx"
```

### Phase 3 (US1) — Launch Frontend Setup in Parallel

```bash
# After T009 (backend done), launch frontend tasks simultaneously:
Task: "Add 'connect' to View union in frontend/src/App.tsx"
Task: "Add Connect tab button to frontend/src/components/Navigation.tsx"
Task: "Create frontend/src/components/ConnectView/ConnectView.module.css"
# Then T013 (depends on T012 CSS being created first)
```

### Phase 7 (Polish) — Launch Polish in Parallel

```bash
Task: "Add startup validation for CLERK_SECRET_KEY in backend/src/persona/server.py"
Task: "Update CLAUDE.md Active Technologies section"
Task: "Update README.md to document Connect tab and new env vars"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T005) — CRITICAL: blocks all stories
3. Write tests (T006–T008) — verify they FAIL
4. Complete Phase 3: User Story 1 (T009–T013)
5. **STOP and VALIDATE**: Run `make check` in both `backend/` and `frontend/`; test MCP connection end-to-end via quickstart.md Step 6
6. Deploy/demo if ready — new users can now connect any AI coding assistant

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (backend dual auth + ConnectView) → Test independently → Deploy (MVP!)
3. Add US2 (copy buttons) → Test independently → Deploy
4. Add US3 (regeneration confirmation) → Test independently → Deploy
5. Add US4 (tab/accordion layout) → Test independently → Deploy

Each story adds value without breaking previous stories.

---

## Phase 8: Defect Fixes

**Purpose**: Fix build and runtime errors discovered after initial implementation.

- [x] T025 Fix TypeScript build error in `frontend/src/components/ConnectView/index.tsx` — remove invalid `onKeyCreated` and `onKeyRegenerated` props from `<APIKeys />` (Clerk's `APIKeysProps` does not accept these); convert conditional warning banner (`keyJustCreated` state) to a static informational tip that is always visible; remove `testKeyJustCreated` test-only prop; add `APIKeysErrorBoundary` error boundary around `<APIKeys />` to gracefully handle Clerk API keys being disabled
- [x] T026 [P] Update `frontend/src/__tests__/ConnectView.test.tsx` to match new static banner behavior — replace `keyJustCreated`-dependent assertions with static tip assertions; add error boundary fallback test
- [x] T027 [P] Add `.apiKeysDisabled` error boundary fallback styles to `frontend/src/components/ConnectView/ConnectView.module.css`
- [x] T028 Fix `make run` failure — add `CLERK_SECRET_KEY=${CLERK_SECRET_KEY}` passthrough to `docker-compose.yml`; add `VITE_CLERK_PUBLISHABLE_KEY` as Docker build arg; add both to `.env.example`
- [x] T029 [P] Fix MCP route matching in `backend/src/persona/server.py` — replace `app.mount("/mcp", mcp_app)` with direct route injection (`app.router.routes.append`) to prevent Starlette's `Mount` regex from requiring a trailing slash, which caused `POST /mcp` to fall through to `StaticFiles` returning 405

---

## Phase 9: Defect Fixes (Round 2)

**Purpose**: Fix runtime issues discovered during end-to-end testing.

- [x] T030 Fix JWT auth failure at `POST /mcp` — wrap the incoming Starlette `Request` as an `httpx.Request` in `authenticate_mcp_request()` (`backend/src/persona/auth.py`) before passing to the Clerk SDK's `authenticate_request()`, ensuring full protocol compatibility for session token verification; add warning log on auth failure with reason/message for diagnostics; add unit test `test_wraps_request_as_httpx_request` in `backend/tests/unit/test_auth.py`; update `_make_mock_request` to use a real Starlette `Request` instead of `MagicMock` for better test fidelity
- [x] T031 Make warning banner dismissable in `ConnectView` — add `bannerDismissed` boolean state (default `false`) to `frontend/src/components/ConnectView/index.tsx`; wrap banner in conditional render `{!bannerDismissed && ...}`; add dismiss `<button>` with `&times;` icon that sets `bannerDismissed` to `true`; update `frontend/src/__tests__/ConnectView.test.tsx` with new `tip is dismissable via close button` test; CSS `.warningDismiss` styles already present

---

## Notes

- `[P]` tasks touch different files — no dependency conflicts, safe to run in parallel
- `[USn]` label maps each task to the spec.md user story for traceability
- TDD: test tasks must be written and confirmed FAILING before their paired implementation tasks
- `<APIKeys />` import path must be verified at implementation time — `@clerk/clerk-react` exports may differ from `@clerk/nextjs` docs (see research.md Decision 5); fallback is `useClerk().apiKeys.create()`
- `CLERK_SECRET_KEY` is NEVER exposed to the frontend; `VITE_MCP_SERVER_URL` is build-time safe
- No DB schema migrations required (all API key state lives in Clerk)
- The REST API (`/api/*`) auth path is unchanged — only `UserContextMiddleware` at `/mcp` is updated
