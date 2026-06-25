"""Structured audit logging for Phoenix Engine.

``AuditLogger`` emits JSON-formatted log records for scraping actions and
persists change-detection alerts through the configured storage backend when
available.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from phoenix.infrastructure.storage import StorageBackend
    from phoenix.models.output import ChangeAlert


class AuditLogger:
    """Structured audit logger backed by Python logging and optional storage."""

    def __init__(
        self,
        storage: StorageBackend | None = None,
        logger_name: str = "phoenix.audit",
    ) -> None:
        """Initialize the audit logger.

        Args:
            storage: Optional storage backend used to persist change alerts.
            logger_name: Logger name used for JSON log emission.
        """
        self._logger = logging.getLogger(logger_name)
        self._storage = storage

    def log_event(self, event_type: str, **kwargs: object) -> None:
        """Emit a structured JSON audit event.

        Args:
            event_type: Category for the event.
            **kwargs: Additional event fields.
        """
        payload = {
            "event_type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            **kwargs,
        }
        self._logger.info(json.dumps(payload, default=str))

    def log_alert(self, alert: ChangeAlert) -> str | None:
        """Persist and log a change-detection alert.

        Args:
            alert: Alert model to record.

        Returns:
            Storage identifier when persisted, otherwise ``None``.
        """
        payload = alert.model_dump(mode="json")
        self._logger.info(json.dumps(payload, default=str))

        if self._storage is None:
            return None
        return self._storage.save_alert(payload)


__all__ = ["AuditLogger"]
