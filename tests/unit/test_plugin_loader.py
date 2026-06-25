"""Unit tests for the Phoenix Engine plugin loader."""

from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from phoenix.adapters.base import BaseAdapter
from phoenix.collectors.base import Collector
from phoenix.options import ScrapingOptions
from phoenix.plugins.loader import PluginLoader
from phoenix.plugins.manifest import PluginManifest
from phoenix.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from phoenix.models.document import RawResponse
    from phoenix.models.output import UnifiedOutput

pytestmark = pytest.mark.unit


class DemoAdapter(BaseAdapter):
    """Demo adapter used in loader tests."""

    @property
    def manifest(self) -> PluginManifest:
        """Return the demo adapter manifest."""
        return PluginManifest(
            name="demo",
            version="1.0.0",
            platforms=["demo"],
            url_patterns=[r"https?://demo\.example/.+"],
        )

    def supported_patterns(self) -> list[re.Pattern[str]]:
        """Return the demo URL patterns."""
        return [re.compile(pattern) for pattern in self.manifest.url_patterns]

    async def collect(
        self,
        url: str,
        strategy: str,
        collector: Collector,
        options: ScrapingOptions,
    ) -> RawResponse:
        """Collect is not exercised in loader tests."""
        raise NotImplementedError

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        """Extract is not exercised in loader tests."""
        raise NotImplementedError

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        """Normalize is not exercised in loader tests."""
        raise NotImplementedError


@pytest.fixture
def fresh_registry() -> PluginRegistry:
    """Return a reset plugin registry for isolated tests."""
    registry = PluginRegistry()
    registry._reset()
    return registry


@pytest.fixture
def loader(fresh_registry: PluginRegistry) -> PluginLoader:
    """Return a plugin loader wired to a fresh registry."""
    return PluginLoader()


def test_loader_initializes_empty(loader: PluginLoader) -> None:
    """A fresh loader has no adapters registered."""
    assert loader.list_adapters() == []
    assert loader.match_url("https://demo.example/post") is None


def test_loader_registers_adapter(loader: PluginLoader) -> None:
    """Register validates and stores a valid adapter."""
    adapter = DemoAdapter()
    loader.register(adapter)

    assert loader.get_adapter("demo") is adapter
    manifests = loader.list_adapters()
    assert len(manifests) == 1
    assert manifests[0].name == "demo"


def test_loader_register_rejects_non_adapter(loader: PluginLoader) -> None:
    """Register raises TypeError for objects that are not adapters."""
    with pytest.raises(TypeError, match="must subclass BaseAdapter"):
        loader.register(MagicMock())


def test_loader_register_rejects_bad_manifest_type(loader: PluginLoader) -> None:
    """Register raises TypeError when the manifest is not a PluginManifest."""

    class BadAdapter(DemoAdapter):
        @property
        def manifest(self) -> object:  # type: ignore[override]
            """Return a non-manifest object."""
            return {"name": "bad"}

    with pytest.raises(TypeError, match="PluginManifest"):
        loader.register(BadAdapter())


def test_loader_register_rejects_missing_platforms(loader: PluginLoader) -> None:
    """Register raises ValueError when the manifest has no platforms."""

    class BadAdapter(DemoAdapter):
        @property
        def manifest(self) -> PluginManifest:
            """Return a manifest without platforms."""
            return PluginManifest(name="bad", version="1.0.0")

    with pytest.raises(ValueError, match="at least one platform"):
        loader.register(BadAdapter())


def test_loader_register_rejects_missing_patterns(loader: PluginLoader) -> None:
    """Register raises ValueError when the manifest has no URL patterns."""

    class BadAdapter(DemoAdapter):
        @property
        def manifest(self) -> PluginManifest:
            """Return a manifest without URL patterns."""
            return PluginManifest(
                name="bad",
                version="1.0.0",
                platforms=["bad"],
                url_patterns=[],
            )

    with pytest.raises(ValueError, match="at least one URL pattern"):
        loader.register(BadAdapter())


def test_loader_match_url_returns_first_match(loader: PluginLoader) -> None:
    """Match_url returns the first adapter whose pattern matches."""
    demo = DemoAdapter()
    loader.register(demo)

    matched = loader.match_url("https://demo.example/post/1")

    assert matched is demo


def test_loader_match_url_returns_none_for_unknown_url(loader: PluginLoader) -> None:
    """Match_url returns None when no adapter pattern matches."""
    loader.register(DemoAdapter())

    assert loader.match_url("https://other.example/post") is None


