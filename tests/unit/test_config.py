"""Unit tests for persona.config module."""

import logging
from pathlib import Path

import pytest


class TestResolveDataDir:
    """Tests for data directory resolution."""

    def test_default_path_when_env_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PERSONA_DATA_DIR", raising=False)
        from backend.config import resolve_data_dir

        result = resolve_data_dir()
        assert result == Path.home() / ".persona"

    def test_env_var_overrides_default(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("PERSONA_DATA_DIR", str(tmp_path / "custom"))
        from backend.config import resolve_data_dir

        result = resolve_data_dir()
        assert result == tmp_path / "custom"

    def test_relative_path_resolved_against_cwd(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("PERSONA_DATA_DIR", "relative/data")
        monkeypatch.chdir(tmp_path)
        from backend.config import resolve_data_dir

        result = resolve_data_dir()
        assert result == tmp_path / "relative" / "data"
        assert result.is_absolute()

    def test_resolved_path_is_logged(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        monkeypatch.setenv("PERSONA_DATA_DIR", "relative/data")
        monkeypatch.chdir(tmp_path)
        from backend.config import resolve_data_dir

        with caplog.at_level(logging.INFO):
            result = resolve_data_dir()

        assert str(result) in caplog.text


class TestConfigureLogging:
    """Tests for logging configuration."""

    def test_default_log_level_is_info(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        from backend.config import configure_logging

        logger = configure_logging()
        assert logger.level == logging.INFO

    def test_log_level_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        from backend.config import configure_logging

        logger = configure_logging()
        assert logger.level == logging.DEBUG
