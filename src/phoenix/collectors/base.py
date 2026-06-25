"""Abstract base class for Phoenix Engine collectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from phoenix.models.document import RawResponse

if TYPE_CHECKING:
    from phoenix.options import CollectionOptions


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(UTC)


class Collector(ABC):
    """Abstract base class for URL collection strategies.

    Concrete implementations fetch raw HTML via direct HTTP or headless
    browser automation and return a standardized :class:`RawResponse`.
    """

    @abstractmethod
    async def collect(self, url: str, options: CollectionOptions) -> RawResponse:
        """Collect the raw HTML response for ``url``.

        Args:
            url: Target URL to fetch.
            options: Collection options such as timeout and archive flags.

        Returns:
            A raw response containing HTML, status, headers, and metadata.

        Raises:
            ScrapingError: When collection fails for any reason.
        """

    @property
    @abstractmethod
    def strategy(self) -> str:
        """Return the strategy identifier for this collector."""


class StubCollector(Collector):
    """In-memory collector that returns synthetic HTML without network calls."""

    def __init__(
        self,
        strategy: str = "http",
        *,
        html: str = "",
    ) -> None:
        """Initialize with a strategy label and optional HTML payload."""
        self._strategy = strategy
        self._html = html or (
            "<html><head><title>Phoenix Test</title></head>"
            "<body><p>Hello from Phoenix Engine</p></body></html>"
        )

    @property
    def strategy(self) -> str:
        """Return the configured strategy label."""
        return self._strategy

    async def collect(self, url: str, options: CollectionOptions) -> RawResponse:  # noqa: ARG002
        """Return a minimal raw HTML response."""
        return RawResponse(
            url=url,
            final_url=url,
            status_code=200,
            headers={"content-type": "text/html"},
            html=self._html,
            strategy=self._strategy,
        )


__all__ = ["Collector", "RawResponse", "StubCollector"]
