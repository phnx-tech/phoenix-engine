from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from phoenix.adapters.base import BaseAdapter
from phoenix.collectors.base import Collector
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.options import CollectionOptions
from phoenix.plugins.manifest import PluginManifest
from phoenix.processing.normalizer import Normalizer


def _select_values(soup: BeautifulSoup, selector: str) -> list[str]:
    attr_match = re.search(r"::attr\(([^)]+)\)$", selector)
    if attr_match:
        plain_selector = selector[: attr_match.start()]
        attribute_name = attr_match.group(1)
        return [
            str(value)
            for element in soup.select(plain_selector)
            if (value := element.get(attribute_name))
        ]
    if selector.endswith("::text"):
        plain_selector = selector[: -len("::text")]
        return [element.get_text(strip=True) for element in soup.select(plain_selector)]
    return [element.get_text(strip=True) for element in soup.select(selector)]


class QuotesToScrapeAdapter(BaseAdapter):
    manifest = PluginManifest(
        name="quotes_to_scrape_adapter",
        version="1.0.0",
        platforms=["quotes_to_scrape"],
        url_patterns=["^https://quotes.toscrape.com/$"],
        generated=True,
    )

    def supported_patterns(self) -> list[re.Pattern[str]]:
        return [re.compile(pattern) for pattern in self.manifest.url_patterns]

    async def collect(
        self,
        url: str,
        strategy: str,
        collector: Collector,
        options: CollectionOptions,
    ) -> RawResponse:
        raw_response = await collector.collect(url, options)
        if not self._is_public_content(raw_response.html):
            raise ValueError("Content is not publicly accessible")
        return raw_response

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        soup = BeautifulSoup(raw_response.html, "html.parser")
        return {
            "quote_text": _select_values(soup, '.text[itemprop="text"]'),
            "quote_text_confidence": [1.0 for _ in _select_values(soup, '.text[itemprop="text"]')],
            "author_name": _select_values(soup, '.author[itemprop="author"]::text'),
            "author_name_confidence": [
                1.0 for _ in _select_values(soup, '.author[itemprop="author"]::text')
            ],
            "tags": _select_values(soup, ".tags a.tag::attr(href)"),
            "tags_confidence": [1.0 for _ in _select_values(soup, ".tags a.tag::attr(href)")],
        }

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        return await Normalizer().normalize(extracted, "quotes_to_scrape", url, strategy)
