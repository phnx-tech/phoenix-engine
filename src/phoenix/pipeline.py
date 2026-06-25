"""Pipeline controller for Phoenix Engine.

Orchestrates URL classification, strategy selection, collection, extraction,
normalization, and diagnostics for a single scrape operation.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from phoenix.exceptions import AntiBotDetectedError, RetryableError, UnsupportedURLError
from phoenix.models import Config, Diagnostics, ScrapingOptions, ScrapingResult

if TYPE_CHECKING:
    from phoenix.collectors.base import Collector
    from phoenix.infrastructure.audit_logger import AuditLogger
    from phoenix.infrastructure.rate_limiter import RateLimiter
    from phoenix.infrastructure.storage import StorageBackend
    from phoenix.intelligence.change_detector import ChangeDetector
    from phoenix.models.classification import URLClassification
    from phoenix.models.document import RawResponse
    from phoenix.models.strategy import StrategySelection
    from phoenix.processing.ai_assistant import AIAssistant
    from phoenix.processing.archiver import SourceArchiver
    from phoenix.processing.domain_memory import DomainMemory
    from phoenix.processing.html_extractor import HTMLExtractor
    from phoenix.processing.normalizer import Normalizer
    from phoenix.router import URLRouter
    from phoenix.strategy_selector import StrategySelector


class PipelineController:
    """Coordinates the full collection pipeline."""

    def __init__(  # noqa: PLR0913
        self,
        router: URLRouter,
        strategy_selector: StrategySelector,
        collectors: dict[str, Collector],
        html_extractor: HTMLExtractor,
        normalizer: Normalizer,
        config: Config,
        ai_assistant: AIAssistant | None = None,
        storage: StorageBackend | None = None,
        archiver: SourceArchiver | None = None,
        rate_limiter: RateLimiter | None = None,
        domain_memory: DomainMemory | None = None,
        change_detector: ChangeDetector | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        """Initialize the pipeline controller.

        Args:
            router: URL router for platform classification.
            strategy_selector: Strategy selector for HTTP vs browser.
            collectors: Mapping of strategy name to ``Collector`` instance.
            html_extractor: Extractor for structured data from HTML.
            normalizer: Normalizer for unified output.
            config: Application configuration.
            ai_assistant: Optional AI assistant for extraction fallback.
            storage: Optional persistent storage backend for results.
            archiver: Optional source archiver for raw HTML.
            rate_limiter: Optional rate limiter for adaptive throttling feedback.
            domain_memory: Optional persistent learning memory.
            change_detector: Optional structural drift detector.
            audit_logger: Optional audit logger for alerts and events.
        """
        self.router = router
        self.strategy_selector = strategy_selector
        self.collectors = collectors
        self.html_extractor = html_extractor
        self.normalizer = normalizer
        self.config = config
        self.ai_assistant = ai_assistant
        self.storage = storage
        self.archiver = archiver
        self.rate_limiter = rate_limiter
        self.domain_memory = domain_memory
        self.change_detector = change_detector
        self.audit_logger = audit_logger

    async def execute(  # noqa: PLR0915
        self,
        url: str,
        options: ScrapingOptions | None = None,
    ) -> ScrapingResult:
        """Execute the collection pipeline for ``url``.

        Args:
            url: Target URL.
            options: Optional collection options.

        Returns:
            ``ScrapingResult`` with output or error details.
        """
        options = options or ScrapingOptions()
        diagnostics = Diagnostics(url=url)
        timing: dict[str, float] = {}
        selectors_used: list[str] = []
        strategies_attempted: list[str] = []
        fallback_triggered = False
        classification_url = url
        ai_assisted = False
        learn_from_run = options.strategy is None

        try:
            classification, classify_ms = self._classify_url(url)
            classification_url = classification.url
            diagnostics.platform = classification.platform
            timing["classify"] = classify_ms

            selection, select_ms = await self._select_strategy(
                classification,
                options,
            )
            diagnostics.primary_strategy = selection.primary
            timing["select"] = select_ms

            raw_response, strategy_error, fetch_ms = await self._fetch_with_fallbacks(
                classification,
                selection,
                options,
                diagnostics,
                strategies_attempted,
            )
            timing["fetch"] = fetch_ms

            if raw_response is None:
                error = self._build_error(
                    classification_url,
                    strategy_error,
                    strategies_attempted,
                    selectors_used,
                )
                await self._record_failure(
                    classification_url,
                    strategies_attempted,
                    error,
                    learn=learn_from_run,
                )
                diagnostics.timing = timing
                return ScrapingResult(
                    success=False,
                    url=classification_url,
                    error=error,
                    diagnostics=diagnostics,
                    timing_ms=_float_to_int_ms(timing),
                )

            fallback_triggered = len(strategies_attempted) > 1

            extracted, extract_ms = await self._extract(
                raw_response,
                classification,
                diagnostics,
            )
            selectors_used = list(extracted.get("selectors_used", []))
            diagnostics.selectors_tried = selectors_used
            timing["extract"] = extract_ms
            ai_assisted = diagnostics.ai_assisted

            adapter = self.router.get_adapter_for_url(classification.url)
            output, normalize_ms = await self._normalize(
                extracted,
                classification,
                raw_response,
                adapter=adapter,
                fallback_triggered=fallback_triggered,
                ai_assisted=ai_assisted,
            )
            timing["normalize"] = normalize_ms

            archived_path: str | None = None
            archive_id: str | None = None
            if options.archive and self.archiver is not None:
                archive_id = await self._archive_raw_html(
                    classification_url,
                    raw_response,
                    diagnostics,
                )
                output.archive_id = archive_id

            if learn_from_run:
                self.strategy_selector.record_success(classification_url, raw_response.strategy)

                if self.domain_memory is not None:
                    await self.domain_memory.record_success(
                        classification_url,
                        raw_response.strategy,
                        extracted,
                        output,
                    )

            if self.change_detector is not None:
                alert = await self.change_detector.detect(
                    url=classification_url,
                    platform=classification.platform,
                    content_type=classification.content_type,
                    raw_response=raw_response,
                    extracted=extracted,
                    output=output,
                    archive_id=archive_id,
                )
                if alert is not None:
                    diagnostics.change_alert = alert.model_dump(mode="json")
                    if self.audit_logger is not None:
                        self.audit_logger.log_alert(alert)

            result = ScrapingResult(
                success=True,
                url=classification_url,
                output=output,
                selectors_used=selectors_used,
                fallback_triggered=fallback_triggered,
                ai_assisted=ai_assisted,
                diagnostics=diagnostics,
                timing_ms=_float_to_int_ms(timing),
                archived_path=archived_path,
                adapter_confidence=adapter.manifest.confidence if adapter is not None else None,
            )

            if self.storage is not None:
                await self._persist_result(result, raw_response, archive_id)

            diagnostics.timing = timing
        except UnsupportedURLError as exc:
            error = self._build_error(url, exc, strategies_attempted, selectors_used)
            await self._record_failure(
                url,
                strategies_attempted,
                error,
                learn=learn_from_run,
            )
            diagnostics.timing = timing
            return ScrapingResult(
                success=False,
                url=classification_url,
                error=error,
                diagnostics=diagnostics,
                timing_ms=_float_to_int_ms(timing),
            )
        except Exception as exc:
            error = self._build_error(url, exc, strategies_attempted, selectors_used)
            await self._record_failure(
                url,
                strategies_attempted,
                error,
                learn=learn_from_run,
            )
            diagnostics.timing = timing
            return ScrapingResult(
                success=False,
                url=classification_url,
                error=error,
                diagnostics=diagnostics,
                timing_ms=_float_to_int_ms(timing),
            )
        else:
            return result

    def _classify_url(self, url: str) -> tuple[URLClassification, float]:
        """Classify ``url`` and return classification with timing."""
        start = time.perf_counter()
        classification = self.router.classify(url)
        return classification, _elapsed_ms(start)

    async def _select_strategy(
        self,
        classification: URLClassification,
        options: ScrapingOptions,
    ) -> tuple[StrategySelection, float]:
        """Select strategy for ``classification`` and return with timing."""
        start = time.perf_counter()
        selection = await self.strategy_selector.select(
            classification.url,
            classification.platform,
            user_override=options.strategy,
        )
        return selection, _elapsed_ms(start)

    async def _fetch_with_fallbacks(
        self,
        classification: URLClassification,
        selection: StrategySelection,
        options: ScrapingOptions,
        diagnostics: Diagnostics,
        strategies_attempted: list[str],
    ) -> tuple[RawResponse | None, Exception | None, float]:
        """Try primary and fallback collectors."""
        start = time.perf_counter()
        raw_response: RawResponse | None = None
        last_error: Exception | None = None
        ordered_strategies = [selection.primary, *selection.fallbacks]
        domain = urlparse(classification.url).netloc or classification.url

        for strategy in ordered_strategies:
            strategies_attempted.append(strategy)
            diagnostics.strategies_attempted = strategies_attempted

            collector = self.collectors.get(strategy)
            if collector is None:
                continue

            attempt_start = time.perf_counter()
            try:
                raw_response = await self._collect_with_retry(
                    collector,
                    classification.url,
                    options,
                    diagnostics,
                )
                latency_ms = raw_response.metadata.get(
                    "response_time_ms",
                    _elapsed_ms(attempt_start),
                )
                await self._record_throttle_outcome(
                    domain,
                    latency_ms=latency_ms,
                    status_code=raw_response.status_code,
                    error=None,
                )
                diagnostics.http_status = raw_response.status_code
                diagnostics.response_headers = dict(raw_response.headers)
                diagnostics.html_size_bytes = len(raw_response.html.encode("utf-8"))
                break
            except Exception as exc:
                last_error = exc
                latency_ms = _elapsed_ms(attempt_start)
                await self._record_throttle_outcome(
                    domain,
                    latency_ms=latency_ms,
                    status_code=None,
                    error=exc,
                )
                continue

        return raw_response, last_error, _elapsed_ms(start)

    async def _record_throttle_outcome(
        self,
        domain: str,
        *,
        latency_ms: float,
        status_code: int | None,
        error: Exception | None,
    ) -> None:
        """Feed collection outcomes back into the rate limiter."""
        if self.rate_limiter is None:
            return
        await self.rate_limiter.record_outcome(
            domain,
            latency_ms=latency_ms,
            status_code=status_code,
            error=error,
        )

    async def _record_failure(
        self,
        url: str,
        strategies_attempted: list[str],
        error: dict[str, Any],
        *,
        learn: bool,
    ) -> None:
        """Feed a failed scrape into the domain memory."""
        if not learn or self.domain_memory is None:
            return
        strategy = strategies_attempted[-1] if strategies_attempted else ""
        await self.domain_memory.record_failure(url, strategy, error)

    async def _extract(
        self,
        raw_response: RawResponse,
        classification: URLClassification,
        diagnostics: Diagnostics,
    ) -> tuple[dict[str, Any], float]:
        """Extract structured data and return with timing."""
        start = time.perf_counter()
        adapter = self.router.get_adapter_for_url(classification.url)
        if adapter is not None and adapter.manifest.generated:
            extracted = await adapter.extract(raw_response)
        else:
            extracted = await self.html_extractor.extract(
                raw_response,
                classification.platform,
            )
        if self._should_use_ai_fallback(extracted) and self.ai_assistant is not None:
            ai_extracted = await self._run_ai_extraction(
                raw_response,
                classification,
                self.ai_assistant,
                diagnostics,
            )
            extracted = self._merge_ai_fields(extracted, ai_extracted)
        return extracted, _elapsed_ms(start)

    def _should_use_ai_fallback(self, extracted: dict[str, Any]) -> bool:
        """Return True when AI fallback is enabled and critical fields are missing."""
        if not self.config.ai_enabled or self.ai_assistant is None:
            return False
        critical = [extracted.get("text"), extracted.get("title"), extracted.get("author")]
        return any(
            value is None or (isinstance(value, str) and value.strip() == "") for value in critical
        )

    async def _run_ai_extraction(
        self,
        raw_response: RawResponse,
        classification: URLClassification,
        ai_assistant: AIAssistant,
        diagnostics: Diagnostics,
    ) -> dict[str, Any]:
        """Run AI extraction and update diagnostics."""
        ai_result = await ai_assistant.extract(
            raw_response,
            classification.platform,
            classification.content_type,
        )
        diagnostics.ai_assisted = True
        diagnostics.ai_model = self.config.ai_model
        diagnostics.ai_tokens_used = ai_assistant.extractor.total_tokens_used
        return ai_result

    @staticmethod
    def _merge_ai_fields(
        selector_data: dict[str, Any],
        ai_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge AI-extracted fields into selector-extracted data.

        Only fills missing or empty values; existing selector values win.
        """
        merged = dict(selector_data)
        for key, value in ai_data.items():
            if key == "selectors_used":
                continue
            existing = merged.get(key)
            if (
                (existing is None or (isinstance(existing, str) and existing.strip() == ""))
                and value is not None
                and value != []
            ):
                merged[key] = value
        return merged

    async def _normalize(  # noqa: PLR0913
        self,
        extracted: dict[str, Any],
        classification: URLClassification,
        raw_response: RawResponse,
        *,
        adapter: Any = None,
        fallback_triggered: bool = False,
        ai_assisted: bool = False,
    ) -> tuple[Any, float]:
        """Normalize extracted data and return with timing."""
        start = time.perf_counter()
        output = await self.normalizer.normalize(
            extracted,
            classification.platform,
            classification.url,
            raw_response.strategy,
            fallback_triggered=fallback_triggered,
            ai_assisted=ai_assisted,
        )
        output.content_type = classification.content_type
        output.scraping_strategy = raw_response.strategy
        adapter_confidence = (
            adapter.manifest.confidence
            if adapter is not None and getattr(adapter.manifest, "confidence", 0.0) > 0.0
            else None
        )
        if adapter_confidence is not None:
            output.confidence = round(output.confidence * adapter_confidence, 4)
        return output, _elapsed_ms(start)

    async def _archive_raw_html(
        self,
        url: str,
        raw_response: RawResponse,
        diagnostics: Diagnostics,
    ) -> str:
        """Archive raw HTML and return the archive identifier."""
        if self.archiver is None:
            raise RuntimeError("Archiver is not available")
        metadata = {
            "platform": diagnostics.platform,
            "strategy": diagnostics.primary_strategy,
            "http_status": diagnostics.http_status,
            "html_size_bytes": diagnostics.html_size_bytes,
            "headers": dict(diagnostics.response_headers),
        }
        return self.archiver.archive(url, raw_response.html, metadata=metadata)

    async def _persist_result(
        self,
        result: ScrapingResult,
        raw_response: RawResponse,
        archive_id: str | None,
    ) -> None:
        """Persist the scraping result to storage."""
        if self.storage is None:
            raise RuntimeError("Storage backend is not available")
        self.storage.save_scrape_result(
            result,
            raw_html=raw_response.html,
            archive_id=archive_id,
        )

    async def _collect_with_retry(
        self,
        collector: Collector,
        url: str,
        options: ScrapingOptions,
        diagnostics: Diagnostics,
    ) -> RawResponse:
        """Collect ``url`` with exponential backoff retries.

        Args:
            collector: Collector to use.
            url: Target URL.
            options: Collection options.
            diagnostics: Mutable diagnostics object to update retries.

        Returns:
            ``RawResponse`` from the collector.

        Raises:
            RetryableError: When retries are exhausted on a retryable failure.
        """
        max_retries = options.max_retries
        last_exception: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                return await collector.collect(url, options)
            except (RetryableError, AntiBotDetectedError) as exc:
                last_exception = exc
                if attempt < max_retries:
                    diagnostics.retries += 1
                    # Exponential backoff with full jitter.
                    base = 2**attempt
                    await asyncio.sleep(base * (0.5 + random.random()))  # noqa: S311
                else:
                    raise

        if last_exception is not None:
            raise last_exception
        raise RuntimeError("Unexpected empty retry loop")

    def _build_error(
        self,
        url: str,
        exc: Exception | None,
        strategies_attempted: list[str],
        selectors_tried: list[str],
    ) -> dict[str, Any]:
        """Build a structured error dictionary."""
        code = "SCR_099"
        message = "Unknown error"
        http_status: int | None = None
        suggested_fix: str | None = None

        if isinstance(exc, UnsupportedURLError):
            code = "SCR_001"
            message = str(exc)
            suggested_fix = "Check the URL format or install a matching plugin"
        elif isinstance(exc, RetryableError):
            code = "SCR_011"
            message = str(exc)
            suggested_fix = "Increase timeout or retry later"
        elif exc is not None:
            message = str(exc)
            suggested_fix = "Check diagnostics and retry"

        return {
            "code": code,
            "message": message,
            "url": url,
            "strategy": strategies_attempted[-1] if strategies_attempted else None,
            "http_status": http_status,
            "selectors_tried": selectors_tried,
            "suggested_fix": suggested_fix,
        }


def _elapsed_ms(start: float) -> float:
    """Return elapsed milliseconds since ``start``."""
    return (time.perf_counter() - start) * 1000


def _float_to_int_ms(timing: dict[str, float]) -> dict[str, int]:
    """Convert timing values from float milliseconds to integer milliseconds."""
    return {stage: round(value) for stage, value in timing.items()}
