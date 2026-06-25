"""Tests for selector health monitoring."""

from __future__ import annotations

import pytest

from phoenix.intelligence.selector_health import SelectorHealthMonitor


@pytest.fixture
def monitor() -> SelectorHealthMonitor:
    return SelectorHealthMonitor()


def test_record_success_and_failure(monitor: SelectorHealthMonitor) -> None:
    monitor.record(
        "example",
        "title",
        "h1",
        matched=True,
        timestamp=1.0,
    )
    monitor.record(
        "example",
        "title",
        "h1",
        matched=False,
        timestamp=2.0,
    )

    record = monitor.get_record("example", "title", "h1")
    assert record is not None
    assert record.total == 2
    assert record.successes == 1
    assert record.failures == 1
    assert record.match_rate == 0.5


def test_degraded_selectors_ignore_low_attempts(monitor: SelectorHealthMonitor) -> None:
    for _ in range(4):
        monitor.record("example", "title", "h1", matched=False)
    degraded = monitor.degraded_selectors(threshold=0.5)
    assert degraded == []


def test_degraded_selectors_flags_below_threshold(monitor: SelectorHealthMonitor) -> None:
    for _ in range(5):
        monitor.record("example", "title", "h1", matched=False)
    degraded = monitor.degraded_selectors(threshold=0.5)
    assert len(degraded) == 1
    assert degraded[0]["selector"] == "h1"
    assert degraded[0]["match_rate"] == 0.0


def test_degraded_selectors_respects_custom_min_attempts(
    monitor: SelectorHealthMonitor,
) -> None:
    for _ in range(2):
        monitor.record("example", "title", "h1", matched=False)
    degraded = monitor.degraded_selectors(threshold=0.5, min_attempts=1)
    assert len(degraded) == 1


def test_health_summary(monitor: SelectorHealthMonitor) -> None:
    monitor.record("example", "title", "h1", matched=True)
    monitor.record("example", "price", ".price", matched=False)
    summary = monitor.health_summary()
    assert summary["total_selectors"] == 2
    assert summary["average_match_rate"] == 0.5
    assert summary["degraded_count"] == 0
