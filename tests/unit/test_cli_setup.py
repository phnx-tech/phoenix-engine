"""Unit tests for the phoenix setup CLI command."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
import typer

from phoenix.cli.setup import _license_ok, _ollama_ok, _playwright_browser_installed

if TYPE_CHECKING:
    from pathlib import Path

    from phoenix.models.config import Config

pytestmark = pytest.mark.unit


def _make_playwright_context_manager(mock_playwright: MagicMock) -> MagicMock:
    """Return a mock context manager wrapping a fake Playwright instance."""
    context_manager = MagicMock()
    context_manager.__enter__.return_value = mock_playwright
    context_manager.__exit__.return_value = False
    return context_manager


def test_playwright_browser_installed_when_executable_exists(tmp_path: Path) -> None:
    """Detect an installed Chromium when the executable path exists."""
    fake_exe = tmp_path / "chromium"
    fake_exe.write_text("")

    mock_playwright = MagicMock()
    mock_playwright.chromium.executable_path = str(fake_exe)

    with patch(
        "playwright.sync_api.sync_playwright",
        return_value=_make_playwright_context_manager(mock_playwright),
    ):
        ok, message = _playwright_browser_installed()

    assert ok is True
    assert "Chromium found" in message


def test_playwright_browser_not_installed() -> None:
    """Report missing browser when executable does not exist."""
    mock_playwright = MagicMock()
    mock_playwright.chromium.executable_path = "/nonexistent/chromium"

    with patch(
        "playwright.sync_api.sync_playwright",
        return_value=_make_playwright_context_manager(mock_playwright),
    ):
        ok, message = _playwright_browser_installed()

    assert ok is False
    assert "not installed" in message.lower()


def test_ollama_ok_when_reachable() -> None:
    """Ollama check succeeds when the tags endpoint returns models."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"models": [{"name": "qwen2.5:7b"}]}
    mock_response.raise_for_status = MagicMock()

    with patch("phoenix.cli.setup.httpx.get", return_value=mock_response):
        ok, message = _ollama_ok()

    assert ok is True
    assert "qwen2.5:7b" in message


def test_ollama_ok_when_unreachable() -> None:
    """Ollama check fails when the endpoint is down."""
    import httpx

    with patch("phoenix.cli.setup.httpx.get", side_effect=httpx.ConnectError("refused")):
        ok, message = _ollama_ok()

    assert ok is False
    assert "Cannot reach Ollama" in message


def test_license_ok_when_enforcement_disabled(sample_config: Config) -> None:
    """License check passes when enforcement is disabled."""
    sample_config.license_enforcement_enabled = False
    ok, message = _license_ok(sample_config)
    assert ok is True
    assert "disabled" in message


def test_license_ok_when_key_missing(sample_config: Config) -> None:
    """License check fails when enforcement is on but no key is set."""
    sample_config.license_enforcement_enabled = True
    sample_config.license_key = None
    ok, message = _license_ok(sample_config)
    assert ok is False
    assert "no key" in message.lower()


def test_setup_command_exits_on_failure(sample_config: Config) -> None:
    """setup_command exits with code 1 if a check fails."""
    from phoenix.cli import setup

    with (
        patch("phoenix.cli.setup.Config", return_value=sample_config),
        patch("phoenix.cli.setup._playwright_browser_installed", return_value=(True, "ok")),
        patch("phoenix.cli.setup._ollama_ok", return_value=(False, "Ollama down")),
        pytest.raises(typer.Exit) as exc_info,
    ):
        setup.setup_command(skip_playwright=False, skip_ollama=False, yes=True)

    assert exc_info.value.exit_code == 1
