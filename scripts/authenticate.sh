#!/usr/bin/env bash
# scripts/authenticate.sh
#
# Authenticate with Clerk using the email-code strategy (test mode).
# Uses Clerk's reserved +clerk_test addresses, which skip actual email
# delivery and accept the fixed OTP code 424242.
#
# Usage:
#   TOKEN=$(./scripts/authenticate.sh user+clerk_test@example.com)
#   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/resumes
#
# The token is also written to .clerk_token in the repo root for convenience.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${REPO_ROOT}/frontend/.env.local"
TOKEN_FILE="${REPO_ROOT}/.clerk_token"
TEST_OTP="424242"

# ── Prerequisites ─────────────────────────────────────────────────────────────
for cmd in python3 curl; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: '$cmd' is required but not found in PATH." >&2
    exit 1
  fi
done

# ── Load VITE_CLERK_PUBLISHABLE_KEY from frontend/.env.local ─────────────────
if [[ ! -f "$ENV_FILE" ]]; then
  cat >&2 <<EOF

Error: frontend/.env.local not found.

Setup instructions:
  1. Create frontend/.env.local with your Clerk publishable key:

       VITE_CLERK_PUBLISHABLE_KEY=pk_test_<your-key>

  2. Get your publishable key from:
       https://dashboard.clerk.com → Your App → API Keys

  3. Re-run this script.
EOF
  exit 1
fi

CLERK_KEY=$(grep '^VITE_CLERK_PUBLISHABLE_KEY=' "$ENV_FILE" | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d "'" | xargs)

if [[ -z "$CLERK_KEY" ]]; then
  cat >&2 <<EOF

Error: VITE_CLERK_PUBLISHABLE_KEY is not set in frontend/.env.local.

Setup instructions:
  1. Open frontend/.env.local and add:

       VITE_CLERK_PUBLISHABLE_KEY=pk_test_<your-key>

  2. Get your publishable key from:
       https://dashboard.clerk.com → Your App → API Keys

  3. Re-run this script.
EOF
  exit 1
fi

# ── Decode Clerk FAPI base URL from the publishable key ──────────────────────
# Key format: pk_test_<base64(instance_domain + "$")>
FAPI_BASE=$(python3 - "$CLERK_KEY" <<'PYEOF'
import sys, base64
key = sys.argv[1]
for prefix in ("pk_test_", "pk_live_"):
    if key.startswith(prefix):
        key = key[len(prefix):]
        break
padding = (4 - len(key) % 4) % 4
decoded = base64.b64decode(key + "=" * padding).decode("utf-8")
print("https://" + decoded.rstrip("$"))
PYEOF
)

# ── Resolve email ─────────────────────────────────────────────────────────────
EMAIL="${1:-}"
if [[ -z "$EMAIL" ]]; then
  printf "Test email (e.g. you+clerk_test@example.com): " >/dev/tty
  read -r EMAIL </dev/tty
fi

if [[ "$EMAIL" != *+clerk_test* ]]; then
  echo "Warning: email does not contain '+clerk_test'." >&2
  echo "  Only +clerk_test addresses skip real email delivery and accept OTP 424242." >&2
  echo >&2
fi

echo "Authenticating with Clerk" >&2
echo "Instance : $FAPI_BASE" >&2
echo "Email    : $EMAIL" >&2
echo >&2

# Maintain cookies across all FAPI requests (Cloudflare edge cookies etc.)
COOKIE_JAR=$(mktemp)
trap 'rm -f "$COOKIE_JAR"' EXIT

# ── Step 0: Dev-browser handshake (required for *.accounts.dev instances) ────
# POST /v1/dev_browser returns {"token":"eyJ..."} which must be appended as
# __clerk_db_jwt query param on every subsequent FAPI request.
DB_JWT_PARAM=""
if [[ "$FAPI_BASE" == *".accounts.dev"* || "$CLERK_KEY" == pk_test_* ]]; then
  DB_JWT=$(curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
    -X POST "${FAPI_BASE}/v1/dev_browser" \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('token',''))" 2>/dev/null || true)
  if [[ -n "$DB_JWT" ]]; then
    DB_JWT_PARAM="?__clerk_db_jwt=${DB_JWT}"
  fi
fi

