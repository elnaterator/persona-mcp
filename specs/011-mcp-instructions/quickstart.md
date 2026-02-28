# Quickstart: MCP Server Connection Instructions & API Key Management

**Feature**: `011-mcp-instructions`
**Date**: 2026-02-27

---

## Prerequisites

- Clerk account with native API keys enabled (public beta, Dec 2025+)
- `CLERK_SECRET_KEY` from your Clerk dashboard (Settings → API Keys → Secret keys)
- Existing dev environment running (`make run-local` or `docker compose up`)

---

## Step 1: Configure Backend Environment

Add `CLERK_SECRET_KEY` to your backend environment. For local dev:

```bash
# backend/.env (or however you supply env vars locally)
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here
```

This key is used by `UserContextMiddleware` to verify both Clerk session JWTs and native API keys at the `/mcp` endpoint.

Existing variables (`CLERK_JWKS_URL`, `CLERK_ISSUER`) remain required for the REST API JWT path.

---

## Step 2: Configure Frontend Environment

Add `VITE_MCP_SERVER_URL` to `frontend/.env.local`:

```bash
VITE_MCP_SERVER_URL=http://localhost:8000/mcp
```

For production, set this to your deployed server URL (e.g., `https://your-persona-server.com/mcp`).

If unset, config snippets in the UI display the placeholder `https://your-persona-server.com/mcp`.

---

## Step 3: Install New Backend Dependency

```bash
cd backend
uv add clerk-backend-api
```

This adds `clerk-backend-api>=1.0.0` to `pyproject.toml` and `uv.lock`.

---

## Step 4: Run Tests

```bash
# Backend — verify dual auth works
cd backend
make check

# Frontend — verify Connect tab renders
cd frontend
make check
```

---

## Step 5: Try the Connect Tab

1. Start the dev server: `make run-local` (from repo root)
2. Open the frontend: http://localhost:5173
3. Log in with your Clerk account
4. Click the **Connect** tab (4th tab in the navigation bar)
5. The `<APIKeys />` component appears — click "Generate API Key"
6. The full key is displayed once — paste it into the "Paste your API key" input below
7. Config commands for all four assistants update with your real key
8. Copy the command for your preferred assistant and configure it

---

## Step 6: Verify MCP Connection

After configuring your preferred assistant, test the connection:

```bash
# Example: Claude Code — verify MCP server is reachable
claude mcp list
# Should show "persona" in the list

# Run a quick tool call
# In Claude Code chat: @persona <any prompt>
```

---

## Supported Assistants at Launch

| Assistant | Config file | Transport |
|---|---|---|
| Claude Code | CLI or `.mcp.json` | HTTP (`--transport http`) |
| Cursor | `.cursor/mcp.json` | HTTP |
| GitHub Copilot | `.vscode/mcp.json` | HTTP |
| Amazon Kiro | `.kiro/settings/mcp.json` | HTTP |

See `research.md` for exact config snippets for each assistant.

---

## Troubleshooting

**"Not authenticated" from MCP endpoint with a valid API key**
- Check that `CLERK_SECRET_KEY` is set correctly in the backend environment
- Verify the key starts with `ak_` (Clerk native API key format)
- Check server logs for `TokenType.API_KEY` verification errors

**Config snippets show placeholder instead of my key**
- Paste your API key into the "Paste your API key" text input in the Connect tab
- The substitution is client-side only; the key is never sent to the server

**`CLERK_SECRET_KEY` not found in environment**
- The backend will log a `KeyError` or `500` — add the env var and restart
