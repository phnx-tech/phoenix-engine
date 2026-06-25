"""End-to-end test for ``phoenix collect`` against a local mock server."""

from __future__ import annotations

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.slow]


@pytest.mark.skip(
    reason="CLI uses stub collectors in Phase 1; real HTTP collection not enabled e2e",
)
def test_cli_collect_mock_server() -> None:
    """Start a local http.server and run ``phoenix collect <url>``.

    This test is skipped until the CLI default collectors are wired to perform
    real HTTP collection. When enabled, it will serve a static HTML fixture,
    invoke ``phoenix collect``, and assert valid JSON output with
    ``result.success`` set to ``True``.
    """
