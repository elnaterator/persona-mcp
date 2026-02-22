"""Unit tests for persona.config module."""

import logging

import pytest


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_default_log_level_is_info(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        from persona.config import configure_logging

        logger = configure_logging()
        assert logger.level == logging.INFO

    def test_log_level_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        from persona.config import configure_logging

        logger = configure_logging()
        assert logger.level == logging.DEBUG