def test_loader_get_adapter_raises_for_unknown_platform(
    loader: PluginLoader,
) -> None:
    """Get_adapter raises KeyError for an unregistered platform."""
    with pytest.raises(KeyError, match="No adapter registered"):
        loader.get_adapter("unknown")


def test_loader_load_builtin_adapters_finds_generic(loader: PluginLoader) -> None:
    """Load_builtin_adapters discovers the generic web adapter."""
    adapters = loader.load_builtin_adapters()

    names = {adapter.manifest.name for adapter in adapters}
    assert "generic_web" in names
    assert loader.get_adapter("generic") is not None


def test_loader_load_builtin_adapters_is_idempotent(loader: PluginLoader) -> None:
    """Loading built-ins twice does not create duplicate registrations."""
    loader.load_builtin_adapters()
    first_count = len(loader.list_adapters())

    loader.load_builtin_adapters()
    second_count = len(loader.list_adapters())

    assert second_count == first_count


@pytest.mark.asyncio
async def test_loader_load_entry_points_loads_class(loader: PluginLoader) -> None:
    """Load_entry_points instantiates and registers adapter classes."""
    fake_entry = MagicMock()
    fake_entry.name = "demo_entry"
    fake_entry.load = MagicMock(return_value=DemoAdapter)

    with patch(
        "phoenix.plugins.loader.entry_points",
        return_value=[fake_entry],
    ):
        loaded = loader.load_entry_points()

    assert len(loaded) == 1
    assert loaded[0].manifest.name == "demo"
    assert loader.get_adapter("demo") is loaded[0]


@pytest.mark.asyncio
async def test_loader_load_entry_points_loads_instance(loader: PluginLoader) -> None:
    """Load_entry_points accepts pre-instantiated adapter objects."""
    adapter = DemoAdapter()
    fake_entry = MagicMock()
    fake_entry.name = "demo_entry"
    fake_entry.load = MagicMock(return_value=adapter)

    with patch(
        "phoenix.plugins.loader.entry_points",
        return_value=[fake_entry],
    ):
        loaded = loader.load_entry_points()

    assert loaded == [adapter]


@pytest.mark.asyncio
async def test_loader_load_entry_points_loads_factory(loader: PluginLoader) -> None:
    """Load_entry_points accepts factory callables returning adapters."""

    def _factory() -> DemoAdapter:
        return DemoAdapter()

    fake_entry = MagicMock()
    fake_entry.name = "demo_entry"
    fake_entry.load = MagicMock(return_value=_factory)

    with patch(
        "phoenix.plugins.loader.entry_points",
        return_value=[fake_entry],
    ):
        loaded = loader.load_entry_points()

    assert len(loaded) == 1
    assert loaded[0].manifest.name == "demo"


@pytest.mark.asyncio
async def test_loader_load_entry_points_factory_returns_non_adapter(
    loader: PluginLoader,
) -> None:
    """Factories that do not return adapters are skipped."""

    def _factory() -> str:
        return "not an adapter"

    fake_entry = MagicMock()
    fake_entry.name = "bad_entry"
    fake_entry.load = MagicMock(return_value=_factory)

    with patch(
        "phoenix.plugins.loader.entry_points",
        return_value=[fake_entry],
    ):
        loaded = loader.load_entry_points()

    assert loaded == []


@pytest.mark.asyncio
async def test_loader_load_entry_points_object_is_neither_class_nor_factory(
    loader: PluginLoader,
) -> None:
    """Entry point objects that are not adapters/classes/factories are skipped."""
    fake_entry = MagicMock()
    fake_entry.name = "bad_entry"
    fake_entry.load = MagicMock(return_value=42)

    with patch(
        "phoenix.plugins.loader.entry_points",
        return_value=[fake_entry],
    ):
        loaded = loader.load_entry_points()

    assert loaded == []


@pytest.mark.asyncio
async def test_loader_load_entry_points_skips_broken_entry(loader: PluginLoader) -> None:
    """Broken entry points are skipped without failing the whole load."""
    broken_entry = MagicMock()
    broken_entry.name = "broken"
    broken_entry.load = MagicMock(side_effect=ImportError("simulated"))

    with patch(
        "phoenix.plugins.loader.entry_points",
        return_value=[broken_entry],
    ):
        loaded = loader.load_entry_points()

    assert loaded == []


@pytest.mark.asyncio
async def test_loader_load_entry_points_scan_failure(loader: PluginLoader) -> None:
    """Failure to scan entry points is handled gracefully."""
    with patch(
        "phoenix.plugins.loader.entry_points",
        side_effect=RuntimeError("simulated"),
    ):
        loaded = loader.load_entry_points()

    assert loaded == []


