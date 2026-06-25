"""Plugin system for loading platform adapters."""

from __future__ import annotations

from phoenix.plugins.loader import PluginLoader
from phoenix.plugins.manifest import PluginManifest
from phoenix.plugins.registry import PluginRegistry

__all__ = ["PluginLoader", "PluginManifest", "PluginRegistry"]
