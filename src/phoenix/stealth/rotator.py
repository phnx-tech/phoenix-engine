"""Rotators for profiles and proxies."""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from enum import StrEnum

from phoenix.stealth.profile import StealthProfile, profile_presets


class RotationPolicy(StrEnum):
    """How to pick the next item from a rotator list."""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"


@dataclass
class ProfileRotator:
    """Rotate browser fingerprint profiles."""

    profiles: list[StealthProfile]
    policy: RotationPolicy = RotationPolicy.ROUND_ROBIN

    def __post_init__(self) -> None:
        """Prepare iterator for round-robin mode."""
        if not self.profiles:
            msg = "ProfileRotator requires at least one profile"
            raise ValueError(msg)
        self._cycle = itertools.cycle(self.profiles)

    def next(self) -> StealthProfile:
        """Return the next profile according to the rotation policy."""
        if self.policy == RotationPolicy.RANDOM:
            return random.choice(self.profiles)  # noqa: S311
        return next(self._cycle)

    @classmethod
    def from_preset_names(
        cls,
        names: list[str],
        *,
        policy: RotationPolicy = RotationPolicy.ROUND_ROBIN,
    ) -> ProfileRotator:
        """Build a rotator from preset profile names."""
        presets = profile_presets()
        profiles = []
        for name in names:
            if name not in presets:
                msg = f"Unknown stealth profile: {name}"
                raise ValueError(msg)
            profiles.append(presets[name])
        return cls(profiles=profiles, policy=policy)


@dataclass
class ProxyRotator:
    """Rotate upstream HTTP proxies."""

    proxies: list[str]
    policy: RotationPolicy = RotationPolicy.ROUND_ROBIN

    def __post_init__(self) -> None:
        """Prepare iterator for round-robin mode and validate URLs."""
        if not self.proxies:
            msg = "ProxyRotator requires at least one proxy URL"
            raise ValueError(msg)
        self._cycle = itertools.cycle(self.proxies)

    def next(self) -> dict[str, str]:
        """Return the next proxy as Playwright proxy kwargs."""
        if self.policy == RotationPolicy.RANDOM:
            url = random.choice(self.proxies)  # noqa: S311
        else:
            url = next(self._cycle)
        return {"server": url}

    def next_url(self) -> str:
        """Return the raw next proxy URL."""
        if self.policy == RotationPolicy.RANDOM:
            return random.choice(self.proxies)  # noqa: S311
        return next(self._cycle)


__all__ = ["ProfileRotator", "ProxyRotator", "RotationPolicy"]
