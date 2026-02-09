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
        from persona.config import resolve_data_dir

        result = resolve_data_dir()
        assert result == Path.home() / ".persona"

    def test_env_var_overrides_default(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("PERSONA_DATA_DIR", str(tmp_path / "custom"))
        from persona.config import resolve_data_dir

        result = resolve_data_dir()
        assert result == tmp_path / "custom"

    def test_relative_path_resolved_against_cwd(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("PERSONA_DATA_DIR", "relative/data")
        monkeypatch.chdir(tmp_path)
        from persona.config import resolve_data_dir

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
        from persona.config import resolve_data_dir

        with caplog.at_level(logging.INFO):
            result = resolve_data_dir()

        assert str(result) in caplog.text


class TestEnsureDataDir:
    """Tests for directory creation on startup."""

    def test_creates_jobs_resume_structure(self, tmp_path: Path) -> None:
        from persona.config import ensure_data_dir

        ensure_data_dir(tmp_path)
        assert (tmp_path / "jobs" / "resume").is_dir()

    def test_creates_parent_if_missing(self, tmp_path: Path) -> None:
        from persona.config import ensure_data_dir

        data_dir = tmp_path / "nonexistent" / "deep" / "path"
        ensure_data_dir(data_dir)
        assert (data_dir / "jobs" / "resume").is_dir()

    def test_idempotent_on_existing_structure(self, tmp_data_dir: Path) -> None:
        from persona.config import ensure_data_dir

        # Should not raise when structure already exists
        ensure_data_dir(tmp_data_dir)
        assert (tmp_data_dir / "jobs" / "resume").is_dir()

    def test_error_on_uncreatable_path(self, tmp_path: Path) -> None:
        from persona.config import ensure_data_dir

        # Create a file where a directory is expected
        blocker = tmp_path / "blocker"
        blocker.write_text("I am a file")
        data_dir = blocker / "nested"

        with pytest.raises(OSError):
            ensure_data_dir(data_dir)


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
