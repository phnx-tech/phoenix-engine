"""Unit tests for the token-bucket rate limiter."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from phoenix.infrastructure.rate_limiter import RateLimiter
from phoenix.models.config import Config

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_rate_limiter_first_request_no_wait() -> None:
    """The first request to a domain proceeds without sleeping."""
    limiter = RateLimiter(Config(rate_limits={"example.com": 1.0}))

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await limiter.wait_if_needed("example.com")

    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_rate_limiter_paces_subsequent_requests() -> None:
    """Back-to-back requests to the same domain sleep for the bucket interval."""
    limiter = RateLimiter(Config(rate_limits={"example.com": 1.0}))

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await limiter.wait_if_needed("example.com")
        await limiter.wait_if_needed("example.com")

    mock_sleep.assert_awaited_once()
    call_args = mock_sleep.await_args.args[0]
    assert 0.9 <= call_args <= 1.1


@pytest.mark.asyncio
async def test_rate_limiter_platform_specific_default() -> None:
    """Instagram uses the platform-specific default rate."""
    limiter = RateLimiter(Config())
    rate = limiter._rate_for("instagram.com")
    assert rate == 0.5


@pytest.mark.asyncio
async def test_rate_limiter_config_override() -> None:
    """Config.rate_limits overrides platform defaults."""
    limiter = RateLimiter(Config(rate_limits={"instagram.com": 2.0}))
    rate = limiter._rate_for("instagram.com")
    assert rate == 2.0


@pytest.mark.asyncio
async def test_rate_limiter_config_override_by_platform_key() -> None:
    """Config.rate_limits can use the platform key to override defaults."""
    limiter = RateLimiter(Config(rate_limits={"instagram": 0.1}))
    rate = limiter._rate_for("instagram.com")
    assert rate == 0.1


@pytest.mark.asyncio
async def test_rate_limiter_different_domains_independent() -> None:
    """Requests to different domains do not share bucket state."""
    limiter = RateLimiter(Config(rate_limits={"example.com": 1.0, "other.org": 1.0}))

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await limiter.wait_if_needed("example.com")
        await limiter.wait_if_needed("other.org")

    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_rate_limiter_reset_clears_state() -> None:
    """Reset clears all bucket state so the next request is unthrottled."""
    limiter = RateLimiter(Config(rate_limits={"example.com": 1.0}))

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await limiter.wait_if_needed("example.com")
        await limiter.reset()
        await limiter.wait_if_needed("example.com")

    mock_sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_record_outcome_tracks_errors() -> None:
    """Recording a failure marks the outcome as unsuccessful."""
    limiter = RateLimiter(Config(rate_limits={"example.com": 1.0}))
    await limiter.record_outcome(
        "example.com",
        latency_ms=100.0,
        status_code=None,
        error=RuntimeError("boom"),
    )

    bucket = limiter._buckets["example.com"]
    assert not bucket.outcomes[-1]
    assert bucket.last_error == "RuntimeError"


@pytest.mark.asyncio
async def test_adaptive_throttling_increases_delay_after_errors() -> None:
    """Back-to-back errors increase the effective wait time."""
    limiter = RateLimiter(Config(rate_limits={"example.com": 1.0}))
    for _ in range(5):
        await limiter.record_outcome(
            "example.com",
            latency_ms=100.0,
            status_code=503,
            error=None,
        )

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await limiter.wait_if_needed("example.com")
        await limiter.wait_if_needed("example.com")

    call_args = mock_sleep.await_args.args[0]
    # Base interval is ~1s; adaptive factor should push it higher.
    assert call_args > 1.0


@pytest.mark.asyncio
async def test_adaptive_throttling_decreases_delay_after_fast_success() -> None:
    """Fast successes keep the adaptive factor at or below 1.0."""
    limiter = RateLimiter(Config(rate_limits={"example.com": 1.0}))
    for _ in range(5):
        await limiter.record_outcome(
            "example.com",
            latency_ms=50.0,
            status_code=200,
            error=None,
        )

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        await limiter.wait_if_needed("example.com")
        await limiter.wait_if_needed("example.com")

    call_args = mock_sleep.await_args.args[0]
    assert call_args <= 1.0
