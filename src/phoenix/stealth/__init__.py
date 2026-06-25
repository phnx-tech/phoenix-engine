"""Anti-detection utilities for browser-based collection."""

from __future__ import annotations

from phoenix.stealth.captcha import CaptchaAction, CaptchaDetector
from phoenix.stealth.humanizer import Humanizer
from phoenix.stealth.profile import StealthProfile, profile_presets
from phoenix.stealth.rotator import ProfileRotator, ProxyRotator, RotationPolicy
from phoenix.stealth.warming import SessionWarming

__all__ = [
    "CaptchaAction",
    "CaptchaDetector",
    "Humanizer",
    "ProfileRotator",
    "ProxyRotator",
    "RotationPolicy",
    "SessionWarming",
    "StealthProfile",
    "profile_presets",
]
