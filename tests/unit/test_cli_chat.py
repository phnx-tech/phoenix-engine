"""Unit tests for the phoenix chat CLI command."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import typer

from phoenix.cli.chat import _ollama_reachable

pytestmark = pytest.mark.unit


def test_ollama_reachable_when_healthy() -> None:
    """Return True when Ollama tags endpoint responds."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("phoenix.cli.chat.httpx.get", return_value=mock_response):
        assert _ollama_reachable("http://localhost:11434/v1") is True


def test_ollama_reachable_when_unhealthy() -> None:
    """Return False when Ollama tags endpoint fails."""
    import httpx

    with patch("phoenix.cli.chat.httpx.get", side_effect=httpx.ConnectError("refused")):
        assert _ollama_reachable("http://localhost:11434/v1") is False


def test_chat_command_exits_when_ollama_unreachable() -> None:
    """chat_command exits with code 1 if Ollama is not reachable."""
    from phoenix.cli import chat

    with (
        patch("phoenix.cli.chat._ollama_reachable", return_value=False),
        pytest.raises(typer.Exit) as exc_info,
    ):
        chat.chat_command(model=None)

    assert exc_info.value.exit_code == 1
