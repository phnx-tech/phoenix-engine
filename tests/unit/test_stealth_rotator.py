"""Unit tests for profile and proxy rotators."""

from __future__ import annotations

import pytest

from phoenix.stealth.profile import profile_presets
from phoenix.stealth.rotator import ProfileRotator, ProxyRotator, RotationPolicy

pytestmark = pytest.mark.unit


def test_profile_rotator_round_robin_cycles_through_profiles() -> None:
    """Round-robin returns profiles in order and loops."""
    profiles = list(profile_presets().values())[:2]
    rotator = ProfileRotator(profiles=profiles, policy=RotationPolicy.ROUND_ROBIN)

    first = rotator.next()
    second = rotator.next()
    third = rotator.next()

    assert first.profile_id == profiles[0].profile_id
    assert second.profile_id == profiles[1].profile_id
    assert third.profile_id == profiles[0].profile_id


def test_profile_rotator_from_presets_rejects_unknown_name() -> None:
    """Building from presets fails for unknown profile names."""
    with pytest.raises(ValueError, match="Unknown stealth profile"):
        ProfileRotator.from_preset_names(["unknown_profile"])


def test_proxy_rotator_returns_playwright_proxy_kwargs() -> None:
    """ProxyRotator returns a dict Playwright can use for context proxy."""
    rotator = ProxyRotator(proxies=["http://proxy1:8080", "http://proxy2:8080"])

    assert rotator.next() == {"server": "http://proxy1:8080"}
    assert rotator.next() == {"server": "http://proxy2:8080"}
    assert rotator.next() == {"server": "http://proxy1:8080"}


def test_rotator_requires_non_empty_list() -> None:
    """Empty profile or proxy list raises ValueError."""
    with pytest.raises(ValueError, match="at least one profile"):
        ProfileRotator(profiles=[])
    with pytest.raises(ValueError, match="at least one proxy URL"):
        ProxyRotator(proxies=[])
