# Feature Specification: MCP Server Connection Instructions & API Key Management

**Feature Branch**: `011-mcp-instructions`
**Created**: 2026-02-27
**Status**: Draft
**Input**: User description: "Add MCP server connection instructions UI with API key management via Clerk"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate API Key and Connect a New Assistant (Priority: P1)

A logged-in user who has never configured an AI coding assistant to use Persona arrives at the application and immediately sees a prominent "Connect to MCP" section. They have no API key yet. They click "Generate API Key," see the key briefly in full, copy the ready-made config command for their preferred AI coding assistant (e.g., Claude Code), paste it into the appropriate config file, and their assistant is immediately connected.

**Why this priority**: This is the core value proposition of the entire Persona MCP server — users can only benefit from MCP tools if they know how to connect. Every user must complete this flow to get value. Without it, the server is inaccessible.

**Independent Test**: Can be tested end-to-end by a brand new user with no API key: generate key → copy Claude Code command → paste into Claude Code config → verify connection works. Delivers the full onboarding value.

**Acceptance Scenarios**:

1. **Given** a logged-in user with no existing API key, **When** they visit the app, **Then** the "Connect to MCP" section is visible without scrolling on the default view and shows a "Generate API Key" call-to-action.
2. **Given** a user clicks "Generate API Key," **When** the key is successfully created, **Then** the full API key is displayed unmasked exactly once, a prominent warning banner reading "Copy your API key now — this is the only time you will see it in full. If you lose it, you will need to generate a new one" is displayed adjacent to the key, and config snippets for each supported AI coding assistant are shown with the real key embedded.
3. **Given** the user has not yet copied the key and navigates away or refreshes, **When** they return, **Then** the key is displayed masked and the user is informed they cannot retrieve the full key again (only regenerate).

---

### User Story 2 - Copy a Config Command with Existing API Key (Priority: P2)

A returning user who already has an API key wants to configure an additional AI coding assistant. They visit the app, find the "Connect to MCP" section, reveal their existing key, and copy the config command for the new assistant.

**Why this priority**: Users set up multiple tools over time. Config commands must remain easy to copy even after initial generation.

**Independent Test**: A user with an existing API key can reveal the masked key and copy a working config command for any listed assistant. No key generation required.

**Acceptance Scenarios**:

1. **Given** a user has an existing API key, **When** they view the Connect section, **Then** the key is displayed as masked (e.g., `persona_••••••••••••abcd`) with a "Show" toggle button.
2. **Given** the user clicks "Show," **When** the key is revealed, **Then** the full key appears in the `<APIKeys />` display field. Config snippets update to show the real key only when the user pastes the key into the API key input field below the component.
3. **Given** the user clicks the copy button next to a specific assistant's config command, **When** copied, **Then** the clipboard contains the exact command with the real (unmasked) API key embedded, even if the display is still masked.

---

### User Story 3 - Regenerate an API Key (Priority: P3)

A user suspects their API key has been compromised, or simply wants to rotate credentials. They click "Regenerate API Key," confirm the action via a prompt, and a new key is generated. The old key stops working immediately. The new key is shown unmasked exactly once.

**Why this priority**: Security hygiene requires the ability to revoke compromised credentials without account disruption.

**Independent Test**: A user with an existing key can regenerate it. The old key immediately returns 401 on the MCP server, and the new key is presented unmasked for copying.

**Acceptance Scenarios**:

1. **Given** a user has an existing API key, **When** they click "Regenerate API Key," **Then** a confirmation dialog explains that the old key will stop working immediately and asks them to confirm.
2. **Given** the user confirms regeneration, **When** the operation completes, **Then** the new key is displayed unmasked, the same "Copy your API key now" warning banner reappears, and the old key no longer authenticates against the Persona MCP server.
3. **Given** the user cancels the confirmation dialog, **When** dismissed, **Then** no change occurs and the existing key remains valid.

---

### User Story 4 - View Instructions for Multiple AI Coding Assistants (Priority: P4)

A user wants to configure a specific AI coding assistant they haven't used before. They can browse through tab- or accordion-style instructions for each supported assistant, with copy-ready config commands, without having to know the correct config file format or location.

**Why this priority**: Each AI coding assistant has a different config format. Users shouldn't need to research this on their own.

**Independent Test**: A user can view syntactically correct, copy-ready config commands for each listed assistant without needing to understand MCP config formats.

**Acceptance Scenarios**:

1. **Given** the Connect section is displayed, **When** the user views it, **Then** instructions are available for at minimum: Claude Code, Cursor, GitHub Copilot, and Amazon Kiro.
2. **Given** the user selects a specific assistant's tab or section, **When** displayed, **Then** the config command or config snippet is complete and correct — no placeholders except possibly the server URL if self-hosting.
3. **Given** the user copies a command, **When** they paste it into the assistant's config, **Then** no manual editing is required (the API key and server URL are already substituted).

---

### Edge Cases

- What happens when the API key generation request fails due to a network or server error?
- How does the system handle a user who tries to copy a config command before generating a key?
- What if the user refreshes the page immediately after generating a key before copying it?
- What happens if the server URL is unavailable or not yet configured in the environment?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The authenticated UI MUST include a dedicated "Connect" tab in the primary navigation bar alongside Resumes, Applications, and Accomplishments. Selecting it displays the Connect to MCP section as the full main content area. The tab MUST be visible on all screen sizes ≥ 375px wide.

- **FR-002**: The Connect section MUST show the MCP server URL and per-assistant configuration snippets for at minimum: Claude Code, Cursor, GitHub Copilot, and Amazon Kiro. Each snippet MUST be syntactically complete and immediately usable.

