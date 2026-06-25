"""Unit tests for the structured audit logger."""

from __future__ import annotations

import json
import logging

import pytest

from phoenix.infrastructure.audit_logger import AuditLogger
from phoenix.infrastructure.storage import SQLiteStorageBackend
from phoenix.models.output import ChangeAlert


@pytest.fixture
def storage() -> SQLiteStorageBackend:
    """Return an in-memory SQLite storage backend."""
    backend = SQLiteStorageBackend(path=":memory:")
    try:
        yield backend
    finally:
        backend.close()


@pytest.fixture
def caplog_setup(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Enable INFO logging for phoenix.audit."""
    caplog.set_level(logging.INFO, logger="phoenix.audit")
    return caplog


def test_log_event_emits_json(caplog_setup: pytest.LogCaptureFixture) -> None:
    """log_event writes a JSON record with event type and timestamp."""
    logger = AuditLogger()

    logger.log_event("scrape_attempt", url="https://example.com", strategy="http")

    assert len(caplog_setup.records) == 1
    payload = json.loads(caplog_setup.records[0].message)
    assert payload["event_type"] == "scrape_attempt"
    assert payload["url"] == "https://example.com"
    assert "timestamp" in payload


def test_log_alert_without_storage(caplog_setup: pytest.LogCaptureFixture) -> None:
    """log_alert emits JSON and returns None when storage is absent."""
    logger = AuditLogger()
    alert = ChangeAlert(
        alert_type="structural_change",
        severity="warning",
        url="https://example.com",
        platform="generic",
    )

    result = logger.log_alert(alert)

    assert result is None
    payload = json.loads(caplog_setup.records[0].message)
    assert payload["alert_type"] == "structural_change"
    assert payload["severity"] == "warning"


def test_log_alert_persists_to_storage(
    storage: SQLiteStorageBackend,
    caplog_setup: pytest.LogCaptureFixture,
) -> None:
    """log_alert persists the alert to storage when a backend is provided."""
    logger = AuditLogger(storage=storage)
    alert = ChangeAlert(
        alert_type="selector_degradation",
        severity="warning",
        url="https://example.com",
        platform="generic",
        details={"field": "title"},
    )

    result = logger.log_alert(alert)

    assert result is not None
    assert isinstance(result, str)
    payload = json.loads(caplog_setup.records[0].message)
    assert payload["details"] == {"field": "title"}
