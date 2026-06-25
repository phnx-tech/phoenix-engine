"""Unit tests for stealth browser profiles."""

from __future__ import annotations

import pytest

from phoenix.stealth.profile import StealthProfile, profile_presets

pytestmark = pytest.mark.unit


def test_profile_context_kwargs_include_user_agent_and_viewport() -> None:
    """A profile produces Playwright-compatible context arguments."""
    profile = StealthProfile(
        profile_id="test",
        user_agent="Mozilla/5.0",
        viewport={"width": 1920, "height": 1080},
        locale="en-GB",
        timezone_id="Europe/London",
    )
    kwargs = profile.context_kwargs()

    assert kwargs["user_agent"] == "Mozilla/5.0"
    assert kwargs["viewport"] == {"width": 1920, "height": 1080}
    assert kwargs["locale"] == "en-GB"
    assert kwargs["timezone_id"] == "Europe/London"


def test_profile_presets_contains_common_profiles() -> None:
    """Preset profiles include at least Chrome and Firefox variants."""
    presets = profile_presets()
    assert "chrome_windows" in presets
    assert "chrome_mac" in presets
    assert "firefox_windows" in presets


def test_profile_with_proxy_creates_new_identity() -> None:
    """Attaching a proxy changes the profile identity."""
    profile = profile_presets()["chrome_windows"]
    proxied = profile.with_proxy({"server": "http://proxy.example.com:8080"})

    assert proxied.profile_id != profile.profile_id
    assert "proxy.example.com" in proxied.profile_id


def test_profile_with_proxy_none_returns_same_profile() -> None:
    """Calling with_proxy(None) returns the original profile unchanged."""
    profile = profile_presets()["chrome_windows"]
    assert profile.with_proxy(None) is profile
