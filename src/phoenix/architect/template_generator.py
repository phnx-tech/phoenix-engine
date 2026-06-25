"""Deterministic adapter generator for PhoenixArchitect.

When the LLM Coder produces fragile or invalid code, this module can generate a
simple but correct Phoenix Engine adapter directly from the Inspector spec. It
uses BeautifulSoup and the CSS selectors provided by the Inspector, normalising
common pseudo-selector syntax (``::text`` and ``::attr(name)``) at runtime.
"""

from __future__ import annotations

import re

_CSS_ATTR_RE = re.compile(
    "\\[([a-zA-Z0-9_-]+)=([^\"'\\[\\]\\s]+)\\]",
)


def _quote_attr_values(selector: str) -> str:
    """Quote unquoted attribute values so SoupSieve accepts them."""

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        value = match.group(2)
        return f'[{key}="{value}"]'

    return _CSS_ATTR_RE.sub(replacer, selector)


def _sanitize_selector(selector: str) -> str:
    """Return a selector string safe to embed in generated Python source."""
    return _quote_attr_values(selector).replace("'", "\\'")


def _field_extraction_code(fields: list[str], selectors: dict[str, str]) -> str:
    """Build the return-statement lines for the extract() method."""
    lines: list[str] = []
    for field in fields:
        selector = selectors.get(field, "")
        if not selector:
            lines.append(f"        '{field}': [],")
            lines.append(f"        '{field}_confidence': [],")
            continue
        safe = _sanitize_selector(selector)
        lines.append(f"        '{field}': _select_values(soup, '{safe}'),")
        lines.append(
            f"        '{field}_confidence': [1.0 for _ in _select_values(soup, '{safe}')],",
        )
    return "\n".join(lines)


def generate_adapter_code(
    platform_name: str,
    url_patterns: list[str],
    fields: list[str],
    selectors: dict[str, str],
) -> str:
    """Return a complete adapter module generated from ``selectors``.

    The generated adapter is intentionally simple: it parses the response HTML
    with BeautifulSoup, runs each field's CSS selector, and returns a flat dict
    of field names to lists of extracted values. ``::text`` and ``::attr(name)``
    pseudo-selectors are handled at runtime so that Inspector output can remain
    close to common scraping conventions.

    Args:
        platform_name: Snake-case platform identifier.
        url_patterns: Regex URL patterns the adapter should match.
        fields: Field names that must appear in the extracted dict.
        selectors: Mapping of field name to CSS selector.

    Returns:
        Python source code for the adapter module.
    """
    patterns_repr = repr(url_patterns)
    field_code = _field_extraction_code(fields, selectors)
    return f"""from __future__ import annotations

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
    attr_match = re.search(r"::attr\\(([^)]+)\\)$", selector)
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


class {platform_name.title().replace("_", "")}Adapter(BaseAdapter):
    manifest = PluginManifest(
        name="{platform_name}_adapter",
        version="1.0.0",
        platforms=["{platform_name}"],
        url_patterns={patterns_repr},
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
        return {{
{field_code}
        }}

    async def normalize(
        self,
        extracted: dict[str, Any],
        url: str,
        strategy: str,
    ) -> UnifiedOutput:
        return await Normalizer().normalize(extracted, "{platform_name}", url, strategy)
"""
