"""Tests for the content normalizer."""

from __future__ import annotations

import pytest

from phoenix.processing.normalizer import Normalizer


@pytest.mark.asyncio
async def test_normalize_computes_field_confidences() -> None:
    normalizer = Normalizer()
    extracted = {
        "title": "Hello",
        "text": "",
        "author": None,
        "title_confidence": 1.0,
        "text_confidence": 0.0,
    }
    output = await normalizer.normalize(extracted, "generic", "https://example.com", "http")

    assert output.field_confidences == {
        "title": 1.0,
        "text": 0.0,
        "author": 0.0,
    }
    assert output.confidence == pytest.approx(1 / 3, rel=1e-3)


@pytest.mark.asyncio
async def test_normalize_applies_fallback_penalty() -> None:
    normalizer = Normalizer()
    extracted = {"title": "Hello", "text": "World"}
    output = await normalizer.normalize(
        extracted,
        "generic",
        "https://example.com",
        "browser",
        fallback_triggered=True,
    )

    assert output.confidence == pytest.approx(0.8, rel=1e-3)


@pytest.mark.asyncio
async def test_normalize_applies_ai_assisted_penalty() -> None:
    normalizer = Normalizer()
    extracted = {"title": "Hello"}
    output = await normalizer.normalize(
        extracted,
        "generic",
        "https://example.com",
        "http",
        ai_assisted=True,
    )

    assert output.confidence == pytest.approx(0.8, rel=1e-3)
