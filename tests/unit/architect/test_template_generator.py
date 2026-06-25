"""Tests for the deterministic adapter template generator."""

from __future__ import annotations

import pytest

from phoenix.adapters.base import BaseAdapter
from phoenix.architect.critic import AdapterCritic
from phoenix.architect.explorer import PageSnapshot
from phoenix.architect.template_generator import generate_adapter_code


@pytest.mark.asyncio
async def test_template_adapter_passes_critic() -> None:
    html = """
    <html>
      <div class="quote">
        <span class="text" itemprop="text">Hello world</span>
        <span class="author" itemprop="author">Alice</span>
        <div class="tags"><a class="tag" href="/tag/a/">a</a></div>
      </div>
    </html>
    """
    snapshot = PageSnapshot(url="https://example.com", html=html, page_number=1)
    code = generate_adapter_code(
        platform_name="example",
        url_patterns=[r"https?://example\.com.*"],
        fields=["quote_text", "author_name", "tags"],
        selectors={
            "quote_text": ".text[itemprop=text]",
            "author_name": ".author[itemprop=author]::text",
            "tags": ".tags a.tag::attr(href)",
        },
    )

    critic = AdapterCritic()
    report = await critic.validate(
        code,
        [snapshot],
        required_fields=["quote_text", "author_name", "tags"],
    )

    assert report.compiles is True
    assert report.execution_error is None
    assert report.score >= 0.8
    assert report.extracted_fields["quote_text"] == ["Hello world"]
    assert report.extracted_fields["author_name"] == ["Alice"]
    assert report.extracted_fields["tags"] == ["/tag/a/"]


def test_template_adapter_is_a_base_adapter_subclass() -> None:
    code = generate_adapter_code(
        platform_name="example",
        url_patterns=[r"https?://example\.com.*"],
        fields=["title"],
        selectors={"title": "h1"},
    )
    namespace: dict[str, object] = {}
    exec(code, namespace)  # noqa: S102
    adapter_class = next(
        obj
        for obj in namespace.values()
        if isinstance(obj, type) and issubclass(obj, BaseAdapter) and obj is not BaseAdapter
    )
    assert adapter_class is not None
