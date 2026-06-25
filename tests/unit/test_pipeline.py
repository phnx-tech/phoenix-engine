"""Unit tests for the Phoenix Engine pipeline controller."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from phoenix.collectors.base import Collector, StubCollector
from phoenix.exceptions import RetryableError
from phoenix.infrastructure.storage import SQLiteStorageBackend
from phoenix.intelligence.change_detector import ChangeDetector
from phoenix.models import Config, ScrapingOptions
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput
from phoenix.pipeline import PipelineController
from phoenix.processing.ai_assistant import AIAssistant
from phoenix.processing.domain_memory import DomainMemory
from phoenix.processing.html_extractor import HTMLExtractor
from phoenix.processing.normalizer import Normalizer
from phoenix.router import URLRouter
from phoenix.strategy_selector import StrategySelector

pytestmark = pytest.mark.unit

URL = "https://example.com/article/123"


@pytest.fixture
def pipeline() -> PipelineController:
    """Return a pipeline wired with real router/selector and stub collector."""
    config = Config()
    router = URLRouter()
    selector = StrategySelector(config)
    collectors: dict[str, Collector] = {"http": StubCollector(strategy="http")}
    return PipelineController(
        router=router,
        strategy_selector=selector,
        collectors=collectors,
        html_extractor=HTMLExtractor(),
        normalizer=Normalizer(),
        config=config,
    )


@pytest.fixture
def raw_response() -> RawResponse:
    """Return a sample raw response."""
    return RawResponse(
        url=URL,
        final_url=URL,
        status_code=200,
        headers={"content-type": "text/html"},
        html="<html><head><title>Test</title></head><body><p>Hello</p></body></html>",
        strategy="http",
        timestamp=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_pipeline_success_path(pipeline: PipelineController) -> None:
    """Pipeline returns a successful ScrapingResult."""
    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is True
    assert result.url == URL
    assert result.output is not None
    assert isinstance(result.output, UnifiedOutput)
    assert result.output.platform == "generic"
    assert result.diagnostics is not None
    assert result.diagnostics.strategies_attempted == ["http"]
    assert "fetch" in result.timing_ms


@pytest.mark.asyncio
async def test_pipeline_fallback_path(raw_response: RawResponse) -> None:
    """Pipeline falls back to the secondary collector when primary fails."""
    config = Config()
    router = URLRouter()
    selector = StrategySelector(config)

    http_collector = AsyncMock(spec=Collector)
    http_collector.collect = AsyncMock(side_effect=RetryableError("HTTP timeout"))
    browser_collector = AsyncMock(spec=Collector)
    browser_collector.collect = AsyncMock(return_value=raw_response)

    collectors: dict[str, Collector] = {
        "http": http_collector,
        "browser": browser_collector,
    }
    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors=collectors,
        html_extractor=HTMLExtractor(),
        normalizer=Normalizer(),
        config=config,
    )

    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is True
    assert result.fallback_triggered is True
    assert result.output is not None
    assert result.output.scraping_strategy == "http"
    http_collector.collect.assert_awaited_once()
    browser_collector.collect.assert_awaited_once()


@pytest.mark.asyncio
async def test_pipeline_retry_path(raw_response: RawResponse) -> None:
    """Pipeline retries retryable errors with exponential backoff."""
    config = Config()
    router = URLRouter()
    selector = StrategySelector(config)

    http_collector = AsyncMock(spec=Collector)
    http_collector.collect = AsyncMock(
        side_effect=[RetryableError("timeout"), raw_response],
    )

    collectors: dict[str, Collector] = {"http": http_collector}
    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors=collectors,
        html_extractor=HTMLExtractor(),
        normalizer=Normalizer(),
        config=config,
    )

    result = await pipeline.execute(URL, ScrapingOptions(max_retries=2))

    assert result.success is True
    assert http_collector.collect.await_count == 2
    assert result.diagnostics is not None
    assert result.diagnostics.retries == 1


@pytest.mark.asyncio
async def test_pipeline_output_includes_confidence(pipeline: PipelineController) -> None:
    """Successful output includes field and overall confidence scores."""
    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is True
    assert result.output is not None
    assert "title" in result.output.field_confidences
    assert "text" in result.output.field_confidences
    assert 0.0 <= result.output.confidence <= 1.0


@pytest.mark.asyncio
async def test_pipeline_records_throttle_outcomes(raw_response: RawResponse) -> None:
    """The pipeline feeds collection outcomes back to the rate limiter."""
    config = Config()
    router = URLRouter()
    selector = StrategySelector(config)
    rate_limiter = AsyncMock()

    http_collector = AsyncMock(spec=Collector)
    http_collector.collect = AsyncMock(side_effect=RetryableError("HTTP timeout"))
    browser_collector = AsyncMock(spec=Collector)
    browser_collector.collect = AsyncMock(return_value=raw_response)

    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors={"http": http_collector, "browser": browser_collector},
        html_extractor=HTMLExtractor(),
        normalizer=Normalizer(),
        config=config,
        rate_limiter=rate_limiter,
    )

    await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert rate_limiter.record_outcome.await_count == 2


@pytest.mark.asyncio
async def test_pipeline_all_strategies_exhausted(pipeline: PipelineController) -> None:
    """Pipeline returns an error result when all strategies fail."""
    config = Config()
    router = URLRouter()
    selector = StrategySelector(config)

    failing_collector = AsyncMock(spec=Collector)
    failing_collector.collect = AsyncMock(side_effect=RetryableError("always fails"))

    collectors: dict[str, Collector] = {
        "http": failing_collector,
        "browser": failing_collector,
    }
    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors=collectors,
        html_extractor=HTMLExtractor(),
        normalizer=Normalizer(),
        config=config,
    )

    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is False
    assert result.error is not None
    assert result.error["code"] == "SCR_011"


@pytest.mark.asyncio
async def test_pipeline_unsupported_url(pipeline: PipelineController) -> None:
    """Pipeline gracefully returns an error for unsupported URLs."""
    result = await pipeline.execute("not-a-url", ScrapingOptions(max_retries=0))

    assert result.success is False
    assert result.error is not None
    assert result.error["code"] == "SCR_001"


@pytest.mark.asyncio
async def test_pipeline_diagnostics_accumulated(pipeline: PipelineController) -> None:
    """Diagnostics include timing, strategies attempted, and selectors tried."""
    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.diagnostics is not None
    diagnostics = result.diagnostics
    assert diagnostics.url == URL
    assert diagnostics.platform == "generic"
    assert diagnostics.primary_strategy == "http"
    assert diagnostics.strategies_attempted == ["http"]
    assert diagnostics.html_size_bytes > 0
    assert "classify" in diagnostics.timing
    assert "fetch" in diagnostics.timing


@pytest.mark.asyncio
async def test_pipeline_handles_unexpected_exception() -> None:
    """Pipeline returns an error result for unexpected exceptions."""
    config = Config()
    router = URLRouter()
    selector = StrategySelector(config)
    collector = AsyncMock(spec=Collector)
    collector.collect = AsyncMock(side_effect=RuntimeError("boom"))

    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors={"http": collector},
        html_extractor=HTMLExtractor(),
        normalizer=Normalizer(),
        config=config,
    )

    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is False
    assert result.error is not None
    assert result.error["code"] == "SCR_099"
    assert "boom" in result.error["message"]


@pytest.mark.asyncio
async def test_pipeline_skips_unknown_strategy(raw_response: RawResponse) -> None:
    """Pipeline skips strategies that have no matching collector."""
    config = Config()
    router = URLRouter()
    selector = StrategySelector(config)
    collector = AsyncMock(spec=Collector)
    collector.collect = AsyncMock(return_value=raw_response)

    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors={"http": collector},
        html_extractor=HTMLExtractor(),
        normalizer=Normalizer(),
        config=config,
    )

    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is True


@pytest.mark.asyncio
async def test_pipeline_ai_merge_ignores_selectors_used(
    raw_response: RawResponse,
) -> None:
    """AI fallback ignores selectors_used from AI data."""
    config = Config(ai_enabled=True)
    router = URLRouter()
    selector = StrategySelector(config)

    html_extractor = AsyncMock()
    html_extractor.extract = AsyncMock(
        return_value={
            "title": None,
            "text": "",
            "author": None,
            "selectors_used": [".selector"],
        },
    )

    ai_assistant = AsyncMock(spec=AIAssistant)
    ai_assistant.extract = AsyncMock(
        return_value={
            "title": "AI Title",
            "selectors_used": [".ai-selector"],
        },
    )
    extractor_mock = MagicMock()
    extractor_mock.total_tokens_used = 7
    ai_assistant.extractor = extractor_mock

    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors={"http": StubCollector(strategy="http")},
        html_extractor=html_extractor,
        normalizer=Normalizer(),
        config=config,
        ai_assistant=ai_assistant,
    )

    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is True
    assert result.output is not None
    assert result.output.selectors_used == [".selector"]


@pytest.mark.asyncio
async def test_pipeline_ai_fallback_when_extraction_incomplete(
    raw_response: RawResponse,
) -> None:
    """Pipeline calls AIAssistant when selectors return no critical fields."""
    config = Config(ai_enabled=True)
    router = URLRouter()
    selector = StrategySelector(config)

    html_extractor = AsyncMock()
    html_extractor.extract = AsyncMock(
        return_value={
            "title": None,
            "text": "",
            "author": None,
            "selectors_used": [".missing"],
        },
    )

    ai_assistant = AsyncMock(spec=AIAssistant)
    ai_assistant.extract = AsyncMock(
        return_value={"title": "AI Title", "author": "AI Author"},
    )
    extractor_mock = MagicMock()
    extractor_mock.total_tokens_used = 42
    ai_assistant.extractor = extractor_mock

    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors={"http": StubCollector(strategy="http")},
        html_extractor=html_extractor,
        normalizer=Normalizer(),
        config=config,
        ai_assistant=ai_assistant,
    )

    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is True
    assert result.ai_assisted is True
    assert result.output is not None
    assert result.output.title == "AI Title"
    assert result.output.author == "AI Author"
    assert result.diagnostics is not None
    assert result.diagnostics.ai_assisted is True
    assert result.diagnostics.ai_model == config.ai_model
    assert result.diagnostics.ai_tokens_used == 42
    ai_assistant.extract.assert_awaited_once()


@pytest.mark.asyncio
async def test_pipeline_ai_not_triggered_when_disabled(
    raw_response: RawResponse,
) -> None:
    """Pipeline skips AI fallback when ai_enabled is False."""
    config = Config(ai_enabled=False)
    router = URLRouter()
    selector = StrategySelector(config)

    html_extractor = AsyncMock()
    html_extractor.extract = AsyncMock(
        return_value={
            "title": None,
            "text": "",
            "author": None,
            "selectors_used": [".missing"],
        },
    )

    ai_assistant = AsyncMock(spec=AIAssistant)

    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors={"http": StubCollector(strategy="http")},
        html_extractor=html_extractor,
        normalizer=Normalizer(),
        config=config,
        ai_assistant=ai_assistant,
    )

    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is True
    assert result.ai_assisted is False
    ai_assistant.extract.assert_not_awaited()


@pytest.mark.asyncio
async def test_pipeline_ai_not_triggered_when_fields_present(
    raw_response: RawResponse,
) -> None:
    """Pipeline skips AI fallback when selector extraction is complete."""
    config = Config(ai_enabled=True)
    router = URLRouter()
    selector = StrategySelector(config)

    html_extractor = AsyncMock()
    html_extractor.extract = AsyncMock(
        return_value={
            "title": "Selector Title",
            "text": "Selector text",
            "author": "Selector Author",
            "selectors_used": ["h1"],
        },
    )

    ai_assistant = AsyncMock(spec=AIAssistant)

    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors={"http": StubCollector(strategy="http")},
        html_extractor=html_extractor,
        normalizer=Normalizer(),
        config=config,
        ai_assistant=ai_assistant,
    )

    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is True
    assert result.ai_assisted is False
    assert result.output is not None
    assert result.output.title == "Selector Title"
    ai_assistant.extract.assert_not_awaited()


@pytest.mark.asyncio
async def test_pipeline_ai_merge_preserves_selector_values(
    raw_response: RawResponse,
) -> None:
    """AI fallback only fills missing fields and preserves selector values."""
    config = Config(ai_enabled=True)
    router = URLRouter()
    selector = StrategySelector(config)

    html_extractor = AsyncMock()
    html_extractor.extract = AsyncMock(
        return_value={
            "title": "Selector Title",
            "text": "",
            "author": None,
            "selectors_used": ["h1"],
        },
    )

    ai_assistant = AsyncMock(spec=AIAssistant)
    ai_assistant.extract = AsyncMock(
        return_value={
            "title": "AI Title",
            "author": "AI Author",
            "text": "AI Text",
        },
    )
    extractor_mock = MagicMock()
    extractor_mock.total_tokens_used = 10
    ai_assistant.extractor = extractor_mock

    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors={"http": StubCollector(strategy="http")},
        html_extractor=html_extractor,
        normalizer=Normalizer(),
        config=config,
        ai_assistant=ai_assistant,
    )

    result = await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    assert result.success is True
    assert result.ai_assisted is True
    assert result.output is not None
    assert result.output.title == "Selector Title"
    assert result.output.author == "AI Author"
    assert result.output.text == "AI Text"


@pytest.mark.asyncio
async def test_pipeline_records_domain_memory_success(raw_response: RawResponse) -> None:
    """A successful scrape records domain memory."""
    config = Config()
    router = URLRouter()
    selector = StrategySelector(config)
    domain_memory = AsyncMock(spec=DomainMemory)

    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors={"http": StubCollector(strategy="http", html=raw_response.html)},
        html_extractor=HTMLExtractor(),
        normalizer=Normalizer(),
        config=config,
        domain_memory=domain_memory,
    )

    await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    domain_memory.record_success.assert_awaited_once()


@pytest.mark.asyncio
async def test_pipeline_records_domain_memory_failure() -> None:
    """A failed scrape records domain memory failure."""
    config = Config()
    router = URLRouter()
    selector = StrategySelector(config)
    domain_memory = AsyncMock(spec=DomainMemory)

    failing_collector = AsyncMock(spec=Collector)
    failing_collector.collect = AsyncMock(side_effect=RetryableError("always fails"))

    pipeline = PipelineController(
        router=router,
        strategy_selector=selector,
        collectors={"http": failing_collector},
        html_extractor=HTMLExtractor(),
        normalizer=Normalizer(),
        config=config,
        domain_memory=domain_memory,
    )

    await pipeline.execute(URL, ScrapingOptions(max_retries=0))

    domain_memory.record_failure.assert_awaited_once()


@pytest.mark.asyncio
async def test_pipeline_attaches_change_alert(raw_response: RawResponse) -> None:
    """A structural change alert is attached to diagnostics."""
    config = Config()
    router = URLRouter()
    selector = StrategySelector(config)
    storage = SQLiteStorageBackend(path=":memory:")
    try:
        change_detector = ChangeDetector(storage=storage, config=config)

        # First scrape establishes the baseline.
        pipeline = PipelineController(
            router=router,
            strategy_selector=selector,
            collectors={"http": StubCollector(strategy="http", html=raw_response.html)},
            html_extractor=HTMLExtractor(),
            normalizer=Normalizer(),
            config=config,
            change_detector=change_detector,
        )
        await pipeline.execute(URL, ScrapingOptions(max_retries=0))

        # Second scrape with a different structure triggers an alert.
        changed_html = "<html><body><div><h1>Title</h1></div></body></html>"
        pipeline2 = PipelineController(
            router=router,
            strategy_selector=selector,
            collectors={"http": StubCollector(strategy="http", html=changed_html)},
            html_extractor=HTMLExtractor(),
            normalizer=Normalizer(),
            config=config,
            change_detector=change_detector,
        )
        result = await pipeline2.execute(URL, ScrapingOptions(max_retries=0))

        assert result.diagnostics is not None
        assert result.diagnostics.change_alert is not None
        assert "structural_change" in result.diagnostics.change_alert["alert_type"]
    finally:
        storage.close()
