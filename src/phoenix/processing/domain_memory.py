"""Persistent learning memory for per-domain strategy and selector feedback.

``DomainMemory`` records what works for each registered domain (HTTP vs browser,
which selectors match, average confidence) and loads that memory on subsequent
engine restarts. When no storage backend is configured, it falls back to a local
JSON file under the configured data directory.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    from phoenix.infrastructure.storage import StorageBackend
    from phoenix.models.output import UnifiedOutput


@dataclass
class DomainMemoryEntry:
    """Aggregated learning memory for a single domain."""

    domain: str
    strategy_memory: dict[str, Any] = field(default_factory=dict)
    selector_memory: dict[str, Any] = field(default_factory=dict)
    aggregates: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


class DomainMemory:
    """Persistent feedback store keyed by registered domain."""

    _DEFAULT_DATA_DIR: str = ".phoenix"
    _MEMORY_FILENAME: str = "domain_memory.json"

    def __init__(
        self,
        storage: StorageBackend | None = None,
        data_dir: Path | str | None = None,
    ) -> None:
        """Initialize the domain memory store.

        Args:
            storage: Optional persistent storage backend. When provided, memory
                is read from and written to the backend.
            data_dir: Optional filesystem directory for the JSON fallback file.
                Ignored when ``storage`` is provided.
        """
        self._storage = storage
        self._data_dir = Path(data_dir or self._DEFAULT_DATA_DIR)
        self._cache: dict[str, DomainMemoryEntry] = {}

    def get(self, domain: str) -> DomainMemoryEntry:
        """Return the memory entry for ``domain``.

        The result is cached in memory after the first load.
        """
        if domain in self._cache:
            return self._cache[domain]

        entry = self._load(domain)
        self._cache[domain] = entry
        return entry

    def _load(self, domain: str) -> DomainMemoryEntry:
        """Load memory for ``domain`` from storage or the local JSON file."""
        data: dict[str, Any] | None = None
        if self._storage is not None:
            data = self._storage.get_domain_memory(domain)
        else:
            data = self._load_json().get(domain)

        if data is None:
            return DomainMemoryEntry(domain=domain)

        return DomainMemoryEntry(
            domain=domain,
            strategy_memory=dict(data.get("strategy_memory", {})),
            selector_memory=dict(data.get("selector_memory", {})),
            aggregates=dict(data.get("aggregates", {})),
        )

    def _persist(self, entry: DomainMemoryEntry) -> None:
        """Persist ``entry`` to storage or the local JSON file."""
        data = entry.as_dict()
        if self._storage is not None:
            self._storage.save_domain_memory(entry.domain, data)
        else:
            all_data = self._load_json()
            all_data[entry.domain] = data
            self._save_json(all_data)

    def _load_json(self) -> dict[str, Any]:
        """Load the entire JSON fallback store."""
        path = self._data_dir / self._MEMORY_FILENAME
        if not path.exists():
            return {}
        try:
            return dict(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return {}

    def _save_json(self, data: dict[str, Any]) -> None:
        """Save the entire JSON fallback store."""
        self._data_dir.mkdir(parents=True, exist_ok=True)
        path = self._data_dir / self._MEMORY_FILENAME
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    @staticmethod
    def _domain(url: str) -> str:
        """Return the registered domain for ``url`` without leading ``www.``."""
        netloc = urlparse(url).netloc.lower()
        if "." in netloc and netloc.startswith("www."):
            return netloc[4:]
        return netloc

    @staticmethod
    def _now_iso() -> str:
        """Return the current UTC timestamp as an ISO string."""
        return datetime.now(UTC).isoformat()

    async def record_success(
        self,
        url: str,
        strategy: str,
        extracted: dict[str, Any],
        output: UnifiedOutput | None,
    ) -> None:
        """Record a successful scrape for ``url``'s domain.

        Args:
            url: URL that was scraped.
            strategy: Strategy that succeeded (``http`` or ``browser``).
            extracted: Raw extracted fields from the adapter/extractor.
            output: Normalized output, if available.
        """
        domain = self._domain(url)
        entry = self.get(domain)

        self._update_strategy_memory(entry, strategy, success=True)
        self._update_selector_memory(entry, extracted, output)
        self._update_aggregates(entry, success=True, output=output)

        self._persist(entry)

    async def record_failure(
        self,
        url: str,
        strategy: str,
        error: dict[str, Any] | None,
    ) -> None:
        """Record a failed scrape for ``url``'s domain.

        Args:
            url: URL that failed.
            strategy: Strategy that was in use when the failure occurred.
            error: Structured error dictionary.
        """
        domain = self._domain(url)
        entry = self.get(domain)

        self._update_strategy_memory(entry, strategy, success=False)
        self._update_aggregates(entry, success=False, error=error)

        self._persist(entry)

    def _update_strategy_memory(
        self,
        entry: DomainMemoryEntry,
        strategy: str,
        *,
        success: bool,
    ) -> None:
        """Update the success flag for ``strategy`` on ``entry``."""
        if strategy not in {"http", "browser"}:
            return
        now = self._now_iso()
        strategy_mem = entry.strategy_memory.setdefault(strategy, {})
        if success:
            strategy_mem["success"] = True
            strategy_mem["last_success"] = now
        else:
            strategy_mem["last_failure"] = now

    def _update_selector_memory(
        self,
        entry: DomainMemoryEntry,
        extracted: dict[str, Any],
        output: UnifiedOutput | None,
    ) -> None:
        """Record selector outcomes discovered in ``extracted``."""
        confidences: dict[str, float] = output.field_confidences if output is not None else {}
        now = self._now_iso()

        for field_name, value in extracted.items():
            if field_name in {"selectors_used", "platform", "url", "content_type"}:
                continue
            if not isinstance(value, dict):
                continue
            selector = value.get("selector_used")
            if not selector:
                continue
            matched = bool(value.get("matched", value.get("value")))
            confidence = float(
                value.get("confidence", confidences.get(field_name, 1.0 if matched else 0.0)),
            )
            self._record_selector(
                entry,
                field_name,
                selector,
                matched=matched,
                confidence=confidence,
                timestamp=now,
            )

        # Also credit top-level selectors_used when no per-field details exist.
        for selector in extracted.get("selectors_used", []):
            self._record_selector(
                entry,
                "_page",
                selector,
                matched=True,
                confidence=confidences.get("_page", 1.0),
                timestamp=now,
            )

    def _record_selector(  # noqa: PLR0913
        self,
        entry: DomainMemoryEntry,
        field_name: str,
        selector: str,
        *,
        matched: bool,
        confidence: float,
        timestamp: str,
    ) -> None:
        """Update the running statistics for a single selector."""
        field_mem = entry.selector_memory.setdefault(field_name, {"selectors": {}})
        selectors = field_mem["selectors"]
        record = selectors.setdefault(
            selector,
            {"successes": 0, "attempts": 0, "match_rate": 0.0, "last_seen": None},
        )
        record["attempts"] += 1
        if matched:
            record["successes"] += 1
        record["match_rate"] = round(record["successes"] / record["attempts"], 3)
        record["last_seen"] = timestamp
        record["confidence"] = round(confidence, 3)

        # Promote the best selector for this field.
        best = max(
            selectors.items(),
            key=lambda item: (item[1]["match_rate"], item[1]["attempts"]),
        )
        field_mem["best_selector"] = best[0]

    def _update_aggregates(
        self,
        entry: DomainMemoryEntry,
        *,
        success: bool,
        output: UnifiedOutput | None = None,
        error: dict[str, Any] | None = None,
    ) -> None:
        """Update aggregate counters for ``entry``."""
        now = self._now_iso()
        aggregates = entry.aggregates
        aggregates["attempts"] = aggregates.get("attempts", 0) + 1
        if success:
            aggregates["successes"] = aggregates.get("successes", 0) + 1
            aggregates["last_success"] = now
            if output is not None:
                self._update_average(aggregates, "average_confidence", output.confidence)
        else:
            aggregates["failures"] = aggregates.get("failures", 0) + 1
            aggregates["last_failure"] = now
            if error is not None:
                aggregates["last_error_code"] = error.get("code")

        attempts = aggregates["attempts"]
        successes = aggregates.get("successes", 0)
        aggregates["success_rate"] = round(successes / attempts, 3) if attempts else 0.0

    @staticmethod
    def _update_average(aggregates: dict[str, Any], key: str, value: float | None) -> None:
        """Maintain a running average for ``key``."""
        if value is None:
            return
        count_key = f"{key}_count"
        current = aggregates.get(key, 0.0)
        count = aggregates.get(count_key, 0) + 1
        aggregates[key] = round((current * (count - 1) + value) / count, 4)
        aggregates[count_key] = count


__all__ = ["DomainMemory", "DomainMemoryEntry"]
