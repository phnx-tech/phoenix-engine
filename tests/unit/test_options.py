"""Unit tests for ScrapingOptions."""

from __future__ import annotations

import pytest

from phoenix.options import ScrapingOptions

pytestmark = pytest.mark.unit


def test_scraping_options_defaults() -> None:
    """Default options are sensible."""
    options = ScrapingOptions()

    assert options.timeout == 30.0
    assert options.max_retries == 3
    assert options.archive is True
    assert options.strategy is None
    assert options.stealth_enabled is None
    assert options.stealth_profile is None
    assert options.proxy is None
    assert options.humanize is None
    assert options.warm_session is None
    assert options.captcha_action is None


def test_scraping_options_stealth_overrides() -> None:
    """Stealth fields can be set per request."""
    options = ScrapingOptions(
        stealth_enabled=True,
        stealth_profile="chrome_mac",
        proxy="http://proxy.example:8080",
        humanize=True,
        warm_session=True,
        captcha_action="raise",
    )

    assert options.stealth_enabled is True
    assert options.stealth_profile == "chrome_mac"
    assert options.proxy == "http://proxy.example:8080"
    assert options.humanize is True
    assert options.warm_session is True
    assert options.captcha_action == "raise"
