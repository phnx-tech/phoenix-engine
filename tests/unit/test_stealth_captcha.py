"""Unit tests for CAPTCHA / anti-bot detection."""

from __future__ import annotations

import pytest

from phoenix.stealth.captcha import CaptchaAction, CaptchaDetector

pytestmark = pytest.mark.unit


def test_captcha_detector_finds_challenge_marker() -> None:
    """A page containing a challenge marker is flagged."""
    detector = CaptchaDetector()
    html = "<html><div class='cf-challenge'>Please wait</div></html>"
    result = detector.detect(html, url="https://example.com")

    assert result.detected is True
    assert "cf-challenge" in result.reason


def test_captcha_detector_flags_short_html() -> None:
    """An unusually short response is flagged as suspicious."""
    detector = CaptchaDetector(min_html_length=200)
    result = detector.detect("<html></html>", url="https://example.com")

    assert result.detected is True
    assert "short" in result.reason


def test_captcha_detector_flags_interstitial_url() -> None:
    """A final URL containing /captcha is flagged."""
    detector = CaptchaDetector()
    result = detector.detect(
        "<html>ok</html>",
        url="https://example.com",
        final_url="https://example.com/captcha",
    )

    assert result.detected is True
    assert "interstitial" in result.reason


def test_captcha_detector_ignores_normal_page() -> None:
    """A normal HTML page is not flagged."""
    detector = CaptchaDetector()
    html = "<html><body><h1>Hello</h1><p>" + "Content here. " * 50 + "</p></body></html>"
    result = detector.detect(html, url="https://example.com")

    assert result.detected is False


def test_captcha_detector_respects_skip_action() -> None:
    """SKIP action never flags a page as detected."""
    detector = CaptchaDetector(action=CaptchaAction.SKIP)
    result = detector.detect("<html>cf-challenge</html>", url="https://example.com")
    assert result.detected is False
