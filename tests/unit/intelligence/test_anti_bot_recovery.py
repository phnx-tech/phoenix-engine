"""Tests for anti-bot recovery intelligence."""

from __future__ import annotations

import pytest

from phoenix.intelligence.anti_bot_recovery import AntiBotRecovery


@pytest.fixture
def recovery() -> AntiBotRecovery:
    return AntiBotRecovery()


def test_detect_cloudflare(recovery: AntiBotRecovery) -> None:
    html = '<html><title>Just a moment...</title><div class="cf-browser-verification">'
    result = recovery.detect(html, 503)
    assert result["blocked"] is True
    assert "cloudflare" in result["indicators"]


def test_detect_captcha(recovery: AntiBotRecovery) -> None:
    result = recovery.detect("<html>Please complete the CAPTCHA</html>", 200)
    assert result["blocked"] is True
    assert "captcha" in result["indicators"]


def test_detect_rate_limit(recovery: AntiBotRecovery) -> None:
    result = recovery.detect("<html>Too Many Requests</html>", 429)
    assert result["blocked"] is True


def test_not_blocked(recovery: AntiBotRecovery) -> None:
    result = recovery.detect("<html>Normal page content</html>", 200)
    assert result["blocked"] is False


@pytest.mark.asyncio
async def test_suggest_strategy_rate_limit(recovery: AntiBotRecovery) -> None:
    suggestion = await recovery.suggest_strategy("", 429)
    assert suggestion["blocked"] is True
    assert suggestion["strategy"] == "increase_delay"
    assert suggestion["confidence"] > 0.5


@pytest.mark.asyncio
async def test_suggest_strategy_captcha(recovery: AntiBotRecovery) -> None:
    suggestion = await recovery.suggest_strategy(
        "<html>Please verify you are human</html>",
        200,
    )
    assert suggestion["blocked"] is True
    assert suggestion["strategy"] == "switch_to_browser"


@pytest.mark.asyncio
async def test_suggest_strategy_not_blocked(recovery: AntiBotRecovery) -> None:
    suggestion = await recovery.suggest_strategy("<html>OK</html>", 200)
    assert suggestion["blocked"] is False
    assert suggestion["strategy"] is None
