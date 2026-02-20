"""Unit tests for persona.auth — JWKS caching and JWT validation."""

import time
from typing import Any
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jose import jwt

# ---------------------------------------------------------------------------
# Helpers: generate an RSA key pair and build a minimal JWKS entry
# ---------------------------------------------------------------------------


def _gen_rsa_key_pair() -> tuple[Any, Any]:
    """Return (private_key, public_key) for test use."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    return private_key, private_key.public_key()


def _public_key_to_jwk(public_key: Any, kid: str = "test-kid") -> dict[str, Any]:
    """Convert an RSA public key to a minimal JWK dict usable by python-jose."""
    from jose.backends import RSAKey

    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    rsa_key = RSAKey(pem, "RS256")  # pyright: ignore [reportOptionalCall]
    jwk_dict = rsa_key.public_key().to_dict()
    jwk_dict["kid"] = kid
    jwk_dict["kty"] = "RSA"
    jwk_dict["alg"] = "RS256"
    return jwk_dict


def _make_token(
    private_key: Any,
    kid: str = "test-kid",
    sub: str = "user_test_123",
    issuer: str = "https://clerk.test",
    exp_offset: int = 3600,
) -> str:
    """Create a signed RS256 JWT for testing."""
    now = int(time.time())
    claims = {
        "sub": sub,
        "iss": issuer,
        "iat": now,
        "exp": now + exp_offset,
        "email": "test@example.com",
    }
    headers = {"kid": kid}
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return jwt.encode(claims, pem, algorithm="RS256", headers=headers)


# ---------------------------------------------------------------------------
# Tests for JWKS cache helpers
# ---------------------------------------------------------------------------


class TestJWKSCache:
    """Tests for the in-memory JWKS cache behaviour."""

    def setup_method(self) -> None:
        """Reset the module-level cache state before each test."""
        import persona.auth as auth_module

        auth_module._JWKS_CACHE = {}
        auth_module._JWKS_FETCHED_AT = 0.0

    def test_cache_hit_returns_key_without_fetch(self) -> None:
        """A known kid within TTL is returned without an HTTP call."""
        import persona.auth as auth_module

        key_data = {"kid": "k1", "kty": "RSA"}
        auth_module._JWKS_CACHE = {"k1": key_data}
        auth_module._JWKS_FETCHED_AT = time.monotonic()  # fresh

        with patch("persona.auth._fetch_jwks") as mock_fetch:
            result = auth_module._get_jwks_key("k1")

        mock_fetch.assert_not_called()
        assert result == key_data

    def test_cache_miss_triggers_fetch(self) -> None:
        """An unknown kid in a fresh cache triggers a JWKS refresh."""
        import persona.auth as auth_module

        auth_module._JWKS_CACHE = {}
        auth_module._JWKS_FETCHED_AT = time.monotonic()  # fresh but empty

        key_data = {"kid": "k2", "kty": "RSA"}

        def _fake_fetch() -> dict[str, Any]:
            auth_module._JWKS_CACHE = {"k2": key_data}
            auth_module._JWKS_FETCHED_AT = time.monotonic()
            return auth_module._JWKS_CACHE

        with patch("persona.auth._fetch_jwks", side_effect=_fake_fetch):
            result = auth_module._get_jwks_key("k2")

        assert result == key_data

    def test_expired_ttl_triggers_refresh(self) -> None:
        """An expired cache forces a fresh JWKS fetch even for a known kid."""
        import persona.auth as auth_module

        key_data = {"kid": "k3", "kty": "RSA"}
        auth_module._JWKS_CACHE = {"k3": key_data}
        auth_module._JWKS_FETCHED_AT = time.monotonic() - 7200.0  # 2h ago — expired

        refreshed = {"kid": "k3", "kty": "RSA", "refreshed": True}

        def _fake_fetch() -> dict[str, Any]:
            auth_module._JWKS_CACHE = {"k3": refreshed}
            auth_module._JWKS_FETCHED_AT = time.monotonic()
            return auth_module._JWKS_CACHE

        with patch("persona.auth._fetch_jwks", side_effect=_fake_fetch) as mock_fetch:
            result = auth_module._get_jwks_key("k3")

        mock_fetch.assert_called_once()
        assert result["refreshed"] is True

    def test_unknown_kid_after_refresh_raises_401(self) -> None:
        """If kid is still absent after a fresh JWKS fetch, a 401 is raised."""
        import persona.auth as auth_module

        auth_module._JWKS_CACHE = {}
        auth_module._JWKS_FETCHED_AT = 0.0

        def _fake_fetch() -> dict[str, Any]:
            auth_module._JWKS_CACHE = {}
            auth_module._JWKS_FETCHED_AT = time.monotonic()
            return auth_module._JWKS_CACHE

        with patch("persona.auth._fetch_jwks", side_effect=_fake_fetch):
            with pytest.raises(HTTPException) as exc_info:
                auth_module._get_jwks_key("unknown-kid")

        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Tests for verify_clerk_jwt
# ---------------------------------------------------------------------------


class TestVerifyClerkJwt:
    """Tests for the verify_clerk_jwt function."""

    def setup_method(self) -> None:
        import persona.auth as auth_module

        auth_module._JWKS_CACHE = {}
        auth_module._JWKS_FETCHED_AT = 0.0

    def _setup_valid_key(
        self, kid: str = "test-kid", issuer: str = "https://clerk.test"
    ) -> tuple[Any, str]:
        """Set up JWKS cache with a test key and return (private_key, issuer)."""
        import persona.auth as auth_module

        private_key, public_key = _gen_rsa_key_pair()
        jwk_entry = _public_key_to_jwk(public_key, kid=kid)
        auth_module._JWKS_CACHE = {kid: jwk_entry}
        auth_module._JWKS_FETCHED_AT = time.monotonic()
        return private_key, issuer

    def test_valid_token_returns_claims(self) -> None:
        """A valid JWT with matching issuer and sub returns claims dict."""
        private_key, issuer = self._setup_valid_key()
        token = _make_token(private_key, issuer=issuer)

        with patch.dict("os.environ", {"CLERK_ISSUER": issuer}):
            claims = __import__(
                "persona.auth", fromlist=["verify_clerk_jwt"]
            ).verify_clerk_jwt(token)

        assert claims["sub"] == "user_test_123"
        assert claims["email"] == "test@example.com"

    def test_expired_token_raises_401(self) -> None:
        """An expired JWT raises HTTP 401."""
        private_key, issuer = self._setup_valid_key()
        token = _make_token(private_key, issuer=issuer, exp_offset=-3600)

        with patch.dict("os.environ", {"CLERK_ISSUER": issuer}):
            with pytest.raises(HTTPException) as exc_info:
                __import__(
                    "persona.auth", fromlist=["verify_clerk_jwt"]
                ).verify_clerk_jwt(token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_wrong_issuer_raises_401(self) -> None:
        """A JWT signed with a different issuer fails validation."""
        private_key, _ = self._setup_valid_key()
        token = _make_token(private_key, issuer="https://evil.example.com")

        with patch.dict("os.environ", {"CLERK_ISSUER": "https://clerk.test"}):
            with pytest.raises(HTTPException) as exc_info:
                __import__(
                    "persona.auth", fromlist=["verify_clerk_jwt"]
                ).verify_clerk_jwt(token)

        assert exc_info.value.status_code == 401

    def test_missing_sub_raises_401(self) -> None:
        """A JWT without a 'sub' claim raises HTTP 401."""
        private_key, issuer = self._setup_valid_key()
        # Craft a token without sub
        now = int(time.time())
        claims_no_sub = {
            "iss": issuer,
            "iat": now,
            "exp": now + 3600,
        }
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        token = jwt.encode(
            claims_no_sub, pem, algorithm="RS256", headers={"kid": "test-kid"}
        )

        with patch.dict("os.environ", {"CLERK_ISSUER": issuer}):
            with pytest.raises(HTTPException) as exc_info:
                __import__(
                    "persona.auth", fromlist=["verify_clerk_jwt"]
                ).verify_clerk_jwt(token)

        assert exc_info.value.status_code == 401
        assert "sub" in exc_info.value.detail.lower()

    def test_malformed_token_raises_401(self) -> None:
        """A garbage string raises HTTP 401."""
        with patch.dict("os.environ", {"CLERK_ISSUER": "https://clerk.test"}):
            with pytest.raises(HTTPException) as exc_info:
                __import__(
                    "persona.auth", fromlist=["verify_clerk_jwt"]
                ).verify_clerk_jwt("not.a.jwt")

        assert exc_info.value.status_code == 401
