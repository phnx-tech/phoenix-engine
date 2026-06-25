"""Plugin loader for Phoenix Engine adapters.

Discovers and registers platform adapters from built-in packages, entry
points, and user plugin directories. Broken plugins are logged and skipped
rather than failing engine startup.
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import logging
import pkgutil
import sys
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING

import phoenix.adapters as adapters_package
from phoenix.adapters.base import BaseAdapter
from phoenix.plugins.manifest import PluginManifest
from phoenix.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from types import ModuleType


logger = logging.getLogger(__name__)


class PluginLoader:
    """Discovers, loads, and registers Phoenix Engine adapter plugins."""

    def __init__(self, plugin_dirs: list[str] | None = None) -> None:
        """Initialize the plugin loader.

        Args:
            plugin_dirs: Optional list of directories to scan for user
                adapter plugins.
        """
        self.plugin_dirs = [Path(d) for d in (plugin_dirs or [])]
        self.registry = PluginRegistry()

    def load_builtin_adapters(self) -> list[BaseAdapter]:
        """Scan ``phoenix.adapters`` and register all adapter classes found.

        Returns:
            List of adapters that were successfully loaded and registered.
        """
        loaded: list[BaseAdapter] = []
        prefix = adapters_package.__name__ + "."
        for module_info in pkgutil.iter_modules(adapters_package.__path__, prefix):
            module = importlib.import_module(module_info.name)
            for adapter in self._find_adapter_classes(module):
                self.register(adapter)
                loaded.append(adapter)

        return loaded

    def load_entry_points(self) -> list[BaseAdapter]:
        """Load adapters registered under the ``phoenix.plugins`` entry point.

        Returns:
            List of adapters that were successfully loaded and registered.
        """
        loaded: list[BaseAdapter] = []
        try:
            eps = entry_points(group="phoenix.plugins")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not scan entry points: %s", exc)
            return loaded

        for ep in eps:
            try:
                obj = ep.load()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to load entry point %s: %s", ep.name, exc)
                continue

            adapter = self._instantiate_adapter(obj)
            if adapter is not None:
                self.register(adapter)
                loaded.append(adapter)

        return loaded

    def load_plugin_dirs(self) -> list[BaseAdapter]:
        """Scan user plugin directories for adapter modules.

        Returns:
            List of adapters that were successfully loaded and registered.
        """
        loaded: list[BaseAdapter] = []
        for directory in self.plugin_dirs:
            if not directory.exists() or not directory.is_dir():
                logger.warning("Plugin directory does not exist: %s", directory)
                continue

            for path in directory.iterdir():
                if path.is_dir() and (path / "__init__.py").exists():
                    module = self._load_module_from_package(path)
                elif path.is_file() and path.suffix == ".py" and not path.name.startswith("_"):
                    module = self._load_module_from_file(path)
                else:
                    continue

                if module is None:
                    continue

                for adapter in self._find_adapter_classes(module):
                    self.register(adapter)
                    loaded.append(adapter)

        return loaded

    def register(self, adapter: BaseAdapter) -> None:
        """Validate and register ``adapter`` with the plugin registry.

        Raises:
            TypeError: If ``adapter`` does not implement the adapter contract.
            ValueError: If the adapter manifest is invalid.
        """
        if not isinstance(adapter, BaseAdapter):
            raise TypeError(
                f"Adapter must subclass BaseAdapter, got {type(adapter).__name__}",
            )

        manifest = adapter.manifest
        if not isinstance(manifest, PluginManifest):
            raise TypeError(
                f"Adapter manifest must be a PluginManifest, got {type(manifest).__name__}",
            )
        if not manifest.platforms:
            raise ValueError(
                f"Adapter {manifest.name} must declare at least one platform.",
            )
        if not manifest.url_patterns:
            raise ValueError(
                f"Adapter {manifest.name} must declare at least one URL pattern.",
            )

        self.registry.register(adapter)

    def get_adapter(self, platform: str) -> BaseAdapter:
        """Return the adapter registered for ``platform``.

        Raises:
            KeyError: If no adapter is registered for ``platform``.
        """
        return self.registry.get_adapter(platform)

    def match_url(self, url: str) -> BaseAdapter | None:
        """Return the first adapter whose URL pattern matches ``url``.

        Returns:
            Matching adapter or ``None`` if no adapter handles the URL.
        """
        return self.registry.match_url(url)

    def list_adapters(self) -> list[PluginManifest]:
        """Return manifests for all registered adapters."""
        return self.registry.list_adapters()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_adapter_classes(self, module: ModuleType) -> list[BaseAdapter]:
        """Return instances of BaseAdapter subclasses defined in ``module``."""
        found: list[BaseAdapter] = []
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, BaseAdapter)
                and obj is not BaseAdapter
                and obj.__module__ == module.__name__
            ):
                try:
                    instance = obj()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to instantiate adapter %s: %s", obj.__name__, exc)
                    continue
                found.append(instance)
        return found

    def _instantiate_adapter(self, obj: object) -> BaseAdapter | None:
        """Instantiate an adapter from an entry point object.

        Supports both adapter classes and factory callables that return an
        adapter instance.
        """
        if isinstance(obj, BaseAdapter):
            return obj

        if inspect.isclass(obj) and issubclass(obj, BaseAdapter):
            try:
                return obj()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to instantiate entry point adapter: %s", exc)
                return None

        if callable(obj):
            try:
                result = obj()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to call entry point factory: %s", exc)
                return None
            if isinstance(result, BaseAdapter):
                return result

        logger.warning(
            "Entry point object %r is not a BaseAdapter subclass or factory.",
            obj,
        )
        return None

    def _load_module_from_file(self, path: Path) -> ModuleType | None:
        """Load a Python module from a file path."""
        module_name = f"phoenix_plugin_{path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                logger.warning("Could not create module spec for %s", path)
                return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not create module spec for %s: %s", path, exc)
            return None

        try:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load plugin module %s: %s", path, exc)
            return None

        return module

    def _load_module_from_package(self, path: Path) -> ModuleType | None:
        """Load a Python package directory containing an ``__init__.py``."""
        module_name = f"phoenix_plugin_{path.name}"
        try:
            spec = importlib.util.spec_from_file_location(
                module_name,
                path / "__init__.py",
                submodule_search_locations=[str(path)],
            )
            if spec is None or spec.loader is None:
                logger.warning("Could not create package spec for %s", path)
                return None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not create package spec for %s: %s", path, exc)
            return None

        try:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load plugin package %s: %s", path, exc)
            return None

        return module


__all__ = ["PluginLoader"]
