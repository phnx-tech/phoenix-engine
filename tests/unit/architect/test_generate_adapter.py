"""Tests for PhoenixArchitect.generate_adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from phoenix.architect.critic import AdapterValidationReport
from phoenix.architect.explorer import PageSnapshot
from phoenix.architect.orchestrator import PhoenixArchitect
from phoenix.plugins.manifest import PluginManifest

if TYPE_CHECKING:
    from pathlib import Path


SAMPLE_CODE = """
from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from phoenix.adapters.base import BaseAdapter
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.plugins.manifest import PluginManifest
from phoenix.processing.normalizer import Normalizer


class QuotesAdapter(BaseAdapter):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="quotes_toscrape",
            version="0.1.0",
            platforms=["quotes_toscrape"],
            url_patterns=[r"https?://quotes\\.toscrape\\.com.*"],
            generated=True,
        )

    def supported_patterns(self) -> list[re.Pattern[str]]:
        return [re.compile(p, re.IGNORECASE) for p in self.manifest.url_patterns]

    async def collect(self, url, strategy, collector, options):
        return await collector.collect(url, options)

    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:
        soup = BeautifulSoup(raw_response.html, "html.parser")
        return {
            "title": soup.find("h1").get_text(strip=True) if soup.find("h1") else "",
            "text": "",
            "author": "",
        }

    async def normalize(self, extracted, url, strategy):
        return Normalizer().normalize(extracted, "quotes_toscrape", url, strategy)
"""


@pytest.fixture
def architect(tmp_path: Path) -> PhoenixArchitect:
    return PhoenixArchitect(writer=MagicMock(output_dir=tmp_path))


@pytest.mark.asyncio
async def test_generate_adapter_returns_existing(architect: PhoenixArchitect) -> None:
    existing = MagicMock()
    existing.manifest = PluginManifest(
        name="existing",
        version="0.1.0",
        platforms=["existing"],
        url_patterns=[r"https?://example\.com/.+"],
    )
    with patch.object(
        architect,
        "find_existing_adapter",
        return_value=existing,
    ):
        adapter, report = await architect.generate_adapter("https://example.com/")
        assert adapter is existing
        assert report.score == 1.0


@pytest.mark.asyncio
async def test_generate_adapter_registers_new_adapter(
    architect: PhoenixArchitect,
) -> None:
    snapshot = PageSnapshot(
        url="https://quotes.toscrape.com/",
        html="<html><h1>Quotes</h1></html>",
        page_number=1,
    )
    spec = {
        "platform_name": "quotes_toscrape",
        "content_type": "quote",
        "data_fields": ["title", "text", "author"],
    }
    report = AdapterValidationReport()
    report.score = 0.8
    report.extracted_fields = {"title": "Quotes", "text": "", "author": ""}

    with (
        patch.object(architect, "find_existing_adapter", return_value=None),
        patch.object(architect, "explore", new=AsyncMock(return_value=[snapshot])),
        patch.object(architect._inspector, "inspect", new=AsyncMock(return_value=spec)),
        patch.object(architect._coder, "generate", new=AsyncMock(return_value=SAMPLE_CODE)),
        patch.object(
            architect._get_critic(),
            "validate",
            new=AsyncMock(return_value=report),
        ),
    ):
        adapter, returned_report = await architect.generate_adapter(
            snapshot.url,
            persist=False,
        )

    assert adapter.manifest.name == "quotes_toscrape"
    assert returned_report.score == 0.8
    assert architect.router.get_adapter_for_url(snapshot.url) is adapter


@pytest.mark.asyncio
async def test_generate_adapter_repair_loop(architect: PhoenixArchitect) -> None:
    snapshot = PageSnapshot(
        url="https://quotes.toscrape.com/",
        html="<html><h1>Quotes</h1></html>",
        page_number=1,
    )
    spec = {"platform_name": "quotes_toscrape", "content_type": "quote"}

    bad_report = AdapterValidationReport()
    bad_report.score = 0.2
    good_report = AdapterValidationReport()
    good_report.score = 0.8
    good_report.extracted_fields = {"title": "Quotes"}

    critic = architect._get_critic()
    with (
        patch.object(architect, "find_existing_adapter", return_value=None),
        patch.object(architect, "explore", new=AsyncMock(return_value=[snapshot])),
        patch.object(architect._inspector, "inspect", new=AsyncMock(return_value=spec)),
        patch.object(architect._coder, "generate", new=AsyncMock(return_value="bad code")),
        patch.object(architect._coder, "repair", new=AsyncMock(return_value=SAMPLE_CODE)),
        patch.object(
            critic,
            "validate",
            new=AsyncMock(side_effect=[bad_report, good_report]),
        ),
    ):
        adapter, report = await architect.generate_adapter(
            snapshot.url,
            persist=False,
        )

    assert report.score == 0.8
    assert adapter.manifest.name == "quotes_toscrape"


@pytest.mark.asyncio
async def test_generate_adapter_raises_when_validation_fails(
    architect: PhoenixArchitect,
) -> None:
    snapshot = PageSnapshot(
        url="https://example.com/",
        html="<html></html>",
        page_number=1,
    )
    spec = {"platform_name": "example_com", "content_type": "generic"}
    bad_report = AdapterValidationReport()
    bad_report.score = 0.1

    with (
        patch.object(architect, "find_existing_adapter", return_value=None),
        patch.object(architect, "explore", new=AsyncMock(return_value=[snapshot])),
        patch.object(architect._inspector, "inspect", new=AsyncMock(return_value=spec)),
        patch.object(architect._coder, "generate", new=AsyncMock(return_value="bad code")),
        patch.object(architect._coder, "repair", new=AsyncMock(return_value="still bad")),
        patch.object(
            architect._get_critic(),
            "validate",
            new=AsyncMock(return_value=bad_report),
        ),
        pytest.raises(ValueError, match="failed validation"),
    ):
        await architect.generate_adapter(snapshot.url, persist=False)
