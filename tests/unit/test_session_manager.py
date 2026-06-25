"""Unit tests for the authenticated session manager."""

from __future__ import annotations

import pytest

from phoenix.infrastructure.session_manager import SessionManager
from phoenix.infrastructure.storage import SQLiteStorageBackend


@pytest.fixture
def manager() -> SessionManager:
    """Return a session manager backed by in-memory storage."""
    storage = SQLiteStorageBackend(path=":memory:")
    try:
        yield SessionManager(storage)
    finally:
        storage.close()


def test_save_and_get_session(manager: SessionManager) -> None:
    """Sessions can be saved and retrieved by platform."""
    manager.save_session("x_twitter", [{"name": "auth", "value": "token"}])

    session = manager.get_session("x_twitter")

    assert session is not None
    assert session.platform == "x_twitter"
    assert session.cookies[0]["value"] == "token"


def test_get_cookies_returns_empty_for_invalid(manager: SessionManager) -> None:
    """No cookies are returned when the session is invalid or missing."""
    assert manager.get_cookies("x_twitter") == []

    manager.save_session("x_twitter", [{"name": "auth", "value": "token"}], is_valid=False)
    assert manager.get_cookies("x_twitter") == []


def test_invalidate_session(manager: SessionManager) -> None:
    """Invalidating a session marks it as invalid in storage."""
    manager.save_session("x_twitter", [{"name": "auth", "value": "token"}])

    assert manager.is_session_valid("x_twitter") is True
    assert manager.invalidate_session("x_twitter") is True
    assert manager.is_session_valid("x_twitter") is False
    assert manager.invalidate_session("unknown") is False


def test_list_sessions(manager: SessionManager) -> None:
    """All persisted sessions can be listed."""
    manager.save_session("x_twitter", [])
    manager.save_session("instagram", [])

    sessions = manager.list_sessions()

    assert len(sessions) == 2
    assert {s.platform for s in sessions} == {"instagram", "x_twitter"}
