"""Public HTTP scraper alias."""

from __future__ import annotations

from phoenix.collectors.direct import DirectCollector

HTTPScraper = DirectCollector

__all__ = ["HTTPScraper"]
