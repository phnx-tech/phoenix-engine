"""Token-bucket rate limiter for polite per-domain scraping."""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urlparse

from phoenix.models.config import Config

# Default rate is 1 request per 3 seconds ~= 0.33 req/s.
_DEFAULT_REQUESTS_PER_SECOND = 1.0 / 3.0

# Platform-specific defaults expressed as requests per second.
_PLATFORM_DEFAULTS: dict[str, float] = {
    "instagram": 0.5,
    "x": 0.5,
    "twitter": 0.5,
    "tiktok": 0.5,
    "linkedin": 0.2,
    "facebook": 0.5,
    "youtube": 0.5,
}

# Adaptive throttling constants.
_LATENCY_WINDOW = 10
_ERROR_WINDOW = 10
_TARGET_LATENCY_MS = 1000.0
_MIN_FACTOR = 0.5
_MAX_FACTOR = 5.0
_ERROR_RATE_THRESHOLD = 0.2
_HTTP_ERROR_STATUS_THRESHOLD = 400


@dataclass
class _DomainBucket:
    """Token bucket state for a single domain with adaptive feedback."""

    rate_per_second: float
    tokens: float = 1.0
    last_update: float = field(default_factory=time.monotonic)
    latencies: deque[float] = field(
        default_factory=lambda: deque(maxlen=_LATENCY_WINDOW),
    )
    outcomes: deque[bool] = field(
        default_factory=lambda: deque(maxlen=_ERROR_WINDOW),
    )
    last_status: int | None = None
    last_error: str | None = None


class RateLimiter:
    """Async token-bucket rate limiter with per-domain defaults.

    The limiter enforces a minimum delay between consecutive requests to the
    same domain. Platform-specific defaults apply automatically based on the
    target domain, and users may override rates through :class:`Config`.

    Outcome feedback (latency, HTTP status, errors) is used to adapt the
    effective rate per domain.
    """

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the rate limiter.

        Args:
            config: Optional configuration with per-domain rate overrides.
        """
        self._config = config or Config()
        self._buckets: dict[str, _DomainBucket] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _domain(url_or_domain: str) -> str:
        """Extract a normalized domain from a URL or domain string."""
        parsed = urlparse(url_or_domain)
        netloc = parsed.netloc or url_or_domain
        # Strip leading www. and any port.
        host = netloc.split(":", 1)[0].removeprefix("www.")
        return host.lower()

    @staticmethod
    def _platform(domain: str) -> str | None:
        """Infer a platform identifier from a domain."""
        for platform in _PLATFORM_DEFAULTS:
            if platform in domain:
                return platform
        return None

    def _rate_for(self, domain: str) -> float:
        """Return the requests-per-second limit for a domain."""
        host = self._domain(domain)
        overrides = self._config.rate_limits
        # Allow override by exact domain or known platform key.
        if host in overrides:
            return overrides[host]
        platform = self._platform(host)
        if platform and platform in overrides:
            return overrides[platform]
        if platform and platform in _PLATFORM_DEFAULTS:
            return _PLATFORM_DEFAULTS[platform]
        return _DEFAULT_REQUESTS_PER_SECOND

    def _adaptive_factor(self, bucket: _DomainBucket) -> float:
        """Return a multiplier for the base delay based on recent outcomes."""
        factor = 1.0

        if bucket.outcomes:
            error_rate = 1.0 - (sum(bucket.outcomes) / len(bucket.outcomes))
            if error_rate > _ERROR_RATE_THRESHOLD:
                factor += error_rate * 2.0

        if bucket.last_status in {429, 403, 503}:
            factor *= 1.5

        if bucket.last_error in {"AntiBotDetectedError", "RateLimitExceededError"}:
            factor *= 2.0

        if bucket.latencies:
            avg_latency = sum(bucket.latencies) / len(bucket.latencies)
            if avg_latency > _TARGET_LATENCY_MS:
                factor *= min(3.0, avg_latency / _TARGET_LATENCY_MS)

        return max(_MIN_FACTOR, min(_MAX_FACTOR, factor))

    async def wait_if_needed(self, domain: str) -> None:
        """Wait until a request to ``domain`` may proceed.

        Args:
            domain: Target domain or full URL.
        """
        host = self._domain(domain)
        async with self._lock:
            bucket = self._buckets.get(host)
            if bucket is None:
                bucket = _DomainBucket(rate_per_second=self._rate_for(host))
                self._buckets[host] = bucket
            else:
                # Recalculate rate in case config changed.
                bucket.rate_per_second = self._rate_for(host)

            factor = self._adaptive_factor(bucket)
            adaptive_rate = bucket.rate_per_second / factor

            now = time.monotonic()
            elapsed = now - bucket.last_update
            bucket.tokens = min(1.0, bucket.tokens + elapsed * adaptive_rate)
            bucket.last_update = now

            if bucket.tokens < 1.0:
                need = 1.0 - bucket.tokens
                wait_seconds = need / adaptive_rate
                await asyncio.sleep(wait_seconds)
                bucket.tokens = 0.0
                bucket.last_update = time.monotonic()
            else:
                bucket.tokens -= 1.0

    async def record_outcome(
        self,
        domain: str,
        *,
        latency_ms: float,
        status_code: int | None,
        error: Exception | None,
    ) -> None:
        """Record the outcome of a request so throttling can adapt.

        Args:
            domain: Target domain or full URL.
            latency_ms: Round-trip latency in milliseconds.
            status_code: HTTP response status, if any.
            error: Exception raised, if the request failed.
        """
        host = self._domain(domain)
        success = error is None and (
            status_code is None or status_code < _HTTP_ERROR_STATUS_THRESHOLD
        )
        async with self._lock:
            bucket = self._buckets.setdefault(
                host,
                _DomainBucket(rate_per_second=self._rate_for(host)),
            )
            bucket.latencies.append(latency_ms)
            bucket.outcomes.append(success)
            bucket.last_status = status_code
            bucket.last_error = type(error).__name__ if error else None

    async def reset(self) -> None:
        """Clear all bucket state (primarily for tests)."""
        async with self._lock:
            self._buckets.clear()


__all__ = ["RateLimiter"]
