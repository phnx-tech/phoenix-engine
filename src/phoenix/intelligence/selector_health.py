"""Selector health monitoring for Phoenix Engine.

Tracks how often CSS selectors match over time and flags selectors whose
success rate drops below a threshold so they can be repaired or retired.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any


@dataclass
class SelectorHealthRecord:
    """Health statistics for a single selector."""

    platform: str
    field: str
    selector: str
    successes: int = 0
    failures: int = 0
    total: int = 0
    match_rate: float = 0.0
    last_seen: float | None = None

    def record(self, *, matched: bool, timestamp: float) -> None:
        """Update the record with a single match result."""
        self.total += 1
        if matched:
            self.successes += 1
        else:
            self.failures += 1
        self.match_rate = round(self.successes / self.total, 3)
        self.last_seen = timestamp

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict representation."""
        return {
            "platform": self.platform,
            "field": self.field,
            "selector": self.selector,
            "successes": self.successes,
            "failures": self.failures,
            "total": self.total,
            "match_rate": self.match_rate,
            "last_seen": self.last_seen,
        }


class SelectorHealthMonitor:
    """Monitor selector match rates and detect degradation."""

    _DEFAULT_MIN_ATTEMPTS: int = 5

    def __init__(self) -> None:
        """Initialize an empty selector health monitor."""
        self._records: dict[tuple[str, str, str], SelectorHealthRecord] = {}

    def record(
        self,
        platform: str,
        field_name: str,
        selector: str,
        *,
        matched: bool,
        timestamp: float | None = None,
    ) -> None:
        """Record a selector match result.

        Args:
            platform: Platform the selector belongs to.
            field_name: Field name the selector extracts.
            selector: CSS selector string.
            matched: Whether the selector matched at least one element.
            timestamp: Optional event timestamp. Defaults to the current time.
        """
        key = (platform, field_name, selector)
        record = self._records.get(key)
        if record is None:
            record = SelectorHealthRecord(
                platform=platform,
                field=field_name,
                selector=selector,
            )
            self._records[key] = record
        record.record(matched=matched, timestamp=timestamp or time())

    def get_record(
        self,
        platform: str,
        field_name: str,
        selector: str,
    ) -> SelectorHealthRecord | None:
        """Return the health record for a selector, if any."""
        return self._records.get((platform, field_name, selector))

    def degraded_selectors(
        self,
        threshold: float = 0.5,
        *,
        min_attempts: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return selectors whose match rate is below ``threshold``.

        Args:
            threshold: Minimum acceptable match rate (0.0 - 1.0).
            min_attempts: Minimum number of attempts before a selector is
                considered degraded. Defaults to ``_DEFAULT_MIN_ATTEMPTS``.

        Returns:
            List of degraded selector records as dictionaries.
        """
        min_attempts = min_attempts or self._DEFAULT_MIN_ATTEMPTS
        return [
            record.to_dict()
            for record in self._records.values()
            if record.total >= min_attempts and record.match_rate < threshold
        ]

    def health_summary(self) -> dict[str, Any]:
        """Return an aggregate summary of all tracked selectors."""
        records = list(self._records.values())
        if not records:
            return {
                "total_selectors": 0,
                "average_match_rate": 0.0,
                "degraded_count": 0,
            }
        average_rate = sum(record.match_rate for record in records) / len(records)
        degraded = self.degraded_selectors()
        return {
            "total_selectors": len(records),
            "average_match_rate": round(average_rate, 3),
            "degraded_count": len(degraded),
        }


__all__ = ["SelectorHealthMonitor", "SelectorHealthRecord"]
