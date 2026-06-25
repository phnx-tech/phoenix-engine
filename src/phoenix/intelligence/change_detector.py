"""HTML structural drift and selector degradation detection.

``ChangeDetector`` maintains a per-URL baseline of structural fingerprints and
selector snapshots. On each successful scrape it compares the new page against
the baseline and returns a ``ChangeAlert`` when material drift is detected.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, Tag

from phoenix.models.output import ChangeAlert

if TYPE_CHECKING:
    from phoenix.infrastructure.storage import StorageBackend
    from phoenix.models.config import Config
    from phoenix.models.document import RawResponse
    from phoenix.models.output import UnifiedOutput


class ChangeDetector:
    """Detect structural changes and selector degradation between scrapes."""

    _DEFAULT_SIZE_THRESHOLD = 0.3
    _FIELD_CONFIDENCE_THRESHOLD = 0.5
    _CRITICAL_FIELDS = ("title", "author", "text")

    def __init__(
        self,
        storage: StorageBackend | None = None,
        config: Config | None = None,
    ) -> None:
        """Initialize the change detector.

        Args:
            storage: Optional persistent storage backend for baselines and alerts.
            config: Optional engine configuration. When omitted, defaults are used.
        """
        self._storage = storage
        self._config = config
        self._size_threshold = self._resolve_size_threshold()

    def _resolve_size_threshold(self) -> float:
        """Return the configured fractional HTML size delta threshold."""
        if self._config is None:
            return self._DEFAULT_SIZE_THRESHOLD
        return getattr(self._config, "change_alert_size_threshold", self._DEFAULT_SIZE_THRESHOLD)

    @staticmethod
    def structural_fingerprint(html: str) -> str:
        """Return a stable hash of the DOM skeleton.

        The fingerprint ignores text content, ``id`` values, and volatile
        attribute values. It captures the tag hierarchy and the names of
        attributes present on each tag.
        """
        soup = BeautifulSoup(html, "html.parser")

        for tag_name in ("script", "style"):
            for tag in soup.find_all(tag_name):
                tag.decompose()

        def _serialize(tag: Tag | object) -> str:
            if not isinstance(tag, Tag) or tag.name is None:
                return ""
            name = tag.name
            attr_names = sorted(k for k in tag.attrs if k != "id")
            node = f"{name}[{','.join(attr_names)}]"
            children = "".join(_serialize(child) for child in tag.children)
            return f"{node}({children})"

        serialized = _serialize(soup)
        normalized = " ".join(serialized.split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def selector_snapshot(extracted: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Build a field-to-selector match snapshot from extracted data."""
        snapshot: dict[str, dict[str, Any]] = {}

        for field_name, value in extracted.items():
            if field_name in {"selectors_used", "platform", "url", "content_type"}:
                continue
            if not isinstance(value, dict):
                continue
            selector = value.get("selector_used")
            if not selector:
                continue
            snapshot[field_name] = {
                "selector": selector,
                "matched": bool(value.get("matched", value.get("value"))),
                "confidence": float(value.get("confidence", 1.0)),
            }

        page_selectors = extracted.get("selectors_used", [])
        if page_selectors:
            snapshot["_page"] = {
                "selectors": list(page_selectors),
                "matched": True,
            }

        return snapshot

    @staticmethod
    def critical_fields_hash(output: UnifiedOutput | None) -> str | None:
        """Return a hash of critical extracted text fields."""
        if output is None:
            return None
        parts = []
        for field in ChangeDetector._CRITICAL_FIELDS:
            value = getattr(output, field, None) or ""
            parts.append(str(value)[:200])
        combined = "|".join(parts)
        if not combined.strip("|"):
            return None
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    async def detect(  # noqa: PLR0913
        self,
        *,
        url: str,
        platform: str,
        content_type: str | None,
        raw_response: RawResponse,
        extracted: dict[str, Any],
        output: UnifiedOutput | None,
        archive_id: str | None = None,
    ) -> ChangeAlert | None:
        """Compare the current scrape against the stored baseline.

        When no baseline exists, one is created and ``None`` is returned.
        """
        fingerprint = self.structural_fingerprint(raw_response.html)
        selectors = self.selector_snapshot(extracted)
        critical_hash = self.critical_fields_hash(output)
        html_size = len(raw_response.html.encode("utf-8"))

        baseline = None
        if self._storage is not None:
            baseline = self._storage.get_latest_baseline(url)

        if baseline is None:
            self._save_baseline(
                url=url,
                platform=platform,
                content_type=content_type,
                fingerprint=fingerprint,
                selectors=selectors,
                critical_hash=critical_hash,
                html_size=html_size,
                archive_id=archive_id,
            )
            return None

        alert = self._compare(
            baseline=baseline,
            url=url,
            platform=platform,
            content_type=content_type,
            fingerprint=fingerprint,
            selectors=selectors,
            critical_hash=critical_hash,
            html_size=html_size,
        )

        self._save_baseline(
            url=url,
            platform=platform,
            content_type=content_type,
            fingerprint=fingerprint,
            selectors=selectors,
            critical_hash=critical_hash,
            html_size=html_size,
            archive_id=archive_id,
        )

        return alert

    def _compare(  # noqa: PLR0913
        self,
        *,
        baseline: dict[str, Any],
        url: str,
        platform: str,
        content_type: str | None,
        fingerprint: str,
        selectors: dict[str, dict[str, Any]],
        critical_hash: str | None,
        html_size: int,
    ) -> ChangeAlert | None:
        """Return a ``ChangeAlert`` when drift crosses configured thresholds."""
        details: dict[str, Any] = {}
        alert_types: list[str] = []
        severity = "info"

        if fingerprint != baseline["structural_fingerprint"]:
            alert_types.append("structural_change")
            details["structural_change"] = {
                "old_fingerprint": baseline["structural_fingerprint"],
                "new_fingerprint": fingerprint,
            }
            severity = "warning"

        degraded = self._degraded_selectors(
            baseline["selectors_snapshot"],
            selectors,
        )
        if degraded:
            alert_types.append("selector_degradation")
            details["selector_degradation"] = degraded
            severity = "warning"

        lost_fields = self._lost_fields(baseline["critical_fields_hash"], critical_hash)
        if lost_fields:
            alert_types.append("field_loss")
            details["field_loss"] = lost_fields
            severity = "critical"

        baseline_size = int(baseline.get("html_size_bytes", 0) or 0)
        if baseline_size > 0:
            delta = abs(html_size - baseline_size) / baseline_size
            if delta > self._size_threshold:
                alert_types.append("size_anomaly")
                details["size_anomaly"] = {
                    "baseline_size": baseline_size,
                    "current_size": html_size,
                    "delta_ratio": round(delta, 3),
                }
                if severity != "critical":
                    severity = "warning"

        if not alert_types:
            return None

        return ChangeAlert(
            alert_type=",".join(alert_types),
            severity=severity,
            url=url,
            platform=platform,
            content_type=content_type,
            details=details,
            baseline_id=baseline.get("id"),
        )

    @staticmethod
    def _degraded_selectors(
        baseline: dict[str, Any],
        current: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Return selectors that previously matched but now fail."""
        degraded: list[dict[str, Any]] = []
        for field, snapshot in baseline.items():
            if field == "_page":
                continue
            current_snapshot = current.get(field)
            if current_snapshot is None:
                degraded.append({"field": field, "selector": snapshot.get("selector")})
            elif snapshot.get("matched") and not current_snapshot.get("matched"):
                degraded.append(
                    {
                        "field": field,
                        "selector": snapshot.get("selector"),
                        "old_confidence": snapshot.get("confidence"),
                        "new_confidence": current_snapshot.get("confidence"),
                    },
                )
        return degraded

    def _lost_fields(
        self,
        baseline_hash: str | None,
        current_hash: str | None,
    ) -> list[str]:
        """Return critical fields that appear to have been lost."""
        if baseline_hash is None or current_hash is None:
            return []
        if baseline_hash == current_hash:
            return []
        # A change in the combined hash indicates at least one critical field
        # changed materially. We surface a generic marker here; downstream
        # consumers can inspect the full output for specifics.
        return ["critical_fields_changed"]

    def _save_baseline(  # noqa: PLR0913
        self,
        *,
        url: str,
        platform: str,
        content_type: str | None,
        fingerprint: str,
        selectors: dict[str, dict[str, Any]],
        critical_hash: str | None,
        html_size: int,
        archive_id: str | None,
    ) -> None:
        """Persist the current scrape as the new baseline."""
        if self._storage is None:
            return
        self._storage.save_baseline(
            url=url,
            platform=platform,
            content_type=content_type,
            structural_fingerprint=fingerprint,
            selectors_snapshot=selectors,
            critical_fields_hash=critical_hash,
            html_size_bytes=html_size,
            archive_id=archive_id,
        )


__all__ = ["ChangeDetector"]
