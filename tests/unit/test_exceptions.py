"""Unit tests for Phoenix Engine exceptions."""

from __future__ import annotations

import pytest

from phoenix.exceptions import (
    ConfigurationError,
    PhoenixError,
    ScrapingError,
    UnsupportedURLError,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "exception_class",
    [
        PhoenixError,
        ScrapingError,
        UnsupportedURLError,
        ConfigurationError,
    ],
)
def test_exceptions_are_catchable(exception_class: type[PhoenixError]) -> None:
    """All custom exceptions derive from PhoenixError."""
    with pytest.raises(PhoenixError):
        raise exception_class("boom")
