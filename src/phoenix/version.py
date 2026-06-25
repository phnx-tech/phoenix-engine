"""Version information for Phoenix Engine."""

from __future__ import annotations

try:
    from importlib.metadata import PackageNotFoundError, version

    __version__ = version("phoenix-engine")
except (ImportError, PackageNotFoundError):  # pragma: no cover
    try:
        from phoenix._version import version as __version__  # type: ignore[no-redef]
    except ImportError:  # pragma: no cover
        __version__ = "unknown"

__all__ = ["__version__"]
