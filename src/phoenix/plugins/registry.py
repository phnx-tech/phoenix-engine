"""Registry for loaded Phoenix Engine adapter plugins.

The registry stores adapter instances keyed by platform identifier and
provides URL-to-adapter matching. A module-level singleton is used so that
the plugin loader, router, and engine share the same adapter catalog by
default.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, cast

if TYPE_CHECKING:
    from re import Pattern

    from phoenix.adapters.base import BaseAdapter
    from phoenix.plugins.manifest import PluginManifest


class PluginRegistry:
    """In-memory registry of loaded platform adapters.

    The registry is implemented as a singleton so multiple components
    (``PluginLoader``, ``URLRouter``, ``PhoenixEngine``) observe the same
    adapter catalog without passing state around.
    """

    _instance: PluginRegistry | None = None

    def __new__(cls) -> Self:
        """Create or return the singleton registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._adapters = {}
            cls._instance._patterns = []
        return cast("Self", cls._instance)

    def __init__(self) -> None:
        """Initialize the registry attributes on the singleton instance."""
        if not hasattr(self, "_adapters"):
            self._adapters: dict[str, BaseAdapter] = {}
        if not hasattr(self, "_patterns"):
            self._patterns: list[tuple[Pattern[str], BaseAdapter]] = []

    def register(self, adapter: BaseAdapter) -> None:
        """Register ``adapter`` under each platform it supports.

        If an adapter for a platform is already registered, it is replaced
        so that later loads (e.g., user plugins) can override built-ins.
        """
        for platform in adapter.manifest.platforms:
            self._adapters[platform] = adapter

        for pattern in adapter.supported_patterns():
            self._patterns.append((pattern, adapter))

    def get_adapter(self, platform: str) -> BaseAdapter:
        """Return the adapter registered for ``platform``.

        Raises:
            KeyError: If no adapter is registered for ``platform``.
        """
        try:
            return self._adapters[platform]
        except KeyError as exc:
            raise KeyError(f"No adapter registered for platform: {platform}") from exc

    def match_url(self, url: str) -> BaseAdapter | None:
        """Return the first adapter whose URL pattern matches ``url``.

        Patterns are evaluated in registration order. Returns ``None`` if no
        adapter matches.
        """
        for pattern, adapter in self._patterns:
            if pattern.match(url):
                return adapter
        return None

    def match_url_all(self, url: str) -> list[BaseAdapter]:
        """Return all adapters whose URL patterns match ``url``.

        Adapters are returned in registration order. This is useful when a
        catch-all generic adapter is registered before more specific adapters
        and the caller wants to find the most specific match.
        """
        return [adapter for pattern, adapter in self._patterns if pattern.match(url)]

    def list_adapters(self) -> list[PluginManifest]:
        """Return manifests for all registered adapters.

        Each platform appears at most once even if it is matched by multiple
        URL patterns.
        """
        seen: set[str] = set()
        manifests: list[PluginManifest] = []
        for adapter in self._adapters.values():
            name = adapter.manifest.name
            if name not in seen:
                seen.add(name)
                manifests.append(adapter.manifest)
        return manifests

    def _reset(self) -> None:
        """Reset the registry. Intended for tests only."""
        self._adapters.clear()
        self._patterns.clear()


__all__ = ["PluginRegistry"]
