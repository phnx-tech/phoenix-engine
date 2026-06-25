"""Tests for content classifiers."""

from __future__ import annotations

import pytest

from phoenix.intelligence.classifier import HeuristicContentClassifier


@pytest.fixture
def classifier() -> HeuristicContentClassifier:
    return HeuristicContentClassifier()


def test_classify_real_estate_url(classifier: HeuristicContentClassifier) -> None:
    result = classifier.classify(
        "<html><title>Apartment for sale</title></html>",
        "https://example.com/property/123",
    )
    assert result["content_type"] == "real_estate"
    assert result["confidence"] > 0.5


def test_classify_quote_url(classifier: HeuristicContentClassifier) -> None:
    result = classifier.classify(
        "<html><title>Famous Quotes</title></html>",
        "https://quotes.toscrape.com/",
    )
    assert result["content_type"] == "quote"
    assert result["platform"] == "generic"


def test_classify_platform_by_domain(classifier: HeuristicContentClassifier) -> None:
    result = classifier.classify("<html></html>", "https://www.instagram.com/p/abc")
    assert result["platform"] == "instagram"
    assert result["confidence"] >= 0.9


def test_classify_schema_org_product(classifier: HeuristicContentClassifier) -> None:
    html = '<html><script type="application/ld+json">{"@type":"Product"}</script></html>'
    result = classifier.classify(html, "https://shop.example.com/item/1")
    assert result["content_type"] == "product"


def test_classify_low_confidence_fallback(classifier: HeuristicContentClassifier) -> None:
    result = classifier.classify("<html></html>", "https://unknown.example.com/")
    assert result["platform"] == "generic"
    assert result["confidence"] < 0.5
