"""Public base class for scrapers.

This module provides the documentation-facing name ``HTMLScraper`` as an
alias for the existing ``Collector`` base class.
"""

from __future__ import annotations

from phoenix.collectors.base import Collector

HTMLScraper = Collector

__all__ = ["HTMLScraper"]
