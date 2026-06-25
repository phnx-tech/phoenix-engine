"""Phoenix Engine -- universal pure web scraping engine."""

from __future__ import annotations

from phoenix.adapters import (
    BaseAdapter,
    GenericWebAdapter,
    PluginInterface,
    ScraperPlugin,
)
from phoenix.engine import PhoenixEngine
from phoenix.models.output import (
    CollectionResult,
    ScrapingResult,
    UnifiedOutput,
)
from phoenix.models.strategy import ScrapingStrategy

# Import options and core models before engine to prevent circular imports
# with router/pipeline submodules.
from phoenix.options import CollectionOptions, ScrapingOptions
from phoenix.plugins import PluginLoader, PluginManifest, PluginRegistry
from phoenix.version import __version__

__all__ = [
    "BaseAdapter",
    "CollectionOptions",
    "CollectionResult",
    "GenericWebAdapter",
    "PhoenixEngine",
    "PluginInterface",
    "PluginLoader",
    "PluginManifest",
    "PluginRegistry",
    "ScraperPlugin",
    "ScrapingOptions",
    "ScrapingResult",
    "ScrapingStrategy",
    "UnifiedOutput",
    "__version__",
]
