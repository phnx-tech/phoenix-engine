"""Unit tests for the configuration file loader."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from phoenix.infrastructure.config import ConfigLoader, ConfigLoadError
from phoenix.models.config import Config

if TYPE_CHECKING:
    from pathlib import Path


def test_load_json_config(tmp_path: Path) -> None:
    """JSON configuration files are loaded and merged."""
    config_path = tmp_path / "phoenix.json"
    config_path.write_text(json.dumps({"timeout": 60.0, "archive_enabled": False}))

    loader = ConfigLoader(search_paths=[tmp_path])
    data = loader.load()

    assert data["timeout"] == 60.0
    assert data["archive_enabled"] is False


def test_load_yaml_config(tmp_path: Path) -> None:
    """YAML configuration files are loaded and merged."""
    config_path = tmp_path / "phoenix.yaml"
    config_path.write_text("timeout: 45.0\nai_enabled: true\n")

    loader = ConfigLoader(search_paths=[tmp_path])
    data = loader.load()

    assert data["timeout"] == 45.0
    assert data["ai_enabled"] is True


def test_load_toml_config(tmp_path: Path) -> None:
    """TOML configuration files extract the ``[tool.phoenix]`` table."""
    config_path = tmp_path / "pyproject.toml"
    config_path.write_text("[tool.phoenix]\ntimeout = 90.0\n")

    loader = ConfigLoader(search_paths=[tmp_path])
    data = loader.load()

    assert data["timeout"] == 90.0


def test_load_config_returns_validated_config(tmp_path: Path) -> None:
    """``load_config`` returns a validated :class:`Config`."""
    config_path = tmp_path / "phoenix.json"
    config_path.write_text(json.dumps({"timeout": 60.0}))

    config = ConfigLoader(search_paths=[tmp_path]).load_config()

    assert isinstance(config, Config)
    assert config.timeout == 60.0


def test_overrides_take_precedence(tmp_path: Path) -> None:
    """Explicit overrides take precedence over file values."""
    config_path = tmp_path / "phoenix.json"
    config_path.write_text(json.dumps({"timeout": 60.0}))

    config = ConfigLoader(search_paths=[tmp_path]).load_config(
        overrides={"timeout": 15.0},
    )

    assert config.timeout == 15.0


def test_unsupported_format_raises(tmp_path: Path) -> None:
    """Unsupported configuration file formats raise ``ConfigLoadError``."""
    config_path = tmp_path / "phoenix.ini"
    config_path.write_text("[DEFAULT]\ntimeout=1\n")

    loader = ConfigLoader(search_paths=[tmp_path])

    with pytest.raises(ConfigLoadError):
        loader._load_file(config_path)
