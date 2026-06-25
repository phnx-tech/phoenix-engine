"""Unit tests for the Phoenix Engine CLI."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from phoenix import __version__
from phoenix.cli.main import app

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.unit

runner = CliRunner()


def test_cli_version_flag() -> None:
    """``--version`` prints the package version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"phoenix-engine {__version__}" in result.output


def test_cli_version_command() -> None:
    """The ``version`` command prints the package version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert f"phoenix-engine {__version__}" in result.output


def test_cli_scrape_outputs_valid_json() -> None:
    """The ``scrape`` command emits valid JSON for a generic URL."""
    result = runner.invoke(
        app,
        ["scrape", "https://example.com/article/123", "--no-archive"],
    )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["url"] == "https://example.com/article/123"
    assert data["output"]["platform"] == "generic"


def test_cli_scrape_pretty_format() -> None:
    """The ``scrape`` command supports pretty-printed output."""
    result = runner.invoke(
        app,
        ["scrape", "https://example.com/article/123", "--format", "pretty", "--no-archive"],
    )

    assert result.exit_code == 0
    assert "platform" in result.output
    assert "generic" in result.output


def test_cli_scrape_writes_to_output_file(tmp_path: Path) -> None:
    """The ``scrape`` command can write results to a file."""
    output_path = tmp_path / "result.json"
    result = runner.invoke(
        app,
        [
            "scrape",
            "https://example.com/article/123",
            "--output",
            str(output_path),
            "--no-archive",
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["success"] is True


def test_cli_scrape_strategy_override() -> None:
    """The ``scrape`` command accepts a strategy override."""
    result = runner.invoke(
        app,
        [
            "scrape",
            "https://example.com/article/123",
            "--strategy",
            "http",
            "--no-archive",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["output"]["scraping_strategy"] == "http"


def test_cli_scrape_batch_outputs_summary() -> None:
    """The ``scrape-batch`` command returns aggregated results."""
    result = runner.invoke(
        app,
        [
            "scrape-batch",
            "https://example.com/1",
            "https://example.com/2",
            "--no-archive",
        ],
    )

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["count"] == 2
    assert data["successful"] == 2
    assert data["failed"] == 0


def test_cli_scrape_batch_pretty_format() -> None:
    """The ``scrape-batch`` command supports pretty-printed output."""
    result = runner.invoke(
        app,
        [
            "scrape-batch",
            "https://example.com/1",
            "https://example.com/2",
            "--no-archive",
            "--format",
            "pretty",
        ],
    )

    assert result.exit_code == 0
    assert "count" in result.output
    assert "successful" in result.output


def test_cli_scrape_batch_writes_to_output_file(tmp_path: Path) -> None:
    """The ``scrape-batch`` command can write results to a file."""
    output_path = tmp_path / "batch.json"
    result = runner.invoke(
        app,
        [
            "scrape-batch",
            "https://example.com/1",
            "https://example.com/2",
            "--no-archive",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.exists()
    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["count"] == 2


def test_cli_plugins_list_outputs_adapters() -> None:
    """The ``plugins list`` command prints built-in adapter manifests."""
    result = runner.invoke(app, ["plugins", "list"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    names = {entry["name"] for entry in data}
    assert "generic_web" in names
    assert "x_twitter" in names


def test_cli_plugins_list_includes_platforms_and_patterns() -> None:
    """Each adapter entry includes platforms and URL patterns."""
    result = runner.invoke(app, ["plugins", "list"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    generic = next(entry for entry in data if entry["name"] == "generic_web")
    assert generic["platforms"] == ["generic"]
    assert generic["url_patterns"] == ["https?://.+"]


def test_cli_config_show_outputs_effective_config() -> None:
    """The ``config show`` command prints the resolved configuration."""
    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "ai_base_url" in data
    assert data["ai_model"] == "qwen2.5:7b"


def test_cli_config_show_masks_secrets_by_default() -> None:
    """The ``config show`` command masks the API key by default."""
    result = runner.invoke(app, ["config", "show"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ai_api_key"] == "***"


def test_cli_config_show_can_reveal_secrets() -> None:
    """The ``config show --show-secrets`` command reveals the API key."""
    result = runner.invoke(app, ["config", "show", "--show-secrets"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ai_api_key"] == "ollama"
