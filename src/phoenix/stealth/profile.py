"""Browser fingerprint profiles for stealth collection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StealthProfile:
    """A coherent browser fingerprint used to create a Playwright context.

    Keeping viewport, locale, timezone, and user-agent consistent makes the
    browser look like a real user rather than a generic headless client.
    """

    profile_id: str
    user_agent: str
    viewport: dict[str, int]
    locale: str = "en-US"
    timezone_id: str = "America/New_York"
    color_scheme: str = "light"
    extra_http_headers: dict[str, str] | None = None
    geolocation: dict[str, float] | None = None
    permissions: list[str] | None = None
    bypass_csp: bool = True
    java_script_enabled: bool = True

    def context_kwargs(self) -> dict[str, Any]:
        """Return Playwright ``browser.new_context`` keyword arguments."""
        kwargs: dict[str, Any] = {
            "user_agent": self.user_agent,
            "viewport": self.viewport,
            "locale": self.locale,
            "timezone_id": self.timezone_id,
            "color_scheme": self.color_scheme,
            "bypass_csp": self.bypass_csp,
            "java_script_enabled": self.java_script_enabled,
        }
        if self.extra_http_headers:
            kwargs["extra_http_headers"] = self.extra_http_headers
        if self.geolocation:
            kwargs["geolocation"] = self.geolocation
            kwargs["permissions"] = self.permissions or ["geolocation"]
        return kwargs

    def with_proxy(self, proxy: dict[str, str] | None) -> StealthProfile:
        """Return a copy of this profile with the given Playwright proxy config."""
        if proxy is None:
            return self
        kwargs = self.context_kwargs()
        kwargs["proxy"] = proxy
        return StealthProfile(
            profile_id=f"{self.profile_id}@{proxy.get('server', 'proxy')}",
            user_agent=self.user_agent,
            viewport=self.viewport,
            locale=self.locale,
            timezone_id=self.timezone_id,
            color_scheme=self.color_scheme,
            extra_http_headers=self.extra_http_headers,
            geolocation=self.geolocation,
            permissions=self.permissions,
            bypass_csp=self.bypass_csp,
            java_script_enabled=self.java_script_enabled,
        )


def profile_presets() -> dict[str, StealthProfile]:
    """Return a small set of realistic desktop browser profiles."""
    return {
        "chrome_windows": StealthProfile(
            profile_id="chrome_windows",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Upgrade-Insecure-Requests": "1",
            },
        ),
        "chrome_mac": StealthProfile(
            profile_id="chrome_mac",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1512, "height": 982},
            locale="en-US",
            timezone_id="America/Los_Angeles",
            extra_http_headers={
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"macOS"',
                "Upgrade-Insecure-Requests": "1",
            },
        ),
        "firefox_windows": StealthProfile(
            profile_id="firefox_windows",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) "
                "Gecko/20100101 Firefox/127.0"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/Chicago",
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Upgrade-Insecure-Requests": "1",
            },
        ),
    }


__all__ = ["StealthProfile", "profile_presets"]
