"""Contract tests for authentication and authorisation on all API routes.

Phase 3 tests (T009): 401 on missing token, 200 on valid mock JWT.
Phase 4 tests (T016, T035, T036): 403 on cross-user access.
Plan 016 (T15-T19): MCP OAuth2 resource server contract tests.
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
# Plan 016 — T15-T19: MCP OAuth2 resource server contract tests
# ---------------------------------------------------------------------------

_TEST_PUBLIC_URL = "https://persona.test"
_TEST_ISSUER = "https://clerk.test"
_TEST_RESOURCE = f"{_TEST_PUBLIC_URL}/mcp"


def _build_mcp_oauth_app(private_key: Any) -> Any:
    """Build a FastMCP ASGI app with JWT auth wired for testing."""
    from fastmcp import FastMCP
    from fastmcp.server.auth import RemoteAuthProvider
    from fastmcp.server.auth.providers.jwt import JWTVerifier

    pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    # Mirror production build_mcp_auth: audience is NOT validated because Clerk
    # DCR mints tokens with aud=client_id. Signature + issuer stay strict.
    verifier = JWTVerifier(
        public_key=pem,
        issuer=_TEST_ISSUER,
        audience=None,
        base_url=_TEST_PUBLIC_URL,
    )
    provider = RemoteAuthProvider(
        token_verifier=verifier,
        authorization_servers=[_TEST_ISSUER],  # type: ignore[arg-type]
        base_url=_TEST_PUBLIC_URL,
        resource_name="Persona",
    )
    m = FastMCP("persona", auth=provider)

    @m.tool()
    def ping() -> str:
        return "pong"

    return m.http_app(path="/mcp", stateless_http=True)


def _make_mcp_token(
    private_key: Any,
    kid: str = "ck1",
    sub: str = "user_alice",
    issuer: str = _TEST_ISSUER,
    audience: str = _TEST_RESOURCE,
    exp_offset: int = 3600,
) -> str:
    now = int(time.time())
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    claims: dict[str, Any] = {
        "sub": sub,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + exp_offset,
    }
    return jwt.encode(claims, pem, algorithm="RS256", headers={"kid": kid})


@pytest.fixture(scope="module")
def mcp_oauth_key_pair() -> tuple[Any, Any]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


class TestMCPOAuth2ProtectedResourceMetadata:
    """T15: /.well-known/oauth-protected-resource/mcp returns RFC 9728 metadata."""

    def test_metadata_route_returns_200(self, mcp_oauth_key_pair: tuple) -> None:
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/.well-known/oauth-protected-resource/mcp")
        assert resp.status_code == 200

    def test_metadata_body_has_resource(self, mcp_oauth_key_pair: tuple) -> None:
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/.well-known/oauth-protected-resource/mcp")
        body = resp.json()
        assert "resource" in body

    def test_metadata_body_has_authorization_servers(
        self, mcp_oauth_key_pair: tuple
    ) -> None:
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/.well-known/oauth-protected-resource/mcp")
        body = resp.json()
        assert "authorization_servers" in body
        # FastMCP may normalize URLs with a trailing slash
        servers = [s.rstrip("/") for s in body["authorization_servers"]]
        assert _TEST_ISSUER.rstrip("/") in servers


class TestMCPOAuth2Unauthenticated:
    """T16: Unauthenticated POST /mcp → 401 with WWW-Authenticate header."""

    def test_unauth_post_returns_401(self, mcp_oauth_key_pair: tuple) -> None:
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        )
        assert resp.status_code == 401

    def test_unauth_post_has_www_authenticate_header(
        self, mcp_oauth_key_pair: tuple
    ) -> None:
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        )
        assert "www-authenticate" in {k.lower(): v for k, v in resp.headers.items()}

    def test_www_authenticate_references_metadata_url(
        self, mcp_oauth_key_pair: tuple
    ) -> None:
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            "/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        )
        www_auth = resp.headers.get("www-authenticate", "")
        assert "/.well-known/oauth-protected-resource/mcp" in www_auth


class TestMCPOAuth2TokenValidation:
    """T17: valid token ok; foreign aud accepted (DCR); expired → 401."""

    def test_valid_token_allows_request(self, mcp_oauth_key_pair: tuple) -> None:
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        token = _make_mcp_token(private_key)
        with TestClient(app, raise_server_exceptions=False) as client:
            resp = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json, text/event-stream",
                },
            )
        # 200 or 202 means auth passed; 401/403 means auth failed
        assert resp.status_code not in (401, 403)

    def test_foreign_audience_is_accepted(self, mcp_oauth_key_pair: tuple) -> None:
        # Clerk DCR sets aud=client_id, so audience is intentionally not
        # validated. A token with a foreign aud but valid signature + issuer
        # must still authenticate.
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        with TestClient(app, raise_server_exceptions=False) as client:
            token = _make_mcp_token(
                private_key, audience="https://wrong.example.com/mcp"
            )
            resp = client.post(
                "/mcp",
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json, text/event-stream",
                },
            )
        assert resp.status_code not in (401, 403)

    def test_expired_token_returns_401(self, mcp_oauth_key_pair: tuple) -> None:
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        client = TestClient(app, raise_server_exceptions=False)
        token = _make_mcp_token(private_key, exp_offset=-3600)
        resp = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json, text/event-stream",
            },
        )
        assert resp.status_code == 401


class TestMCPWellKnownRouteOrdering:
    """T19: Well-known route not shadowed by SPA static catch-all."""

    def test_well_known_route_in_mcp_app_routes(
        self, mcp_oauth_key_pair: tuple
    ) -> None:
        """The /.well-known/... route is present in mcp_app.routes before any mount."""
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert any("/.well-known/oauth-protected-resource/mcp" in p for p in paths)

    def test_well_known_route_precedes_mcp_route(
        self, mcp_oauth_key_pair: tuple
    ) -> None:
        """Well-known route index < /mcp route index in mcp_app.routes."""
        private_key, _ = mcp_oauth_key_pair
        app = _build_mcp_oauth_app(private_key)
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        wk_idx = next(i for i, p in enumerate(paths) if "/.well-known" in p)
        mcp_idx = next(i for i, p in enumerate(paths) if p == "/mcp")
        assert wk_idx < mcp_idx
