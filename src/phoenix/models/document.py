"""HTML document model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


@dataclass
class HTMLDocument:
    """Parsed HTML document with metadata."""

    url: str
    raw_html: str
    soup: Any
    status_code: int = 200
    headers: dict[str, Any] = field(default_factory=dict)
    final_url: str | None = None


class RawResponse(BaseModel):
    """Raw response produced by a collector before extraction.

    This model is the cross-layer contract between the collection engines
    and the downstream HTML extractor. It captures the URL, final URL after
    redirects, HTTP status, headers, raw HTML, the collection strategy used,
    timing metadata, and an optional screenshot path.
    """

    model_config = ConfigDict(extra="allow")

    url: str = Field(..., description="Original URL requested.")
    final_url: str | None = Field(
        default=None,
        description="Final URL after any redirects.",
    )
    status_code: int = Field(..., description="HTTP status code.")
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Response headers.",
    )
    html: str = Field(..., description="Raw or rendered HTML content.")
    strategy: str = Field(..., description="Collection strategy used (e.g. direct, browser).")
    timestamp: datetime = Field(
        default_factory=_utc_now,
        description="When the response was collected.",
    )
    screenshot_path: str | None = Field(
        default=None,
        description="Path to archived screenshot, if any.",
    )
    error: dict[str, Any] | None = Field(
        default=None,
        description="Error information when collection partially succeeds.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Collector-specific metadata such as anti-bot flags.",
    )


__all__ = ["HTMLDocument", "RawResponse"]
