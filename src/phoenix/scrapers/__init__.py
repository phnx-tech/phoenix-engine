"""Public scraping engine aliases for Architecture v2.0.0.

``phoenix.scrapers`` re-exports the collector implementations under the
scraping-oriented names used by the updated documentation.
"""

from __future__ import annotations

from phoenix.collectors import (
    BrowserCollector,
    BrowserPool,
    Collector,
    DirectCollector,
    RawResponse,
    StubCollector,
)
from phoenix.scrapers.base import HTMLScraper
from phoenix.scrapers.browser import BrowserScraper
from phoenix.scrapers.http import HTTPScraper
from phoenix.scrapers.selector_engine import SelectorEngine

__all__ = [
    "BrowserCollector",
    "BrowserPool",
    "BrowserScraper",
    "Collector",
    "DirectCollector",
    "HTMLScraper",
    "HTTPScraper",
    "RawResponse",
    "SelectorEngine",
    "StubCollector",
]