# Helper: POST to FAPI, check HTTP status, return response body.
# The __clerk_db_jwt query param is automatically appended for dev instances.
fapi_post() {
  local path="$1"
  shift
  local raw
  raw=$(curl -s -w "\n__HTTP_STATUS__%{http_code}" \
    -c "$COOKIE_JAR" -b "$COOKIE_JAR" \
    -X POST "${FAPI_BASE}${path}${DB_JWT_PARAM}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    "$@")
  local status body
  status=$(printf '%s' "$raw" | tail -1 | sed 's/__HTTP_STATUS__//')
  body=$(printf '%s' "$raw" | sed '$d')
  if [[ "$status" != "200" && "$status" != "422" ]]; then
    local msg
    msg=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    errs = d.get('errors', [])
    print(errs[0].get('long_message') or errs[0].get('message', 'HTTP $status') if errs else 'HTTP $status')
except Exception:
    print('HTTP $status')
" <<< "$body" 2>/dev/null || echo "HTTP $status")
    echo "Error: Clerk API call failed (${path}) — ${msg}" >&2
    exit 1
  fi
  printf '%s' "$body"
}

# ── Step 1: Create sign-in, request email_code strategy ──────────────────────
echo "Step 1/3  Creating sign-in…" >&2
STEP1=$(fapi_post "/v1/client/sign_ins" \
  --data-urlencode "identifier=${EMAIL}")

SIGN_IN_ID=$(python3 -c "import json,sys; print(json.loads(sys.argv[1])['response']['id'])" "$STEP1")

EMAIL_ADDRESS_ID=$(python3 - "$STEP1" "$EMAIL" <<'PYEOF'
import json, sys
data = json.loads(sys.argv[1])
email = sys.argv[2]
factors = data["response"].get("supported_first_factors", [])
match = next(
    (f for f in factors if f.get("strategy") == "email_code" and f.get("safe_identifier") == email),
    next((f for f in factors if f.get("strategy") == "email_code"), None),
)
if not match:
    print("", end="")
else:
    print(match.get("email_address_id", ""), end="")
PYEOF
)

if [[ -z "$EMAIL_ADDRESS_ID" ]]; then
  echo "Error: email_code strategy not available for this account." >&2
  echo "  Ensure the account exists and email code sign-in is enabled in your Clerk dashboard." >&2
  exit 1
fi

# ── Step 2: Prepare first factor (triggers OTP — skipped for +clerk_test) ────
echo "Step 2/3  Preparing email code factor…" >&2
fapi_post "/v1/client/sign_ins/${SIGN_IN_ID}/prepare_first_factor" \
  -d "strategy=email_code" \
  --data-urlencode "email_address_id=${EMAIL_ADDRESS_ID}" \
  >/dev/null

# ── Step 3: Attempt first factor with test OTP 424242 ────────────────────────
echo "Step 3/3  Submitting OTP ${TEST_OTP}…" >&2
STEP3=$(fapi_post "/v1/client/sign_ins/${SIGN_IN_ID}/attempt_first_factor" \
  -d "strategy=email_code" \
  --data-urlencode "code=${TEST_OTP}")

# ── Extract JWT ───────────────────────────────────────────────────────────────
JWT=$(python3 - "$STEP3" <<'PYEOF'
import json, sys
data = json.loads(sys.argv[1])
sign_in = data.get("response", {})
status = sign_in.get("status")
if status != "complete":
    print(f"INCOMPLETE:{status}", end="")
    sys.exit(0)
session_id = sign_in.get("created_session_id")
sessions = data.get("client", {}).get("sessions", [])
session = next((s for s in sessions if s["id"] == session_id), sessions[0] if sessions else None)
if not session:
    print("NO_SESSION", end="")
    sys.exit(1)
print(session.get("last_active_token", {}).get("jwt", ""), end="")
PYEOF
)

if [[ "$JWT" == INCOMPLETE:* ]]; then
  echo "Error: Sign-in incomplete (status: ${JWT#INCOMPLETE:})." >&2
  exit 1
fi

if [[ -z "$JWT" || "$JWT" == "NO_SESSION" ]]; then
  echo "Error: Could not extract session token from Clerk response." >&2
  exit 1
fi

# ── Emit token ────────────────────────────────────────────────────────────────
echo "$JWT" > "$TOKEN_FILE"
chmod 600 "$TOKEN_FILE"
echo >&2
echo "Token saved to .clerk_token" >&2
echo >&2
echo "Usage:" >&2
echo "  TOKEN=\$(cat .clerk_token)" >&2
echo "  curl -H \"Authorization: Bearer \$TOKEN\" http://localhost:8000/api/resumes" >&2

echo "$JWT"
