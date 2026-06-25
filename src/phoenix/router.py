"""URL router for Phoenix Engine.

Maps input URLs to platform identifiers based on domain and path patterns.
The router consults the plugin loader first so that platform adapters can
extend routing without modifying core code, and falls back to the generic
web adapter for unrecognized domains.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlencode, urlparse

from phoenix.adapters.generic import GenericWebAdapter
from phoenix.exceptions import UnsupportedURLError
from phoenix.models import URLClassification
from phoenix.plugins.loader import PluginLoader

if TYPE_CHECKING:
    from phoenix.adapters.base import BaseAdapter


# Ordered platform patterns for built-in platforms. Generic routing is handled
# by the plugin loader so that the generic web adapter can be extended without
# touching core code.
_PLATFORM_PATTERNS: dict[str, list[str]] = {
    "instagram": [
        r"https?://(?:www\.)?instagram\.com/p/[^/]+",
        r"https?://(?:www\.)?instagram\.com/reel/[^/]+",
        r"https?://(?:www\.)?instagram\.com/[^/]+",
    ],
    "x": [
        r"https?://(?:www\.)?(?:twitter|x)\.com/[^/]+/status/\d+",
        r"https?://(?:www\.)?(?:twitter|x)\.com/[^/]+",
    ],
    "tiktok": [
        r"https?://(?:www\.)?tiktok\.com/@[^/]+/video/\d+",
        r"https?://(?:www\.)?tiktok\.com/t/\w+",
        r"https?://(?:www\.)?tiktok\.com/@[^/]+",
    ],
    "linkedin": [
        r"https?://(?:www\.)?linkedin\.com/posts/[^/]+",
        r"https?://(?:www\.)?linkedin\.com/pulse/[^/]+",
        r"https?://(?:www\.)?linkedin\.com/activity/[^/]+",
        r"https?://(?:www\.)?linkedin\.com/in/[^/]+",
        r"https?://(?:www\.)?linkedin\.com/company/[^/]+",
    ],
    "facebook": [
        r"https?://(?:www\.)?facebook\.com/[^/]+/posts/[^/]+",
        r"https?://(?:www\.)?facebook\.com/[^/]+/photos/[^/]+",
        r"https?://(?:www\.)?facebook\.com/[^/]+/videos/[^/]+",
        r"https?://(?:www\.)?facebook\.com/[^/]+/reel/[^/]+",
        r"https?://(?:www\.)?facebook\.com/[^/]+",
    ],
    "youtube": [
        r"https?://(?:www\.)?youtube\.com/watch\?.*v=[^&]+",
        r"https?://(?:www\.)?youtube\.com/shorts/[^/]+",
        r"https?://(?:www\.)?youtube\.com/embed/[^/]+",
        r"https?://(?:www\.)?youtube\.com/@[^/]+",
        r"https?://(?:www\.)?youtube\.com/channel/[^/]+",
        r"https?://(?:www\.)?youtu\.be/[^/]+",
    ],
}

_GENERIC_PLATFORM = "generic"
_GENERIC_PATTERN = r"https?://.+"

# Tracking parameters to strip during normalization.
_TRACKING_PARAMS: set[str] = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "fbclid",
    "gclid",
    "ttclid",
    "li_fat_id",
    "mc_cid",
    "mc_eid",
}

# Content-type inference rules: (platform, path substring) -> content type.
_CONTENT_TYPE_RULES: list[tuple[str, str, str]] = [
    ("instagram", "/p/", "post"),
    ("instagram", "/reel/", "reel"),
    ("x", "/status/", "post"),
    ("tiktok", "/video/", "video"),
    ("tiktok", "/t/", "video"),
    ("linkedin", "/posts/", "post"),
    ("linkedin", "/pulse/", "post"),
    ("linkedin", "/activity/", "post"),
    ("linkedin", "/in/", "profile"),
    ("linkedin", "/company/", "profile"),
    ("facebook", "/posts/", "post"),
    ("facebook", "/photos/", "post"),
    ("facebook", "/videos/", "video"),
    ("facebook", "/reel/", "reel"),
    ("youtube", "/watch", "video"),
    ("youtube", "/shorts/", "short"),
    ("youtube", "/embed/", "video"),
    ("youtube", "/@", "profile"),
    ("youtube", "/channel/", "profile"),
    ("youtube", "/youtu.be/", "video"),
]

_DEFAULT_CONTENT_TYPES: dict[str, str] = {
    "instagram": "profile",
    "x": "profile",
    "tiktok": "profile",
    "linkedin": "post",
    "facebook": "profile",
    "youtube": "video",
    _GENERIC_PLATFORM: "article",
}


class URLRouter:
    """Routes URLs to platform identifiers and adapters."""

    def __init__(self, plugin_loader: PluginLoader | None = None) -> None:
        """Initialize the router.

        Args:
            plugin_loader: Optional plugin loader. If ``None``, a default
                loader is created and built-in adapters are loaded.
        """
        self.plugin_loader = plugin_loader or self._build_default_loader()
        self._compiled: dict[str, list[re.Pattern[str]]] = {
            platform: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            for platform, patterns in _PLATFORM_PATTERNS.items()
        }
        self._generic_pattern = re.compile(_GENERIC_PATTERN, re.IGNORECASE)

    def normalize_url(self, url: str) -> str:
        """Normalize a URL by stripping tracking parameters.

        Args:
            url: Raw input URL.

        Returns:
            Normalized URL with tracking query parameters removed.

        Raises:
            UnsupportedURLError: If the URL is malformed or uses an unsupported scheme.
        """
        stripped = url.strip()
        if not stripped:
            raise UnsupportedURLError("URL is empty")

        parsed = urlparse(stripped)
        if parsed.scheme not in {"http", "https"}:
            raise UnsupportedURLError(
                f"Unsupported URL scheme: {parsed.scheme or 'missing'}",
            )
        if not parsed.netloc:
            raise UnsupportedURLError("URL is missing a host")

        query_params = parse_qs(parsed.query, keep_blank_values=True)
        filtered = {k: v for k, v in query_params.items() if k.lower() not in _TRACKING_PARAMS}
        new_query = urlencode(filtered, doseq=True)

        return parsed._replace(query=new_query).geturl()

    def match(self, url: str) -> str | None:
        """Return the platform identifier matching ``url``.

        Built-in platform patterns are checked first, then patterns from
        loaded plugins (excluding the catch-all generic adapter), and finally
        the generic adapter is used as a fallback.

        Args:
            url: URL to classify. Should already be normalized.

        Returns:
            Platform identifier or ``None`` if no pattern matches.
        """
        # 1. Built-in specific platforms
        for platform, patterns in self._compiled.items():
            for pattern in patterns:
                if pattern.match(url):
                    return platform

        # 2. Plugin adapters (excluding generic catch-all)
        specific_adapter = self._match_specific_adapter(url)
        if specific_adapter is not None:
            platforms = specific_adapter.manifest.platforms
            return platforms[0] if platforms else _GENERIC_PLATFORM

        # 3. Generic fallback
        if self._generic_pattern.match(url):
            return _GENERIC_PLATFORM

        return None

    def classify(self, url: str) -> URLClassification:
        """Classify ``url`` into a platform and content type.

        Args:
            url: URL to classify.

        Returns:
            ``URLClassification`` with normalized URL, platform, and content type.

        Raises:
            UnsupportedURLError: If the URL is malformed or unsupported.
        """
        normalized = self.normalize_url(url)
        platform = self.match(normalized)
        if platform is None:
            raise UnsupportedURLError(f"No platform matches URL: {normalized}")

        content_type = self._infer_content_type(platform, normalized)
        return URLClassification(
            url=normalized,
            platform=platform,
            content_type=content_type,
        )

    def get_adapter(self, platform: str) -> BaseAdapter:
        """Return the adapter for ``platform``.

        Falls back to the generic web adapter when ``platform`` is unknown.

        Args:
            platform: Platform identifier.

        Returns:
            Adapter instance for ``platform``.
        """
        if platform == _GENERIC_PLATFORM:
            return self._generic_adapter()

        try:
            return self.plugin_loader.get_adapter(platform)
        except KeyError:
            return self._generic_adapter()

    def get_adapter_for_url(self, url: str) -> BaseAdapter | None:
        """Return the adapter that handles ``url``.

        Args:
            url: URL to match. Should already be normalized.

        Returns:
            Matching adapter or ``None`` if no adapter handles the URL.
        """
        # Built-in platforms
        for platform, patterns in self._compiled.items():
            for pattern in patterns:
                if pattern.match(url):
                    return self.get_adapter(platform)

        # Plugin adapters
        adapter = self._match_specific_adapter(url)
        if adapter is not None:
            return adapter

        # Generic fallback
        if self._generic_pattern.match(url):
            return self._generic_adapter()

        return None

    def _infer_content_type(self, platform: str, url: str) -> str:
        """Infer the content type from the platform and URL path."""
        path = urlparse(url).path.lower()
        for rule_platform, substring, content_type in _CONTENT_TYPE_RULES:
            if rule_platform == platform and substring in path:
                return content_type
        return _DEFAULT_CONTENT_TYPES.get(platform, "article")

    def _match_specific_adapter(self, url: str) -> BaseAdapter | None:
        """Return the first non-generic plugin adapter matching ``url``."""
        for adapter in self.plugin_loader.registry.match_url_all(url):
            if not self._is_generic_adapter(adapter):
                return adapter
        return None

    def _generic_adapter(self) -> BaseAdapter:
        """Return the generic web adapter from the plugin loader."""
        try:
            return self.plugin_loader.get_adapter(_GENERIC_PLATFORM)
        except KeyError:
            # Should not happen once built-ins are loaded, but avoid crashing.
            return GenericWebAdapter()

    def _is_generic_adapter(self, adapter: BaseAdapter) -> bool:
        """Return ``True`` if ``adapter`` is the catch-all generic adapter."""
        manifest = adapter.manifest
        if manifest.name == "generic_web":
            return True
        return _GENERIC_PLATFORM in manifest.platforms

    def _build_default_loader(self) -> PluginLoader:
        """Create a plugin loader with built-in adapters loaded."""
        loader = PluginLoader()
        loader.load_builtin_adapters()
        return loader


__all__ = ["URLRouter"]
