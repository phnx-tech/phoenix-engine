"""End-to-end test for the Phoenix Engine CLI version flag."""

from __future__ import annotations

import subprocess
import sys

import pytest

from phoenix import __version__

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


def test_cli_version_subprocess() -> None:
    """``phoenix --version`` prints the package version end-to-end."""
    result = subprocess.run(
        [sys.executable, "-m", "phoenix", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert f"phoenix-engine {__version__}" in result.stdout
