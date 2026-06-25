"""Unit tests for the AI intelligence layer."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from phoenix.intelligence import ContentClassifier, EntityResolver, SelectorRepair
from phoenix.processing.phoenix_ai_extractor import AIExtractionError, PhoenixAIExtractor

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_extractor() -> AsyncMock:
    """Return a mocked PhoenixAIExtractor."""
    mock = AsyncMock(spec=PhoenixAIExtractor)
    mock.estimated_cost_usd = 0.0
    mock.total_tokens_used = 0
    mock.total_api_calls = 0
    return mock


@pytest.mark.asyncio
async def test_classifier_classifies_content(mock_extractor: AsyncMock) -> None:
    """ContentClassifier returns platform, content_type, and confidence."""
    mock_extractor.extract.return_value = {
        "platform": "x_twitter",
        "content_type": "post",
        "confidence": 0.95,
        "reasoning": "Contains tweet-like structure",
    }
    classifier = ContentClassifier(mock_extractor)

    result = await classifier.classify("<html>tweet</html>", "https://x.com/user/status/1")

    assert result["platform"] == "x_twitter"
    assert result["content_type"] == "post"
    assert result["confidence"] == 0.95
    assert result["reasoning"]
    mock_extractor.extract.assert_awaited_once()


@pytest.mark.asyncio
async def test_classifier_defaults_on_missing_fields(mock_extractor: AsyncMock) -> None:
    """Classifier falls back to safe defaults when Phoenix AI omits fields."""
    mock_extractor.extract.return_value = {}
    classifier = ContentClassifier(mock_extractor)

    result = await classifier.classify("<html></html>", "https://example.com/")

    assert result["platform"] == "generic"
    assert result["content_type"] == "article"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_entity_resolver_extracts_entities(mock_extractor: AsyncMock) -> None:
    """EntityResolver extracts a list of entities."""
    mock_extractor.extract.return_value = {
        "entities": [
            {
                "name": "Phoenix AI",
                "type": "organization",
                "handle": "@phoenixai",
                "url": None,
                "confidence": 0.92,
            },
            {
                "name": "Sam Altman",
                "type": "person",
                "handle": "@sama",
                "url": None,
                "confidence": 0.88,
            },
        ],
    }
    resolver = EntityResolver(mock_extractor)

    entities = await resolver.extract_entities(
        "<html>Phoenix AI</html>",
        "https://x.com/",
        "x_twitter",
    )

    assert len(entities) == 2
    assert entities[0]["name"] == "Phoenix AI"
    assert entities[1]["type"] == "person"


@pytest.mark.asyncio
async def test_entity_resolver_handles_non_list_entities(mock_extractor: AsyncMock) -> None:
    """EntityResolver returns empty list when 'entities' is not a list."""
    mock_extractor.extract.return_value = {"entities": "bad"}
    resolver = EntityResolver(mock_extractor)

    entities = await resolver.extract_entities("<html></html>", "https://x.com/", "x_twitter")

    assert entities == []


@pytest.mark.asyncio
async def test_entity_resolver_resolves_match(mock_extractor: AsyncMock) -> None:
    """EntityResolver compares two entities and returns a match verdict."""
    mock_extractor.extract.return_value = {
        "match": True,
        "confidence": 0.91,
        "reasoning": "Same handle and name",
    }
    resolver = EntityResolver(mock_extractor)

    verdict = await resolver.resolve(
        {"name": "Phoenix AI", "handle": "@phoenixai"},
        {"name": "Phoenix AI", "handle": "@phoenixai"},
    )

    assert verdict["match"] is True
    assert verdict["confidence"] == 0.91
    assert verdict["reasoning"]


@pytest.mark.asyncio
async def test_selector_repair_delegates_to_extractor(mock_extractor: AsyncMock) -> None:
    """SelectorRepair calls PhoenixAIExtractor.suggest_selectors."""
    suggestions = [
        {"field": "title", "old": ".old", "new": ".new", "confidence": 0.9},
    ]
    mock_extractor.suggest_selectors.return_value = suggestions
    repair = SelectorRepair(mock_extractor)

    result = await repair.repair("<html></html>", {"title": ".old"})

    assert result == suggestions
    mock_extractor.suggest_selectors.assert_awaited_once_with("<html></html>", {"title": ".old"})


def test_phoenix_ai_extractor_enforces_budget() -> None:
    """PhoenixAIExtractor raises when the estimated cost reaches the configured cap."""
    extractor = PhoenixAIExtractor(max_budget_usd=0.01)
    extractor.estimated_cost_usd = 0.02

    with pytest.raises(AIExtractionError, match="budget exceeded"):
        extractor._check_budget()  # type: ignore[attr-defined]


def test_phoenix_ai_extractor_allows_zero_budget() -> None:
    """PhoenixAIExtractor does not enforce a cap when max_budget_usd is 0."""
    extractor = PhoenixAIExtractor(max_budget_usd=0.0)
    extractor.estimated_cost_usd = 100.0

    extractor._check_budget()  # type: ignore[attr-defined]
