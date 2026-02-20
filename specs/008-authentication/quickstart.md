# Quickstart: Authentication & Multi-user Support (rev 1)

**Date**: 2026-02-18
**Feature**: 008-authentication

## 1. Clerk Setup

To enable authentication, you need a Clerk account and a project.

- [ ] **Create a Clerk Project**: Go to [clerk.com](https://clerk.com) and create a new application.
- [ ] **Enable Google OAuth**: In the Clerk dashboard, go to **Configure > SSO Connections > Google**, toggle it **On**, and save.
- [ ] **Enable GitHub OAuth**: In the Clerk dashboard, go to **Configure > SSO Connections > GitHub**, toggle it **On**, and save.
- [ ] **Collect Frontend Key**: In the dashboard, go to **API Keys** and copy the `Publishable Key` (`pk_test_...`).
- [ ] **Collect Backend Keys**: In the dashboard, go to **API Keys** and note the `JWKS URL` (shown on the page as `https://<your-instance>.clerk.accounts.dev/.well-known/jwks.json`) and the `Issuer` value (e.g. `https://<your-instance>.clerk.accounts.dev`).
- [ ] **Create Webhook Signing Secret**: In the dashboard, go to **Webhooks > Add Endpoint**, set the URL to `https://<your-domain>/api/webhooks/clerk`, select the `user.deleted` event, and copy the **Signing Secret** (`whsec_...`).

## 2. Environment Variables

### Frontend (`frontend/.env.local`)
```env
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
```

### Backend (`backend/.env`)
```env
CLERK_JWKS_URL=https://<your-instance>.clerk.accounts.dev/.well-known/jwks.json
CLERK_ISSUER=https://<your-instance>.clerk.accounts.dev
CLERK_WEBHOOK_SECRET=whsec_...
```

## 3. Running the Project

### Backend
1.  **Install dependencies**: `uv sync` (ensure `python-jose` and `svix` are installed).
2.  **Run migrations**: `python src/persona/migrations.py` (will upgrade from v3 to v4).
3.  **Start server**: `make run` (from `backend/`) or `make run-local` (from repository root).

### Frontend
1.  **Install dependencies**: `npm install`.
2.  **Start dev server**: `npm run dev`.

## 4. Testing Authentication

### 1. Web Login
1.  Open `http://localhost:5173`.
2.  You should be redirected to the Clerk Sign-In page.
3.  **Verify social buttons are visible**: Confirm that "Continue with Google" and "Continue with GitHub" buttons appear on the sign-in page. These appear automatically when social connections are enabled in the Clerk dashboard (no code changes required).
4.  Sign in with Google or GitHub.
5.  Verify you are redirected back to the Persona dashboard.
6.  Verify a user avatar (from `<UserButton>`) appears in the app header.

### 2. API Authorization (Manual)
To test protected endpoints via `curl`, you need a JWT.
1.  In the browser, open DevTools > Network.
2.  Find a request to `/api/...`.
3.  Copy the `Authorization` header value.

```bash
# Test protected endpoint
curl http://localhost:8080/api/resumes \
  -H "Authorization: Bearer <token>"
```

### 3. Multi-user Isolation
1.  Sign in as User A, create a resume.
2.  Sign in as User B (different browser/incognito), create a different resume.
3.  Verify User B cannot see User A's resume.

### 4. Webhook Testing (Simulating Clerk)
1.  Use a tool like `ngrok` or `localtunnel` to expose your local backend (port 8080).
2.  Configure the Clerk Webhook URL in the Clerk dashboard to point to `https://<your-url>/api/webhooks/clerk`.
3.  Select the `user.deleted` event.
4.  Delete a test user in Clerk and verify their data is purged from your local SQLite database.

## 5. MCP Server Auth

### HTTP (streamable-http) Mode
Ensure your MCP client (e.g., Claude Desktop) is configured to send the `Authorization: Bearer <token>` header when connecting to the streamable-http endpoint.

### Stdio Mode (CLI Testing)
For local testing without a full JWT flow:
```bash
# Simulate a specific user
export PERSONA_USER_ID=user_manual_test_123
python -m persona.server --mcp
```
