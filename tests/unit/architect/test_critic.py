"""Tests for the adapter critic."""

from __future__ import annotations

from phoenix.architect.critic import AdapterCritic
from phoenix.architect.explorer import PageSnapshot

GOOD_CODE = """
from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from phoenix.adapters.base import BaseAdapter
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.plugins.manifest import PluginManifest
from phoenix.processing.normalizer import Normalizer


class SampleAdapter(BaseAdapter):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="sample",
            version="0.1.0",
            platforms=["sample"],
            url_patterns=[r"https?://example\\.com.*"],
            generated=True,
        )

    def supported_patterns(self) -> list[re.Pattern[str]]:
        return [re.compile(p, re.IGNORECASE) for p in self.manifest.url_patterns]

    async def collect(self, url, strategy, collector, options):
        return await collector.collect(url, options)

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        soup = BeautifulSoup(raw_response.html, "html.parser")
        return {
            "title": soup.find("h1").get_text(strip=True),
            "price": soup.select_one(".price").get_text(strip=True),
        }

    async def normalize(self, extracted, url, strategy):
        return await Normalizer().normalize(extracted, "sample", url, strategy)
"""

BAD_CODE = """
class SampleAdapter:
    def extract(self, raw_response)
        return {"title": "x"}
"""


async def test_validate_compiles_and_extracts_fields() -> None:
    html = '<html><h1>Title</h1><span class="price">100</span></html>'
    snapshot = PageSnapshot(url="https://example.com", html=html, page_number=1)
    critic = AdapterCritic()
    report = await critic.validate(GOOD_CODE, [snapshot], required_fields=["title", "price"])

    assert report.compiles is True
    assert report.execution_error is None
    assert "title" not in report.missing_fields
    assert "price" not in report.missing_fields
    assert report.score > 0.7


async def test_validate_detects_syntax_error() -> None:
    snapshot = PageSnapshot(url="https://example.com", html="<html></html>", page_number=1)
    critic = AdapterCritic()
    report = await critic.validate(BAD_CODE, [snapshot], required_fields=["title"])

    assert report.compiles is False
    assert report.compile_error is not None
    assert report.score == 0.0


async def test_validate_detects_missing_fields() -> None:
    code = "class A:\n    def extract(self, r):\n        return {'title': ''}"
    snapshot = PageSnapshot(url="https://example.com", html="<html></html>", page_number=1)
    critic = AdapterCritic()
    report = await critic.validate(code, [snapshot], required_fields=["title", "price"])

    assert "price" in report.missing_fields


async def test_validate_low_score_on_execution_error() -> None:
    code = """
from phoenix.adapters.base import BaseAdapter
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.plugins.manifest import PluginManifest

class BadAdapter(BaseAdapter):
    manifest = PluginManifest(name="bad", version="1.0.0", platforms=["bad"], url_patterns=[".*"])

    def supported_patterns(self):
        import re
        return [re.compile(".*")]

    async def collect(self, url, strategy, collector, options):
        return None

    async def extract(self, raw_response: RawResponse):
        raise RuntimeError("boom")

    async def normalize(self, extracted, url, strategy):
        return UnifiedOutput(content_type="post", url=url, scraping_strategy=strategy)
"""
    snapshot = PageSnapshot(url="https://example.com", html="<html></html>", page_number=1)
    critic = AdapterCritic()
    report = await critic.validate(code, [snapshot], required_fields=["title"])

    assert report.execution_error is not None
    assert report.score < 0.6


async def test_build_fix_prompt_includes_report() -> None:
    snapshot = PageSnapshot(url="https://example.com", html="<html></html>", page_number=1)
    critic = AdapterCritic()
    report = await critic.validate("bad code", [snapshot])
    prompt = critic.build_fix_prompt("bad code", report, [snapshot])
    assert "Validation report" in prompt
    assert "bad code" in prompt