def test_loader_load_plugin_dirs_discovers_module(
    loader: PluginLoader,
    tmp_path: Path,
) -> None:
    """Load_plugin_dirs loads adapter modules from a directory."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "demo_plugin.py"
    plugin_file.write_text(
        textwrap.dedent(
            """\
            import re
            from phoenix.adapters.base import BaseAdapter
            from phoenix.plugins.manifest import PluginManifest
            from phoenix.models.document import RawResponse
            from phoenix.models.output import UnifiedOutput
            from phoenix.options import ScrapingOptions
            from typing import Any

            class DemoPluginAdapter(BaseAdapter):
                @property
                def manifest(self):
                    return PluginManifest(
                        name="demo_plugin",
                        version="1.0.0",
                        platforms=["demo_plugin"],
                        url_patterns=[r"https?://demo-plugin\\.example/.+"],
                    )

                def supported_patterns(self):
                    return [re.compile(p) for p in self.manifest.url_patterns]

                async def collect(self, url, strategy, collector, options):
                    raise NotImplementedError

                async def extract(self, raw_response):
                    raise NotImplementedError

                async def normalize(self, extracted, url, strategy):
                    raise NotImplementedError
            """,
        ),
        encoding="utf-8",
    )

    loader.plugin_dirs = [plugin_dir]
    loaded = loader.load_plugin_dirs()

    assert len(loaded) == 1
    assert loaded[0].manifest.name == "demo_plugin"
    assert loader.get_adapter("demo_plugin") is loaded[0]


def test_loader_load_plugin_dirs_discovers_package(
    loader: PluginLoader,
    tmp_path: Path,
) -> None:
    """Load_plugin_dirs loads adapter packages from a directory."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    pkg_dir = plugin_dir / "demo_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text(
        textwrap.dedent(
            """\
            import re
            from phoenix.adapters.base import BaseAdapter
            from phoenix.plugins.manifest import PluginManifest

            class PkgAdapter(BaseAdapter):
                @property
                def manifest(self):
                    return PluginManifest(
                        name="pkg_adapter",
                        version="1.0.0",
                        platforms=["pkg_adapter"],
                        url_patterns=[r"https?://pkg\\.example/.+"],
                    )

                def supported_patterns(self):
                    return [re.compile(p) for p in self.manifest.url_patterns]

                async def collect(self, url, strategy, collector, options):
                    raise NotImplementedError

                async def extract(self, raw_response):
                    raise NotImplementedError

                async def normalize(self, extracted, url, strategy):
                    raise NotImplementedError
            """,
        ),
        encoding="utf-8",
    )

    loader.plugin_dirs = [plugin_dir]
    loaded = loader.load_plugin_dirs()

    assert len(loaded) == 1
    assert loaded[0].manifest.name == "pkg_adapter"


def test_loader_load_plugin_dirs_skips_broken_module(
    loader: PluginLoader,
    tmp_path: Path,
) -> None:
    """Broken plugin modules are skipped without crashing the loader."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "broken.py"
    plugin_file.write_text("raise RuntimeError('simulated')", encoding="utf-8")

    loader.plugin_dirs = [plugin_dir]
    loaded = loader.load_plugin_dirs()

    assert loaded == []


def test_loader_load_plugin_dirs_skips_broken_package(
    loader: PluginLoader,
    tmp_path: Path,
) -> None:
    """Broken plugin packages are skipped without crashing the loader."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    pkg_dir = plugin_dir / "broken_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text(
        "raise RuntimeError('simulated')",
        encoding="utf-8",
    )

    loader.plugin_dirs = [plugin_dir]
    loaded = loader.load_plugin_dirs()

    assert loaded == []


