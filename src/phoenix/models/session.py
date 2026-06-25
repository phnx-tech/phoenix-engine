"""Session model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


@dataclass
class Session:
    """Authenticated session for a platform."""

    platform: str
    cookies: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime | None = None
    is_valid: bool = True


__all__ = ["Session"]
