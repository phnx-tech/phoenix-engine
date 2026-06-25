"""Phoenix Engine public API."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Self

from phoenix.collectors.base import Collector, StubCollector
from phoenix.infrastructure.audit_logger import AuditLogger
from phoenix.infrastructure.license_manager import LicenseManager
from phoenix.intelligence.change_detector import ChangeDetector
from phoenix.models import Config, ScrapingOptions, ScrapingResult
from phoenix.pipeline import PipelineController
from phoenix.plugins.loader import PluginLoader
from phoenix.processing.ai_assistant import AIAssistant
from phoenix.processing.archiver import SourceArchiver
from phoenix.processing.domain_memory import DomainMemory
from phoenix.processing.html_extractor import HTMLExtractor
from phoenix.processing.normalizer import Normalizer
from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor
from phoenix.router import URLRouter
from phoenix.strategy_selector import StrategySelector
from phoenix.version import __version__

if TYPE_CHECKING:
    from phoenix.infrastructure.rate_limiter import RateLimiter
    from phoenix.infrastructure.session_manager import SessionManager
    from phoenix.infrastructure.storage import StorageBackend


class PhoenixEngine:
    """Primary entry point for the Phoenix Engine scraping library.

    Pure scraping: all data comes from HTML parsing via HTTP requests or
    headless browser rendering. No official APIs are used.

    Example:
        async with PhoenixEngine() as engine:
            result = await engine.scrape("https://example.com/post/123")
            print(result.output)
    """

    version: str = __version__

    def __init__(  # noqa: PLR0913
        self,
        config: Config | None = None,
        *,
        collectors: dict[str, Collector] | None = None,
        storage: StorageBackend | None = None,
        session_manager: SessionManager | None = None,
        archiver: SourceArchiver | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """Initialize the Phoenix Engine.

        Args:
            config: Application configuration. If ``None``, default config is used.
            collectors: Optional mapping of strategy name to ``Collector``.
                If ``None``, stub collectors are created for HTTP and browser.
            storage: Optional persistent storage backend for results, archives,
                and sessions.
            session_manager: Optional session manager for authenticated
                platform sessions.
            archiver: Optional source archiver for raw HTML. When ``None`` and
                ``archive_enabled`` is ``True``, a default archiver is created.
            rate_limiter: Optional rate limiter used for adaptive throttling.
        """
        self.config = config or Config()
        self._license_manager = self._build_license_manager()
        self.plugin_loader = PluginLoader()
        self.plugin_loader.load_builtin_adapters()
        self.router = URLRouter(self.plugin_loader)
        self.collectors = collectors if collectors is not None else self._build_default_collectors()
        self.storage = storage
        self.session_manager = session_manager
        self.archiver = archiver if archiver is not None else self._build_default_archiver()
        self.domain_memory = self._build_domain_memory()
        self.strategy_selector = StrategySelector(
            self.config,
            domain_memory=self.domain_memory if self.config.learning_memory_enabled else None,
        )
        self.html_extractor = HTMLExtractor()
        self.normalizer = Normalizer()
        self.ai_assistant = self._build_ai_assistant()
        self.rate_limiter = rate_limiter
        self.change_detector = self._build_change_detector()
        self.audit_logger = AuditLogger(storage=self.storage)
        self.pipeline = PipelineController(
            router=self.router,
            strategy_selector=self.strategy_selector,
            collectors=self.collectors,
            html_extractor=self.html_extractor,
            normalizer=self.normalizer,
            config=self.config,
            ai_assistant=self.ai_assistant,
            storage=self.storage,
            archiver=self.archiver,
            rate_limiter=self.rate_limiter,
            domain_memory=self.domain_memory,
            change_detector=self.change_detector,
            audit_logger=self.audit_logger,
        )

    def _build_default_collectors(self) -> dict[str, Collector]:
        """Build default stub collectors for HTTP and browser strategies."""
        return {
            "http": StubCollector(strategy="http"),
            "browser": StubCollector(strategy="browser"),
        }

    def _build_license_manager(self) -> LicenseManager | None:
        """Validate the configured license key when enforcement is enabled."""
        if not self.config.license_enforcement_enabled:
            return None
        manager = LicenseManager.from_config(self.config)
        manager.validate()
        return manager

    def _build_domain_memory(self) -> DomainMemory:
        """Build the domain memory store."""
        return DomainMemory(storage=self.storage, data_dir=self.config.data_dir)

    def _build_change_detector(self) -> ChangeDetector | None:
        """Build the change detector when enabled."""
        if not self.config.change_detection_enabled:
            return None
        return ChangeDetector(storage=self.storage, config=self.config)

    def _build_default_archiver(self) -> SourceArchiver | None:
        """Build a default source archiver when archiving is enabled."""
        if not self.config.archive_enabled:
            return None
        return SourceArchiver(storage=self.storage)

    def _build_ai_assistant(self) -> AIAssistant | None:
        """Build the AI assistant when AI extraction is enabled."""
        if not self.config.ai_enabled:
            return None
        extractor = self._build_extractor()
        return AIAssistant(extractor=extractor)

    def _build_extractor(self) -> PhoenixAIExtractor:
        """Build the configured Phoenix AI extractor."""
        phoenix_ai_config = self.config.phoenix_ai
        return PhoenixAIExtractor(
            api_key=phoenix_ai_config.api_key,
            base_url=phoenix_ai_config.base_url,
            default_model=phoenix_ai_config.model,
            temperature=phoenix_ai_config.temperature,
            max_tokens=phoenix_ai_config.max_tokens,
            timeout=phoenix_ai_config.timeout,
            cache_ttl=phoenix_ai_config.cache_ttl,
            max_budget_usd=phoenix_ai_config.max_budget_usd,
        )

    async def scrape(self, url: str, **options: Any) -> ScrapingResult:  # noqa: ANN401
        """Scrape data from a single URL.

        Args:
            url: The URL to scrape.
            **options: Scraping options (e.g., ``strategy``, ``timeout``).

        Returns:
            ``ScrapingResult`` with success status and output.
        """
        scraping_options = self._build_options(options)
        return await self.pipeline.execute(url, scraping_options)

    async def collect(self, url: str, **options: Any) -> ScrapingResult:  # noqa: ANN401
        """Scrape data from a single URL.

        This is an alias for :meth:`scrape` retained for backwards
        compatibility.
        """
        return await self.scrape(url, **options)

    async def scrape_batch(
        self,
        urls: list[str],
        max_concurrency: int = 5,
        **options: Any,  # noqa: ANN401
    ) -> list[ScrapingResult]:
        """Scrape data from multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape.
            max_concurrency: Maximum number of concurrent scrapes.
            **options: Scraping options applied to all URLs.

        Returns:
            List of ``ScrapingResult`` in the same order as ``urls``.

        Raises:
            ValueError: If ``urls`` is empty or ``max_concurrency`` < 1.
        """
        if not urls:
            raise ValueError("urls must not be empty")
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")

        scraping_options = self._build_options(options)
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _scrape_one(url: str) -> ScrapingResult:
            async with semaphore:
                return await self.pipeline.execute(url, scraping_options)

        return await asyncio.gather(*[_scrape_one(url) for url in urls])

    async def collect_batch(
        self,
        urls: list[str],
        max_concurrency: int = 5,
        **options: Any,  # noqa: ANN401
    ) -> list[ScrapingResult]:
        """Scrape data from multiple URLs concurrently.

        This is an alias for :meth:`scrape_batch` retained for backwards
        compatibility.
        """
        return await self.scrape_batch(urls, max_concurrency=max_concurrency, **options)

    async def close(self) -> None:
        """Close the engine and release resources."""
        if self.storage is not None:
            self.storage.close()
        for collector in (self.collectors or {}).values():
            close_method = getattr(collector, "close", None)
            if close_method is not None:
                await close_method()

    async def __aenter__(self) -> Self:
        """Enter async context."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit async context."""
        await self.close()

    def _build_options(self, options: dict[str, Any]) -> ScrapingOptions:
        """Build ``ScrapingOptions`` from keyword arguments and config."""
        defaults = {
            "timeout": self.config.timeout,
            "archive": self.config.archive_enabled,
            "stealth_enabled": self.config.stealth_enabled,
            "stealth_profile": (
                self.config.stealth_profiles[0] if self.config.stealth_profiles else None
            ),
            "humanize": self.config.delay_max_ms > 0,
            "warm_session": self.config.warm_session,
            "captcha_action": self.config.captcha_action,
        }
        # Only apply config defaults when the option is not explicitly provided.
        for key, value in defaults.items():
            if key not in options:
                options[key] = value
        return ScrapingOptions(**options)