- **FR-003**: If no API key exists for the current user, the Connect section MUST display a "Generate API Key" button as the primary call-to-action. Config snippets MUST show a non-functional placeholder instead of a real key until one is generated.

- **FR-004**: When an API key is generated or regenerated, the system MUST display the full plaintext key unmasked exactly once, in the same UI session, immediately after creation. The ConnectView MUST render a Persona-owned warning banner with the exact message: **"Copy your API key now — this is the only time you will see it in full. If you lose it, you will need to generate a new one."** This banner is Persona's responsibility to render and test independently of Clerk's `<APIKeys />` component. It MUST appear immediately adjacent to the key display, remain visible until the user explicitly dismisses it or navigates away from the Connect tab, and reappear after each regeneration.

- **FR-005**: After the initial unmasked display (or on all subsequent visits), the API key MUST be displayed in masked form with a toggle to reveal it within the current session. (Fulfilled by Clerk's `<APIKeys />` component behavior.)

- **FR-006**: Each per-assistant config snippet MUST have a dedicated one-click copy button. When clicked, the clipboard content MUST include the real (unmasked) API key regardless of the current mask/show toggle state.

- **FR-007**: If an API key exists, the Connect section MUST display a "Regenerate API Key" option. Clicking it MUST present a confirmation step that clearly warns the user the existing key will be immediately invalidated.

- **FR-008**: Upon confirmed regeneration, the system MUST immediately invalidate the old key on the backend so that subsequent MCP requests using the old key are rejected with an authentication error.

- ~~**FR-009**~~: ~~The backend MUST provide authenticated API endpoints to: create an API key for the current user, revoke/regenerate an API key, and retrieve the current user's API key status (exists or not, masked preview, creation date) — without ever returning the plaintext key after initial creation.~~ **Superseded**: Key lifecycle (create, revoke, display) is fully managed by Clerk and the `<APIKeys />` component. No custom backend endpoints are needed. See research.md Decision 7.

- **FR-010**: The MCP endpoint MUST accept both Clerk session JWTs and API keys in the Authorization Bearer header. The system MUST validate whichever token type is presented and associate the request with the correct user. Both authentication paths MUST yield an equivalent user context for MCP tool execution.

- **FR-011**: Each user may have at most one active API key at a time. Generating a new key automatically revokes any previously active key for that user.

- **FR-012**: Adding the "Connect" tab MUST NOT disrupt navigation to or functionality of the Resumes, Applications, and Accomplishments sections.

### Key Entities *(include if feature involves data)*

- **API Key**: A long-lived opaque credential associated with exactly one user. Attributes: unique identifier, masked preview (last 4 chars of the secret), creation timestamp, active/revoked status. The plaintext secret is never stored and cannot be retrieved after initial issuance.
- **API Key Status**: The user-facing representation of a user's key state — returned by the backend including: whether a key exists, when it was created, and the masked preview, but never the plaintext secret.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user with no prior API key can generate a key, copy a working config snippet for Claude Code, and have their MCP connection verified as working — all within 90 seconds of arriving at the Connect section. *Verified manually via T023 quickstart walkthrough; no automated timing enforcement.*
- **SC-002**: Config commands displayed in the UI work without modification in their respective AI coding assistants, with 100% syntactic validity across all listed assistants.
- **SC-003**: The masked API key display reveals no more than the last 4 characters at rest, so the full key cannot be read passively.
- **SC-004**: After an API key is regenerated, the old key is rejected by the MCP server within 1 second of the regeneration completing. *Verified via T017 mock-based contract test; exact sub-second timing is not automatically enforced (depends on Clerk's revocation propagation).*
- **SC-005**: The Connect section loads and displays the user's current API key status in under 2 seconds on a standard broadband connection.

## Assumptions

- The MCP server URL is provided to the frontend via a `VITE_MCP_SERVER_URL` build-time environment variable. Config snippets display this URL. If the variable is unset (e.g., local development), a recognizable placeholder (e.g., `https://your-persona-server.com/mcp`) is shown in its place.
- Clerk's native API key management (entered public beta December 2025) is the preferred mechanism. If it proves incompatible with this backend's verification flow, the implementation may fall back to generating random tokens on the backend, hashing them for storage, and associating them with Clerk user IDs — the spec does not mandate either approach.
- One active API key per user is sufficient for the current use case. Multiple named keys per user are out of scope.
- The user is already authenticated via Clerk before accessing the Connect section. Unauthenticated users see the Landing Page and are not shown MCP instructions.
- AI coding assistants supported at launch: Claude Code, Cursor, GitHub Copilot, and Amazon Kiro. Additional assistants can be added without spec changes if their config format is known.
- The MCP server uses streamable-HTTP transport (the `/mcp` endpoint), which is supported by all listed AI coding assistants via their remote/HTTP MCP transport configuration.
- The API key management UI is implemented using Clerk's prebuilt `<APIKeys />` React component, which handles generation, masking, one-time reveal, and revocation out of the box. Custom UI is out of scope for this feature.

## Clarifications

### Session 2026-02-27

- Q: Should the MCP endpoint accept both Clerk session JWTs and API keys, or API keys only? → A: Both — `/mcp` accepts Clerk JWTs and API keys; both yield an equivalent user context for MCP tool execution.
- Q: How should the Connect to MCP section be surfaced in the UI? → A: Dedicated "Connect" tab in the primary navigation bar, 4th tab alongside Resumes, Applications, Accomplishments.
- Q: How is the MCP server URL supplied to the config snippets? → A: Build-time env var `VITE_MCP_SERVER_URL`; shows a placeholder when unset.
