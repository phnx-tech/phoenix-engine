"""Heuristic detection of anti-bot challenges and CAPTCHAs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CaptchaAction(StrEnum):
    """Possible responses when a challenge is detected."""

    FLAG = "flag"
    RAISE = "raise"
    SKIP = "skip"


@dataclass(frozen=True)
class CaptchaDetected:
    """Result of a CAPTCHA / challenge detection check."""

    detected: bool
    reason: str = ""
    action: CaptchaAction = CaptchaAction.FLAG


class CaptchaDetector:
    """Detect common anti-bot and CAPTCHA indicators in page content.

    This is intentionally heuristic-based. It avoids external CAPTCHA-solving
    services and instead flags pages so the caller can decide what to do.
    """

    CHALLENGE_MARKERS: tuple[str, ...] = (
        "cf-challenge",
        "cf-turnstile",
        "g-recaptcha",
        "h-captcha",
        "data-captcha",
        "captcha",
        "challenge-form",
        "ddos-guard",
        "perimeterx",
        "datadome",
        "px-captcha",
        "blocked",
        "access denied",
        "please verify",
        "are you human",
        "security check",
    )

    def __init__(
        self,
        *,
        action: CaptchaAction = CaptchaAction.FLAG,
        min_html_length: int = 200,
    ) -> None:
        """Initialize detector.

        Args:
            action: Default action to recommend when a challenge is found.
            min_html_length: Pages shorter than this are suspicious.
        """
        self.action = action
        self.min_html_length = min_html_length

    def detect(
        self,
        html: str,
        url: str,  # noqa: ARG002
        final_url: str | None = None,
        status_code: int = 200,
    ) -> CaptchaDetected:
        """Return whether the response looks like a bot challenge."""
        if self.action == CaptchaAction.SKIP:
            return CaptchaDetected(detected=False, action=CaptchaAction.SKIP)

        lowered = html.lower()

        if final_url is not None and self._looks_like_interstitial(final_url):
            return CaptchaDetected(
                detected=True,
                reason=f"Final URL looks like an interstitial: {final_url}",
                action=self.action,
            )

        for marker in self.CHALLENGE_MARKERS:
            if marker in lowered:
                return CaptchaDetected(
                    detected=True,
                    reason=f"Challenge marker found: {marker!r}",
                    action=self.action,
                )

        if len(html.strip()) < self.min_html_length:
            return CaptchaDetected(
                detected=True,
                reason="HTML body is unusually short",
                action=self.action,
            )

        if status_code in (403, 429, 503) and self._has_blocking_language(lowered):
            return CaptchaDetected(
                detected=True,
                reason=f"Blocking status code {status_code} with challenge language",
                action=self.action,
            )

        return CaptchaDetected(detected=False)

    @staticmethod
    def _looks_like_interstitial(url: str) -> bool:
        """Return True when the final URL contains common challenge paths."""
        lowered = url.lower()
        return any(
            fragment in lowered
            for fragment in (
                "/captcha",
                "/challenge",
                "/verify",
                "/blocked",
                "cloudflare",
                "datadome",
                "perimeterx",
            )
        )

    @staticmethod
    def _has_blocking_language(html_lower: str) -> bool:
        """Return True when status-code error pages contain bot-blocking text."""
        return any(
            phrase in html_lower
            for phrase in (
                "access denied",
                "forbidden",
                "too many requests",
                "rate limit",
                "unusual traffic",
            )
        )


__all__ = ["CaptchaAction", "CaptchaDetected", "CaptchaDetector"]
