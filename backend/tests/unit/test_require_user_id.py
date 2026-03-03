"""Unit tests for require_user_id() helper."""

import pytest

from persona.auth import current_user_id_var, require_user_id


class TestRequireUserId:
    """Verify require_user_id enforces an authenticated user context."""

    def test_raises_when_no_user_context_set(self) -> None:
        """Without a user context, require_user_id must raise RuntimeError."""
        token = current_user_id_var.set(None)
        try:
            with pytest.raises(RuntimeError, match="No user context set"):
                require_user_id()
        finally:
            current_user_id_var.reset(token)

    def test_returns_user_id_when_set(self) -> None:
        """With a valid user context, require_user_id returns the user ID."""
        token = current_user_id_var.set("user_alice")
        try:
            assert require_user_id() == "user_alice"
        finally:
            current_user_id_var.reset(token)
