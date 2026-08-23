"""Unit tests for pktx.config module."""

import logging

import pytest


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_default_log_level_is_info(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        from pktx.config import configure_logging

        logger = configure_logging()
        assert logger.level == logging.INFO

    def test_log_level_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        from pktx.config import configure_logging

        logger = configure_logging()
        assert logger.level == logging.DEBUG


class TestExtraClientRedirectUris:
    """PKTX_EXTRA_CLIENT_REDIRECT_URIS: opt-in allowlist for hosted MCP clients."""

    def test_unset_returns_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PKTX_EXTRA_CLIENT_REDIRECT_URIS", raising=False)
        from pktx.config import resolve_extra_client_redirect_uris

        assert resolve_extra_client_redirect_uris() == []

    def test_blank_returns_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PKTX_EXTRA_CLIENT_REDIRECT_URIS", "   ")
        from pktx.config import resolve_extra_client_redirect_uris

        assert resolve_extra_client_redirect_uris() == []

    def test_comma_separated_patterns_are_split_and_stripped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(
            "PKTX_EXTRA_CLIENT_REDIRECT_URIS",
            "https://client.example.com/callback, https://*.other.example/cb ,",
        )
        from pktx.config import resolve_extra_client_redirect_uris

        assert resolve_extra_client_redirect_uris() == [
            "https://client.example.com/callback",
            "https://*.other.example/cb",
        ]
