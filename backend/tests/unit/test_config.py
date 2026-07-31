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


class TestBackupConfig:
    """Backup settings are optional — unset means the feature is off."""

    def test_environment_defaults_to_local(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PKTX_ENV", raising=False)
        from pktx.config import resolve_environment

        assert resolve_environment() == "local"

    def test_environment_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PKTX_ENV", " prod ")
        from pktx.config import resolve_environment

        assert resolve_environment() == "prod"

    def test_bucket_and_token_default_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PKTX_BACKUP_BUCKET", raising=False)
        monkeypatch.delenv("PKTX_BACKUP_TOKEN", raising=False)
        from pktx.config import resolve_backup_bucket, resolve_backup_token

        assert resolve_backup_bucket() == ""
        assert resolve_backup_token() == ""

    def test_bucket_and_token_are_stripped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("PKTX_BACKUP_BUCKET", " pktx-backups-dev ")
        monkeypatch.setenv("PKTX_BACKUP_TOKEN", " s3cret ")
        from pktx.config import resolve_backup_bucket, resolve_backup_token

        assert resolve_backup_bucket() == "pktx-backups-dev"
        assert resolve_backup_token() == "s3cret"
