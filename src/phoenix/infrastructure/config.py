"""Configuration loader for Phoenix Engine.

Supplements the environment-based :class:`~phoenix.models.config.Config` with
optional YAML/JSON/TOML configuration files. Values loaded from files are
merged with environment variables, with environment variables taking precedence.
"""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from phoenix.models.config import Config


class ConfigLoader:
    """Loads configuration from files and merges with environment variables."""

    DEFAULT_FILENAMES = (
        "phoenix.json",
        "phoenix.yaml",
        "phoenix.yml",
        "pyproject.toml",
    )

    def __init__(self, search_paths: list[str | Path] | None = None) -> None:
        """Initialize the loader.

        Args:
            search_paths: Directories to search for configuration files. When
                ``None``, the current working directory and ``~/.phoenix`` are
                searched.
        """
        if search_paths is None:
            search_paths = [Path.cwd(), Path.home() / ".phoenix"]
        self._search_paths = [Path(p) for p in search_paths]

    def _find_files(self) -> list[Path]:
        """Return existing configuration files in search order."""
        files: list[Path] = []
        for directory in self._search_paths:
            for name in self.DEFAULT_FILENAMES:
                candidate = directory / name
                if candidate.exists():
                    files.append(candidate)
        return files

    @staticmethod
    def _load_file(path: Path) -> dict[str, Any]:
        """Parse a configuration file and return its contents as a dict."""
        suffix = path.suffix.lower()
        text = path.read_text(encoding="utf-8")
        if suffix == ".json":
            data: dict[str, Any] = json.loads(text)
            return data
        if suffix in {".yaml", ".yml"}:
            loaded = yaml.safe_load(text) or {}
            return loaded if isinstance(loaded, dict) else {}
        if suffix == ".toml":
            return ConfigLoader._load_toml(text)
        raise ConfigLoadError(f"Unsupported config file format: {path}")

    @staticmethod
    def _load_toml(text: str) -> dict[str, Any]:
        """Load a TOML string, extracting a ``[tool.phoenix]`` table if present."""
        data = tomllib.loads(text)
        tool_table = data.get("tool", {})
        phoenix_table = tool_table.get("phoenix", {})
        return phoenix_table if isinstance(phoenix_table, dict) else {}

    def load(self) -> dict[str, Any]:
        """Load and merge configuration files.

        Later files override earlier files. Environment variables are not
        merged here; :class:`~phoenix.models.config.Config` reads them directly.

        Returns:
            Merged dictionary of configuration values.
        """
        merged: dict[str, Any] = {}
        for path in self._find_files():
            data = self._load_file(path)
            if isinstance(data, dict):
                merged.update(data)
        return merged

    def load_config(self, overrides: dict[str, Any] | None = None) -> Config:
        """Return a validated :class:`Config` from files and overrides.

        Args:
            overrides: Dictionary of values that take precedence over files and
                environment variables.

        Returns:
            Validated application configuration.
        """
        file_values = self.load()
        overrides = dict(overrides) if overrides is not None else {}
        # Apply explicit overrides on top of file values. Pydantic-settings
        # environment variables still take precedence over file values when
        # constructing Config, so we only inject values not already present.
        for key, value in file_values.items():
            env_key = f"PHOENIX_{key.upper()}"
            if key not in overrides and env_key not in os.environ:
                overrides[key] = value
        return Config(**overrides)


class ConfigLoadError(Exception):
    """Raised when a configuration file cannot be loaded."""


def load_config(
    search_paths: list[str | Path] | None = None,
    overrides: dict[str, Any] | None = None,
) -> Config:
    """Convenience shortcut to load a :class:`Config` from files.

    Args:
        search_paths: Optional directories to search for configuration files.
        overrides: Dictionary of explicit values that override files and env.

    Returns:
        Validated application configuration.
    """
    return ConfigLoader(search_paths=search_paths).load_config(overrides=overrides)


__all__ = ["ConfigLoadError", "ConfigLoader", "load_config"]
