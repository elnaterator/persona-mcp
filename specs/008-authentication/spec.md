# Feature Specification: Authentication & Multi-user Support

**Feature Branch**: `008-authentication`  
**Created**: 2026-02-19  
**Status**: Draft  
**Input**: User description: "Update the feature specification for Authentication to use Clerk instead of Crew."

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
-->

### User Story 1 - Secure Sign-up and Sign-in (Priority: P1)

As a job seeker, I want to create a secure account and sign in to the application so that I can save my resumes and track my job applications across different sessions and devices.

**Why this priority**: Essential for personalization and data persistence. Without authentication, users cannot have a "persona" or save their work securely.

**Independent Test**: Can be fully tested by creating a new account, signing out, and signing back in to verify the session is restored.

**Acceptance Scenarios**:

1. **Given** a new user is on the landing page, **When** they choose to sign up and provide valid credentials or use a social provider, **Then** a new account is created and they are logged in.
2. **Given** a registered user, **When** they provide correct credentials at the sign-in screen, **Then** they are granted access to their personal dashboard.
3. **Given** a user provides incorrect credentials, **When** they attempt to sign in, **Then** they are shown a clear error message and denied access.

---

### User Story 2 - Personal Data Isolation (Priority: P1)

As a user, I want to be certain that my resumes, contact details, and application history are only visible to me and cannot be accessed by any other user of the platform.

**Why this priority**: Privacy and security are paramount. Data leakage between users would be a critical failure of the system.

**Independent Test**: Can be tested by creating two separate accounts and verifying that data created in Account A is not visible or accessible when logged into Account B.

**Acceptance Scenarios**:

1. **Given** two authenticated users (User A and User B), **When** User A creates a resume, **Then** User B cannot see that resume in their list.
2. **Given** User A's resume ID, **When** User B attempts to access that specific resume directly, **Then** access is denied with a clear authorization error.

---

### User Story 3 - Social Login Integration (Priority: P2)

As a user, I want to use my existing Google or GitHub accounts to sign in so that I don't have to remember another password.

**Why this priority**: Improves user onboarding and reduces friction.

**Independent Test**: Can be tested by selecting "Sign in with Google" and successfully authenticating through the Google OAuth flow.

**Acceptance Scenarios**:

1. **Given** the sign-in page, **When** a user selects a supported social provider, **Then** they are redirected to that provider's authentication screen.
2. **Given** a successful authentication via social provider, **When** the user is redirected back, **Then** they are logged into Persona with their social identity.

---

### User Story 4 - User Profile and Session Management (Priority: P2)

As a user, I want to manage my profile information and securely sign out of the application when I am finished.

**Why this priority**: Basic user control and security practice for shared devices.

**Independent Test**: Can be tested by updating profile information and clicking the sign-out button to ensure the session is invalidated.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they view their profile, **Then** they can see their account details (email, name).
2. **Given** an authenticated user, **When** they select "Sign Out", **Then** they are redirected to the landing page and cannot access protected routes without signing back in.

### Edge Cases

