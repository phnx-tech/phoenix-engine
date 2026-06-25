"""Authenticated session manager for Phoenix Engine.

Manages platform-specific browser sessions, including cookie persistence and
validation. Sessions are stored via a :class:`~phoenix.infrastructure.storage.StorageBackend`
so that authenticated state survives process restarts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from phoenix.models.session import Session

if TYPE_CHECKING:
    from phoenix.infrastructure.storage import StorageBackend


class SessionManager:
    """Manages authenticated sessions per platform.

    The manager loads and saves sessions through a storage backend. Callers can
    register cookies retrieved from a browser login flow and later retrieve them
    for reuse in authenticated collection.
    """

    def __init__(self, storage: StorageBackend) -> None:
        """Initialize the session manager.

        Args:
            storage: Storage backend used to persist sessions.
        """
        self._storage = storage

    def get_session(self, platform: str) -> Session | None:
        """Return the active session for ``platform`` if one exists."""
        return self._storage.get_session(platform)

    def save_session(
        self,
        platform: str,
        cookies: list[dict[str, Any]],
        *,
        is_valid: bool = True,
    ) -> str:
        """Persist a session for ``platform``.

        Args:
            platform: Platform identifier (e.g. ``x_twitter``).
            cookies: List of cookie dictionaries.
            is_valid: Whether the session is currently valid.

        Returns:
            Storage identifier for the persisted session.
        """
        session = Session(
            platform=platform,
            cookies=list(cookies),
            is_valid=is_valid,
            updated_at=datetime.now(UTC),
        )
        return self._storage.save_session(session)

    def invalidate_session(self, platform: str) -> bool:
        """Mark the session for ``platform`` as invalid.

        Returns:
            ``True`` when a session existed and was invalidated.
        """
        session = self._storage.get_session(platform)
        if session is None:
            return False
        session.is_valid = False
        session.updated_at = datetime.now(UTC)
        self._storage.save_session(session)
        return True

    def list_sessions(self) -> list[Session]:
        """Return all persisted sessions."""
        return self._storage.list_sessions()

    def is_session_valid(self, platform: str) -> bool:
        """Return ``True`` when a valid session exists for ``platform``."""
        session = self.get_session(platform)
        return session is not None and session.is_valid

    def get_cookies(self, platform: str) -> list[dict[str, Any]]:
        """Return cookies for ``platform`` when a valid session exists."""
        session = self.get_session(platform)
        if session is None or not session.is_valid:
            return []
        return list(session.cookies)
