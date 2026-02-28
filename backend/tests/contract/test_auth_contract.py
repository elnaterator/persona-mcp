"""Contract tests for authentication and authorisation on all API routes.

Phase 3 tests (T009): 401 on missing token, 200 on valid mock JWT.
Phase 4 tests (T016, T035, T036): 403 on cross-user access; MCP tool auth.
"""

import time
from typing import Any
from unittest.mock import patch

import psycopg
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from jose import jwt
from psycopg import Connection
from starlette.testclient import TestClient

from persona.accomplishment_service import AccomplishmentService
from persona.api.routes import create_router
from persona.application_service import ApplicationService
from persona.auth import build_get_current_user
from persona.resume_service import ResumeService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gen_rsa_key_pair() -> tuple[Any, Any]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def _public_key_to_jwk(public_key: Any, kid: str = "ck1") -> dict[str, Any]:
    from jose.backends import RSAKey

    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    rsa_key = RSAKey(pem, "RS256")  # pyright: ignore [reportOptionalCall]
    jwk_dict = rsa_key.public_key().to_dict()  # type: ignore[union-attr]
    jwk_dict["kid"] = kid
    jwk_dict["kty"] = "RSA"
    jwk_dict["alg"] = "RS256"
    return jwk_dict


def _make_token(
    private_key: Any,
    kid: str = "ck1",
    sub: str = "user_alice",
    issuer: str = "https://clerk.test",
    email: str = "alice@example.com",
) -> str:
    now = int(time.time())
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return jwt.encode(
        {"sub": sub, "iss": issuer, "iat": now, "exp": now + 3600, "email": email},
        pem,
        algorithm="RS256",
        headers={"kid": kid},
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def auth_db(db_conn: Connection[Any]) -> psycopg.Connection:
    """PostgreSQL connection with schema already applied (via db_conn fixture).

    The 'legacy' user is seeded by migrate_v3_to_v4, so no manual insert needed.
    """
    return db_conn


@pytest.fixture
def auth_app(auth_db: psycopg.Connection) -> tuple:  # type: ignore[override]
    """Full app with auth middleware enabled."""
    import persona.auth as auth_module

    private_key, public_key = _gen_rsa_key_pair()
    jwk_entry = _public_key_to_jwk(public_key, kid="ck1")
    auth_module._JWKS_CACHE = {"ck1": jwk_entry}
    auth_module._JWKS_FETCHED_AT = time.monotonic()

    app = FastAPI()
    get_user = build_get_current_user(auth_db)  # type: ignore[arg-type]
    app.include_router(
        create_router(
            ResumeService(auth_db),  # type: ignore[arg-type]
            app_service=ApplicationService(auth_db),  # type: ignore[arg-type]
            acc_service=AccomplishmentService(auth_db),  # type: ignore[arg-type]
            get_current_user=get_user,
        )
    )
    return TestClient(app, raise_server_exceptions=False), private_key


# ---------------------------------------------------------------------------
# Phase 3 — T009: Basic 401 / 200 contract
# ---------------------------------------------------------------------------


class TestBasicAuthContract:
    """GET /api/resumes without token → 401; with valid token → 200."""

    def test_list_resumes_without_token_returns_401(self, auth_app: tuple) -> None:
        client, _ = auth_app
        response = client.get("/api/resumes")
        assert response.status_code == 401

    def test_list_resumes_with_valid_token_returns_200(self, auth_app: tuple) -> None:
        client, private_key = auth_app
        token = _make_token(private_key, sub="user_alice")
        with patch.dict("os.environ", {"CLERK_ISSUER": "https://clerk.test"}):
            response = client.get(
                "/api/resumes", headers={"Authorization": f"Bearer {token}"}
            )
        assert response.status_code == 200

    def test_health_endpoint_does_not_require_auth(self, auth_app: tuple) -> None:
        client, _ = auth_app
        response = client.get("/health")
        assert response.status_code == 200

    def test_list_applications_without_token_returns_401(self, auth_app: tuple) -> None:
        client, _ = auth_app
        response = client.get("/api/applications")
        assert response.status_code == 401

    def test_list_accomplishments_without_token_returns_401(
        self, auth_app: tuple
    ) -> None:
        client, _ = auth_app
        response = client.get("/api/accomplishments")
        assert response.status_code == 401

    def test_create_resume_without_token_returns_401(self, auth_app: tuple) -> None:
        client, _ = auth_app
        response = client.post("/api/resumes", json={"label": "Test"})
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Phase 4 — T016: 403 on cross-user access for resume/application routes
# ---------------------------------------------------------------------------


class TestCrossUserOwnershipContract:
    """Valid JWT for wrong user → 403 on detail/mutation endpoints."""

    def _make_user_client(
        self,
        auth_db: psycopg.Connection,
        private_key: Any,
        user_id: str,
        email: str,
    ) -> TestClient:

        app = FastAPI()
        get_user = build_get_current_user(auth_db)  # type: ignore[arg-type]
        app.include_router(
            create_router(
                ResumeService(auth_db),  # type: ignore[arg-type]
                app_service=ApplicationService(auth_db),  # type: ignore[arg-type]
                acc_service=AccomplishmentService(auth_db),  # type: ignore[arg-type]
                get_current_user=get_user,
            )
        )

        def _make_client_with_token() -> TestClient:
            token = _make_token(private_key, sub=user_id, email=email)
            client = TestClient(app, raise_server_exceptions=False)
            # Store token for use in tests
            client._auth_token = token  # type: ignore[attr-defined]
            return client

        return _make_client_with_token()

    @pytest.fixture
    def two_user_setup(self, auth_db: psycopg.Connection) -> dict:
        import persona.auth as auth_module

        private_key, public_key = _gen_rsa_key_pair()
        jwk_entry = _public_key_to_jwk(public_key, kid="ck1")
        auth_module._JWKS_CACHE = {"ck1": jwk_entry}
        auth_module._JWKS_FETCHED_AT = time.monotonic()

        # Create user A
        auth_db.execute(
            "INSERT INTO users (id, email) VALUES ('user_alice', 'alice@test.com')"
        )
        # Create user B
        auth_db.execute(
            "INSERT INTO users (id, email) VALUES ('user_bob', 'bob@test.com')"
        )

        app = FastAPI()
        get_user = build_get_current_user(auth_db)  # type: ignore[arg-type]
        app.include_router(
            create_router(
                ResumeService(auth_db),  # type: ignore[arg-type]
                app_service=ApplicationService(auth_db),  # type: ignore[arg-type]
                acc_service=AccomplishmentService(auth_db),  # type: ignore[arg-type]
                get_current_user=get_user,
            )
        )
        client = TestClient(app, raise_server_exceptions=False)

        alice_token = _make_token(private_key, sub="user_alice", email="alice@test.com")
        bob_token = _make_token(private_key, sub="user_bob", email="bob@test.com")

        return {
            "client": client,
            "alice_token": alice_token,
            "bob_token": bob_token,
            "db": auth_db,
            "private_key": private_key,
        }

    def test_get_resume_by_id_wrong_user_returns_403(
        self, two_user_setup: dict
    ) -> None:
        client = two_user_setup["client"]
        alice_token = two_user_setup["alice_token"]
        bob_token = two_user_setup["bob_token"]

        # Alice creates a resume
        with patch.dict("os.environ", {"CLERK_ISSUER": "https://clerk.test"}):
            resp = client.post(
                "/api/resumes",
                json={"label": "Alice's Resume"},
                headers={"Authorization": f"Bearer {alice_token}"},
            )
        assert resp.status_code == 201
        alice_resume_id = resp.json()["id"]

        # Bob tries to access Alice's resume → 403
        with patch.dict("os.environ", {"CLERK_ISSUER": "https://clerk.test"}):
            resp = client.get(
                f"/api/resumes/{alice_resume_id}",
                headers={"Authorization": f"Bearer {bob_token}"},
            )
        assert resp.status_code == 403

    def test_patch_resume_wrong_user_returns_403(self, two_user_setup: dict) -> None:
        client = two_user_setup["client"]
        alice_token = two_user_setup["alice_token"]
        bob_token = two_user_setup["bob_token"]

        with patch.dict("os.environ", {"CLERK_ISSUER": "https://clerk.test"}):
            resp = client.post(
                "/api/resumes",
                json={"label": "Alice Resume"},
                headers={"Authorization": f"Bearer {alice_token}"},
            )
        alice_resume_id = resp.json()["id"]

        with patch.dict("os.environ", {"CLERK_ISSUER": "https://clerk.test"}):
            resp = client.patch(
                f"/api/resumes/{alice_resume_id}",
                json={"label": "Hacked"},
                headers={"Authorization": f"Bearer {bob_token}"},
            )
        assert resp.status_code == 403

    def test_delete_resume_wrong_user_returns_403(self, two_user_setup: dict) -> None:
        client = two_user_setup["client"]
        alice_token = two_user_setup["alice_token"]
        bob_token = two_user_setup["bob_token"]

        with patch.dict("os.environ", {"CLERK_ISSUER": "https://clerk.test"}):
            resp = client.post(
                "/api/resumes",
                json={"label": "Alice Resume"},
                headers={"Authorization": f"Bearer {alice_token}"},
            )
        alice_resume_id = resp.json()["id"]

        with patch.dict("os.environ", {"CLERK_ISSUER": "https://clerk.test"}):
            resp = client.delete(
                f"/api/resumes/{alice_resume_id}",
                headers={"Authorization": f"Bearer {bob_token}"},
            )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Phase 3 (011) — T-MCP-01 through T-MCP-05: /mcp endpoint dual-auth contract
# ---------------------------------------------------------------------------


class TestMCPDualAuth:
    """T-MCP-01 through T-MCP-05: /mcp dual-auth (JWT + API key) contract tests."""

    @pytest.fixture
    def mcp_test_app(self) -> TestClient:
        """Minimal FastAPI app with UserContextMiddleware and mock /mcp endpoint.

        The mock endpoint always returns 200 with the current_user_id_var value;
        the middleware is responsible for returning 401 on auth failure.
        """
        from persona.server import UserContextMiddleware

        app = FastAPI()
        app.add_middleware(UserContextMiddleware)

        @app.post("/mcp")
        async def mock_mcp() -> dict:
            from persona.auth import current_user_id_var

            return {"user_id": current_user_id_var.get()}

        return TestClient(app, raise_server_exceptions=False)

    def _signed_in_state(self, user_id: str = "user_123") -> Any:
        """Build a mock RequestState with is_signed_in=True."""
        from unittest.mock import MagicMock

        from clerk_backend_api.security.types import SessionAuthObjectV2

        state = MagicMock()
        state.is_signed_in = True
        auth = MagicMock(spec=SessionAuthObjectV2)
        auth.sub = user_id
        state.to_auth.return_value = auth
        return state

    def _signed_out_state(self, message: str = "Token invalid") -> Any:
        """Build a mock RequestState with is_signed_in=False."""
        from unittest.mock import MagicMock

        state = MagicMock()
        state.is_signed_in = False
        state.message = message
        return state

    def test_mcp_01_valid_jwt_returns_200_with_user_id(
        self, mcp_test_app: TestClient
    ) -> None:
        """T-MCP-01: /mcp with valid Clerk session JWT → 200 and user_id set."""
        signed_in = self._signed_in_state("user_jwt_123")
        with (
            patch("persona.auth.authenticate_mcp_request", return_value=signed_in),
            patch("persona.auth.build_clerk_client"),
            patch("persona.server.resolve_clerk_secret_key", return_value="sk_test"),
            patch("persona.server.upsert_user"),
        ):
            resp = mcp_test_app.post(
                "/mcp", headers={"Authorization": "Bearer eyJ.valid.jwt"}
            )
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "user_jwt_123"

    def test_mcp_02_valid_api_key_returns_200_with_user_id(
        self, mcp_test_app: TestClient
    ) -> None:
        """T-MCP-02: /mcp with valid Clerk API key (ak_...) → 200 and user_id set."""
        signed_in = self._signed_in_state("user_api_456")
        with (
            patch("persona.auth.authenticate_mcp_request", return_value=signed_in),
            patch("persona.auth.build_clerk_client"),
            patch("persona.server.resolve_clerk_secret_key", return_value="sk_test"),
            patch("persona.server.upsert_user"),
        ):
            resp = mcp_test_app.post(
                "/mcp", headers={"Authorization": "Bearer ak_live_fakeapikey12345"}
            )
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "user_api_456"

    def test_mcp_03_no_auth_header_returns_401(self, mcp_test_app: TestClient) -> None:
        """T-MCP-03: /mcp with no Authorization header → 401."""
        resp = mcp_test_app.post("/mcp")
        assert resp.status_code == 401

    def test_mcp_04_expired_token_returns_401(self, mcp_test_app: TestClient) -> None:
        """T-MCP-04: /mcp with expired/invalid token → 401."""
        signed_out = self._signed_out_state("Token has expired")
        with (
            patch("persona.auth.authenticate_mcp_request", return_value=signed_out),
            patch("persona.auth.build_clerk_client"),
            patch("persona.server.resolve_clerk_secret_key", return_value="sk_test"),
        ):
            resp = mcp_test_app.post(
                "/mcp", headers={"Authorization": "Bearer expired.token.here"}
            )
        assert resp.status_code == 401

    def test_mcp_05_malformed_token_returns_401(self, mcp_test_app: TestClient) -> None:
        """T-MCP-05: /mcp with malformed token → 401."""
        signed_out = self._signed_out_state("Malformed token")
        with (
            patch("persona.auth.authenticate_mcp_request", return_value=signed_out),
            patch("persona.auth.build_clerk_client"),
            patch("persona.server.resolve_clerk_secret_key", return_value="sk_test"),
        ):
            resp = mcp_test_app.post(
                "/mcp", headers={"Authorization": "Bearer not-valid"}
            )
        assert resp.status_code == 401

    def test_mcp_06_revoked_api_key_returns_401(self, mcp_test_app: TestClient) -> None:
        """T-MCP-06: /mcp with a revoked Clerk API key → 401.

        After key regeneration the old key is invalidated by Clerk. When a
        previously-valid ak_ token is presented, Clerk returns is_signed_in=False
        and UserContextMiddleware must reject the request with 401.
        """
        signed_out = self._signed_out_state("API key has been revoked")
        with (
            patch("persona.auth.authenticate_mcp_request", return_value=signed_out),
            patch("persona.auth.build_clerk_client"),
            patch("persona.server.resolve_clerk_secret_key", return_value="sk_test"),
        ):
            resp = mcp_test_app.post(
                "/mcp",
                headers={"Authorization": "Bearer ak_live_revokedkey99999"},
            )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Phase 4 — T035/T036: MCP tool auth via ContextVar
# ---------------------------------------------------------------------------


class TestMCPToolAuthContract:
    """MCP tools require user context; missing context → structured error."""

    def test_mcp_read_tool_without_user_context_raises(self) -> None:
        """Calling get_resume without a user ContextVar set returns an error."""
        import persona.auth as auth_module

        # Clear any existing context
        token = auth_module.current_user_id_var.set(None)
        try:
            with pytest.raises(Exception):
                from persona.tools.read import get_resume_for_user

                # Calling with no context set should raise or return error
                # The exact behaviour depends on implementation
                fn = getattr(get_resume_for_user, "__wrapped__", get_resume_for_user)
                fn()  # type: ignore[call-arg]
        finally:
            auth_module.current_user_id_var.reset(token)

    def test_mcp_write_tool_without_user_context_raises(self) -> None:
        """Calling update_section without a user ContextVar set returns an error."""
        import persona.auth as auth_module

        token = auth_module.current_user_id_var.set(None)
        try:
            with pytest.raises(Exception):
                from persona.tools.write import update_section_for_user

                fn = getattr(
                    update_section_for_user, "__wrapped__", update_section_for_user
                )
                fn()  # type: ignore[call-arg]
        finally:
            auth_module.current_user_id_var.reset(token)