- **Session Expiration**: The Clerk React SDK silently auto-refreshes short-lived JWTs in the background; no user interruption occurs during normal use. If the long-lived session fully expires (e.g., 30-day inactivity), the app redirects to the sign-in page. No custom token-refresh logic is required.
- **Account Deletion**: What happens to a user's data when they choose to delete their account?
- **Network Interruptions during Auth**: If the connection to Clerk is lost during sign-in, the system MUST display a user-friendly error message and allow the user to retry. No fallback authentication path is provided; Clerk availability is a hard dependency (see A-002).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a unified sign-in/sign-up interface using Clerk.
- **FR-002**: System MUST support email/password authentication.
- **FR-003**: System MUST support Social Login (OAuth) via Google and GitHub.
- **FR-004**: System MUST enforce strict data isolation using the authenticated user's unique identifier.
- **FR-005**: System MUST provide a secure way for users to manage their account profile (name, email, profile picture).
- **FR-006**: System MUST support secure sign-out, invalidating the session on both the client and the authentication provider.
- **FR-007**: System MUST automatically redirect unauthenticated users to the sign-in page when they attempt to access protected routes.
- **FR-008**: System MUST hard-delete all user data (resumes and applications) immediately upon account deletion to comply with privacy best practices.
- **FR-009**: The backend MUST validate every API request by verifying the Clerk-issued JWT against Clerk's JWKS endpoint using `python-jose`; the verified `sub` claim is used as the user's authoritative identifier. No request is trusted on the basis of a client-supplied user ID alone.
- **FR-010**: Clerk webhooks (verified via `svix`) MUST be used exclusively for user lifecycle events (e.g., account deletion triggering cascading data removal); they are NOT used for per-request authorization.
- **FR-011**: The MCP server in HTTP mode MUST enforce the same Clerk JWT verification as the REST API; all tool responses MUST be scoped to the authenticated user's `sub`. The MCP server in stdio mode is trusted-local and requires no authentication.
- **FR-012**: A local SQLite `users` table (keyed by Clerk `sub`) MUST serve as the foreign-key anchor for all owned tables (`resumes`, `applications`). A user row MUST be upserted on first successful sign-in. All owned-data queries MUST join through this table to enforce referential integrity.

### Key Entities

- **User**: Represents a unique individual authenticated via Clerk. Stored in a local SQLite `users` table to serve as the foreign-key anchor for all owned data.
  - Attributes: `id TEXT PRIMARY KEY` (Clerk `sub`), `email TEXT`, `display_name TEXT`, `created_at TIMESTAMP`.
  - Relationships: Owns multiple Resumes and Job Applications via foreign key.
  - Lifecycle: Row is created on first successful sign-in (upsert); row (and all owned data) is hard-deleted on account deletion webhook.
- **Resume**: Owned by a User via `user_id TEXT NOT NULL REFERENCES users(id)`.
- **Job Application**: Owned by a User via `user_id TEXT NOT NULL REFERENCES users(id)`.

## Assumptions

- **A-001**: Clerk handles all security-critical aspects of the authentication flow (encryption, token rotation, etc.).
- **A-002**: Users have a stable internet connection required to reach the Clerk authentication endpoints.
- **A-003**: The frontend application will securely store and manage the Clerk session token.
- **A-004**: Clerk's JWKS endpoint is publicly reachable from the backend at runtime; JWT verification is performed locally (no per-request network call to Clerk beyond periodic key refresh).

## Clarifications

### Session 2026-02-19

- Q: How does the backend verify that an incoming API request belongs to a specific Clerk user — JWT validation via JWKS, trust a client-supplied header, or a per-request Clerk SDK call? → A: Backend validates Clerk JWT on every request (JWKS + python-jose); svix only for lifecycle webhooks.
- Q: How does the system handle a user whose session expires while they are mid-action (e.g., editing a resume)? → A: Clerk SDK silently auto-refreshes tokens; redirect to sign-in only on full session expiry.
- Q: Does the MCP server's HTTP mode need to enforce Clerk JWT authentication, or is it out of scope / single-user assumed? → A: MCP HTTP mode requires Clerk JWT; stdio mode is trusted-local (no auth).
- Q: How is user ownership stored in SQLite — `user_id` column on each table, a separate `users` table with foreign keys, or a JSON blob? → A: Separate `users` table keyed by Clerk `sub`; owned tables foreign-key to it.
- Q: How does the system recover if the connection to Clerk is lost during sign-in? → A: Show error + retry prompt; no fallback (Clerk availability is a hard dependency).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: New users can complete the sign-up process and reach their dashboard in under 45 seconds.
- **SC-002**: 100% of data access requests for resumes and applications MUST be verified against the authenticated user's ID.
- **SC-003**: 0% data leakage: No user should ever be able to view or modify data belonging to another user.
- **SC-004**: System supports at least 1,000 concurrent authenticated sessions without performance degradation.
- **SC-005**: 99.9% availability for the authentication service (relying on Clerk's uptime).
