"""Direct HTTP collector using httpx."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

from phoenix.collectors.base import Collector
from phoenix.exceptions import HTTPError, RetryableError
from phoenix.models.document import RawResponse
from phoenix.version import __version__

if TYPE_CHECKING:
    from phoenix.infrastructure.rate_limiter import RateLimiter
    from phoenix.models.config import Config
    from phoenix.options import CollectionOptions

_HTTP_ERROR_THRESHOLD = 400

_TRANSPARENT_USER_AGENT = (
    f"PhoenixEngine/{__version__} (Universal Web Scraping Engine; +https://phoenixengine.dev)"
)

_POLITE_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class DirectCollector(Collector):
    """Collector that fetches pages via direct asynchronous HTTP requests."""

    def __init__(
        self,
        config: Config,
        rate_limiter: RateLimiter,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the direct HTTP collector.

        Args:
            config: Application configuration.
            rate_limiter: Domain rate limiter used to pace requests.
            http_client: Optional httpx client. If omitted, one is created
                with redirect following and polite defaults.
        """
        self._config = config
        self._rate_limiter = rate_limiter
        self._client = http_client or httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=config.max_redirects,
            headers={**_POLITE_HEADERS, "User-Agent": _TRANSPARENT_USER_AGENT},
            timeout=config.timeout,
        )

    @property
    def strategy(self) -> str:
        """Return the strategy identifier."""
        return "http"

    @staticmethod
    def _domain(url: str) -> str:
        """Extract the network location from ``url``."""
        parsed = urlparse(url)
        return parsed.netloc or url

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def collect(self, url: str, options: CollectionOptions) -> RawResponse:
        """Fetch ``url`` via HTTP and return a raw response.

        Args:
            url: Target URL.
            options: Per-request collection options.

        Returns:
            RawResponse with status, headers, and HTML body.

        Raises:
            RetryableError: On timeout, DNS, or connection failure.
            HTTPError: On HTTP 4xx/5xx responses.
        """
        await self._rate_limiter.wait_if_needed(self._domain(url))

        last_error: httpx.RequestError | None = None
        max_attempts = max(1, options.max_retries + 1)

        for attempt in range(max_attempts):
            start = time.perf_counter()
            try:
                response = await self._client.get(
                    url,
                    timeout=options.timeout,
                    follow_redirects=True,
                )
            except httpx.RequestError as exc:
                last_error = exc
                if attempt < max_attempts - 1:
                    continue
                raise RetryableError(
                    f"Failed to fetch {url}: {exc.__class__.__name__}: {exc}",
                ) from exc

            latency_ms = (time.perf_counter() - start) * 1000
            if response.status_code >= _HTTP_ERROR_THRESHOLD:
                raise HTTPError(f"HTTP {response.status_code} for {url}")

            raw_response = RawResponse(
                url=url,
                final_url=str(response.url),
                status_code=response.status_code,
                headers=dict(response.headers),
                html=response.text,
                strategy=self.strategy,
            )
            raw_response.metadata["response_time_ms"] = latency_ms
            return raw_response

        # Defensive fallback; unreachable because errors raise above.
        raise RetryableError(
            f"Failed to fetch {url} after {max_attempts} attempts",
        ) from last_error  # pragma: no cover


__all__ = ["DirectCollector"]
