"""Unit tests for the ``python -m phoenix`` entry point."""

from __future__ import annotations

import subprocess
import sys

import pytest

pytestmark = pytest.mark.unit


def test_module_entry_point_no_args_exits_with_help() -> None:
    """Running the module with no args prints help and exits."""
    result = subprocess.run(
        [sys.executable, "-m", "phoenix"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2  # typer no_args_is_help exit code