def test_loader_load_plugin_dirs_warns_for_missing_directory(
    loader: PluginLoader,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A configured plugin directory that does not exist is logged and ignored."""
    loader.plugin_dirs = [Path("/nonexistent/plugins")]

    with caplog.at_level("WARNING", logger="phoenix.plugins.loader"):
        loaded = loader.load_plugin_dirs()

    assert loaded == []
    assert "does not exist" in caplog.text


def test_loader_load_plugin_dirs_ignores_non_python_files(
    loader: PluginLoader,
    tmp_path: Path,
) -> None:
    """Non-Python files in plugin directories are ignored."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    (plugin_dir / "readme.txt").write_text("hello", encoding="utf-8")

    loader.plugin_dirs = [plugin_dir]
    loaded = loader.load_plugin_dirs()

    assert loaded == []


def test_plugin_registry_is_singleton(fresh_registry: PluginRegistry) -> None:
    """PluginRegistry follows the singleton pattern."""
    another = PluginRegistry()
    assert another is fresh_registry


def test_plugin_registry_initializes_attributes_once() -> None:
    """The registry initializes internal collections only once."""
    registry = PluginRegistry()
    registry._reset()
    registry.register(DemoAdapter())

    another = PluginRegistry()
    assert len(another.list_adapters()) == 1


def test_plugin_registry_reset_clears_adapters(fresh_registry: PluginRegistry) -> None:
    """The internal reset method clears all registered adapters."""
    loader = PluginLoader()
    loader.register(DemoAdapter())

    fresh_registry._reset()

    assert fresh_registry.list_adapters() == []
    assert fresh_registry.match_url("https://demo.example/post") is None


def test_loader_uses_singleton_registry_by_default() -> None:
    """PluginLoader instances share the default singleton registry."""
    registry = PluginRegistry()
    registry._reset()

    loader_a = PluginLoader()
    loader_b = PluginLoader()
    loader_a.register(DemoAdapter())

    assert loader_b.get_adapter("demo") is loader_a.get_adapter("demo")


def test_loader_find_adapter_classes_skips_uninstantiable(
    loader: PluginLoader,
    tmp_path: Path,
) -> None:
    """Adapter classes that fail instantiation are skipped."""
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "bad.py"
    plugin_file.write_text(
        textwrap.dedent(
            """\
            from phoenix.adapters.base import BaseAdapter
            from phoenix.plugins.manifest import PluginManifest

            class BadAdapter(BaseAdapter):
                def __init__(self):
                    raise RuntimeError("broken")

                @property
                def manifest(self):
                    return PluginManifest(
                        name="bad",
                        version="1.0.0",
                        platforms=["bad"],
                        url_patterns=[".*"],
                    )

                def supported_patterns(self):
                    return []

                async def collect(self, url, strategy, collector, options):
                    raise NotImplementedError

                async def extract(self, raw_response):
                    raise NotImplementedError

                async def normalize(self, extracted, url, strategy):
                    raise NotImplementedError
            """,
        ),
        encoding="utf-8",
    )

    loader.plugin_dirs = [plugin_dir]
    loaded = loader.load_plugin_dirs()

    assert loaded == []


def test_loader_instantiate_adapter_class_raises(loader: PluginLoader) -> None:
    """_instantiate_adapter logs and returns None when class init raises."""

    class BrokenAdapter(DemoAdapter):
        def __init__(self) -> None:
            """Raise on instantiation."""
            raise RuntimeError("broken")

    assert loader._instantiate_adapter(BrokenAdapter) is None


def test_loader_instantiate_adapter_factory_raises(loader: PluginLoader) -> None:
    """_instantiate_adapter logs and returns None when factory raises."""

    def _broken() -> DemoAdapter:
        raise RuntimeError("broken")

    assert loader._instantiate_adapter(_broken) is None


def test_loader_load_module_from_file_spec_is_none(
    loader: PluginLoader,
    tmp_path: Path,
) -> None:
    """_load_module_from_file handles spec_from_file_location returning None."""
    plugin_file = tmp_path / "dummy.py"
    plugin_file.write_text("x = 1", encoding="utf-8")

    with patch("phoenix.plugins.loader.importlib.util.spec_from_file_location", return_value=None):
        result = loader._load_module_from_file(plugin_file)

    assert result is None


def test_loader_load_module_from_file_spec_raises(
    loader: PluginLoader,
    tmp_path: Path,
) -> None:
    """_load_module_from_file handles spec creation exceptions."""
    plugin_file = tmp_path / "dummy.py"
    plugin_file.write_text("x = 1", encoding="utf-8")

    with patch(
        "phoenix.plugins.loader.importlib.util.spec_from_file_location",
        side_effect=RuntimeError("simulated"),
    ):
        result = loader._load_module_from_file(plugin_file)

    assert result is None


def test_loader_load_module_from_package_spec_is_none(
    loader: PluginLoader,
    tmp_path: Path,
) -> None:
    """_load_module_from_package handles spec_from_file_location returning None."""
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("x = 1", encoding="utf-8")

    with patch("phoenix.plugins.loader.importlib.util.spec_from_file_location", return_value=None):
        result = loader._load_module_from_package(pkg_dir)

    assert result is None


def test_loader_load_module_from_package_spec_raises(
    loader: PluginLoader,
    tmp_path: Path,
) -> None:
    """_load_module_from_package handles spec creation exceptions."""
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text("x = 1", encoding="utf-8")

    with patch(
        "phoenix.plugins.loader.importlib.util.spec_from_file_location",
        side_effect=RuntimeError("simulated"),
    ):
        result = loader._load_module_from_package(pkg_dir)

    assert result is None
