"""PhoenixArchitect orchestrator.

Coordinates the autonomous adapter-generation workflow:
1. Check if an existing adapter already handles the URL.
2. Classify the content type.
3. Discover/explore candidate pages.
4. Inspect pages and generate an adapter spec.
5. Coder writes a Phoenix Engine adapter.
6. Critic validates the adapter and loops back for repairs.
7. Persist and register the adapter.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from phoenix.adapters.base import BaseAdapter
from phoenix.architect.coder import Coder
from phoenix.architect.critic import AdapterCritic
from phoenix.architect.explorer import BrowserExplorer
from phoenix.architect.inspector import Inspector
from phoenix.architect.researcher import Researcher
from phoenix.architect.template_generator import generate_adapter_code
from phoenix.architect.writer import GeneratedAdapterWriter
from phoenix.collectors.browser_pool import BrowserPool
from phoenix.intelligence.classifier import ContentClassifier, HeuristicContentClassifier
from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor
from phoenix.router import URLRouter

if TYPE_CHECKING:
    from phoenix.architect.critic import AdapterValidationReport
    from phoenix.architect.explorer import PageSnapshot
    from phoenix.architect.fixture_generator import FixtureGenerator
    from phoenix.architect.researcher import SearchResult

logger = logging.getLogger(__name__)

_HEURISTIC_CONFIDENCE_THRESHOLD = 0.8
_DEFAULT_SCORE_THRESHOLD = 0.6


class PhoenixArchitect:
    """High-level controller for autonomous adapter generation."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        router: URLRouter | None = None,
        browser_pool: BrowserPool | None = None,
        ai_extractor: PhoenixAIExtractor | None = None,
        content_classifier: ContentClassifier | None = None,
        critic: AdapterCritic | None = None,
        writer: GeneratedAdapterWriter | None = None,
        researcher: Researcher | None = None,
        fixture_generator: FixtureGenerator | None = None,
    ) -> None:
        """Initialize the architect.

        Args:
            router: Router used to find existing adapters. A default router is
                created if none is supplied.
            browser_pool: Optional browser pool for page exploration. A default
                pool with stealth enabled is created on demand if none is given.
            ai_extractor: Optional Phoenix AI extractor. Defaults to a local
                Ollama-backed extractor.
            content_classifier: Optional classifier for content type detection.
            critic: Optional adapter critic for validation loops.
            writer: Optional writer for persisting generated adapters.
            researcher: Optional Researcher for search-driven URL discovery.
            fixture_generator: Optional generator for fixtures and unit tests.
        """
        self._router = router or URLRouter()
        self._browser_pool = browser_pool
        self._ai_extractor = ai_extractor or PhoenixAIExtractor()
        self._content_classifier = content_classifier
        self._critic = critic
        self._writer = writer or GeneratedAdapterWriter()
        self._researcher = researcher or Researcher()
        self._fixture_generator = fixture_generator
        self._inspector = Inspector(self._ai_extractor)
        self._coder = Coder(self._ai_extractor)

    @property
    def router(self) -> URLRouter:
        """Return the architect's router."""
        return self._router

    def find_existing_adapter(self, url: str) -> BaseAdapter | None:
        """Return an existing adapter that handles ``url``.

        PhoenixArchitect should reuse existing adapters instead of generating
        duplicates. This method consults the plugin registry and built-in
        platform patterns.

        Args:
            url: Target URL.

        Returns:
            Matching adapter or ``None`` if no adapter handles the URL.
        """
        normalized = self._router.normalize_url(url)
        adapter = self._router.get_adapter_for_url(normalized)
        if adapter is not None:
            manifest = adapter.manifest
            logger.info(
                "Found existing adapter '%s' for %s (platforms: %s)",
                manifest.name,
                normalized,
                ", ".join(manifest.platforms),
            )
        return adapter

    async def classify(self, html: str, url: str) -> dict[str, object]:
        """Classify the content type of ``html``.

        Uses a fast heuristic classifier first, then falls back to the AI
        classifier if one is configured and heuristic confidence is low.

        Args:
            html: Raw HTML content.
            url: Source URL.

        Returns:
            Classification result with ``platform``, ``content_type``, and
            ``confidence`` keys.
        """
        heuristic = HeuristicContentClassifier()
        result = heuristic.classify(html, url)
        if result.get("confidence", 0.0) >= _HEURISTIC_CONFIDENCE_THRESHOLD:
            return result

        if self._content_classifier is not None:
            try:
                ai_result = await self._content_classifier.classify(html, url)
                if ai_result.get("confidence", 0.0) >= result.get("confidence", 0.0):
                    return ai_result
            except Exception as exc:  # noqa: BLE001
                logger.warning("AI classification failed: %s", exc)

        return result

    async def explore(
        self,
        url: str,
        *,
        max_pages: int = 3,
        scroll: bool = True,
    ) -> list[PageSnapshot]:
        """Collect page snapshots from ``url``.

        Args:
            url: Starting URL.
            max_pages: Maximum pagination pages to collect.
            scroll: Whether to scroll each page for lazy-loaded content.

        Returns:
            List of collected page snapshots.
        """
        pool = self._browser_pool or BrowserPool(max_contexts=1, stealth_enabled=True)
        explorer = BrowserExplorer(pool, page_load_wait=2.0)
        try:
            return await explorer.explore(
                url,
                max_pages=max_pages,
                scroll=scroll,
            )
        finally:
            if self._browser_pool is None:
                await pool.close_all()

    async def generate_adapter(  # noqa: PLR0913
        self,
        url: str,
        *,
        max_pages: int = 3,
        max_repair_iterations: int = 2,
        score_threshold: float = _DEFAULT_SCORE_THRESHOLD,
        required_fields: list[str] | None = None,
        persist: bool = True,
        force: bool = False,
        with_fixtures: bool = False,
    ) -> tuple[BaseAdapter, AdapterValidationReport]:
        """Generate, validate, and register a Phoenix Engine adapter for ``url``.

        Args:
            url: Target URL.
            max_pages: Maximum pagination pages to explore.
            max_repair_iterations: How many Critic-driven repair loops to allow.
            score_threshold: Minimum critic score to accept the adapter.
            required_fields: Fields the generated adapter must extract. Defaults
                to the fields suggested by the Inspector.
            persist: Whether to write the adapter to disk.
            force: If ``True``, generate a new adapter even when an existing
                adapter already handles the URL.
            with_fixtures: Whether to generate pytest fixtures and a unit test
                from the collected snapshots.

        Returns:
            Tuple of the registered adapter and its validation report.

        Raises:
            ValueError: If no snapshots can be collected or the adapter cannot
                be made to pass validation.
        """
        existing = None if force else self.find_existing_adapter(url)
        if existing is not None:
            logger.info("Reusing existing adapter for %s", url)
            report = await AdapterCritic().validate(
                "",
                [],
                required_fields=required_fields or [],
            )
            report.score = 1.0
            return existing, report

        snapshots = await self.explore(url, max_pages=max_pages)
        if not snapshots:
            raise ValueError(f"No page snapshots collected for {url}")

        sample = snapshots[0]
        spec = await self._inspector.inspect(snapshots, url)
        fields = required_fields or spec.get("data_fields") or ["title", "text", "author"]

        code = await self._coder.generate(spec, sample, url)
        critic = self._get_critic()
        report = await critic.validate(code, snapshots, required_fields=fields)

        for iteration in range(max_repair_iterations):
            if report.score >= score_threshold:
                break
            logger.info(
                "Adapter score %.2f below threshold %.2f; starting repair iteration %d",
                report.score,
                score_threshold,
                iteration + 1,
            )
            fix_prompt = critic.build_fix_prompt(code, report, snapshots)
            code = await self._coder.repair(fix_prompt)
            report = await critic.validate(code, snapshots, required_fields=fields)

        if report.score < score_threshold:
            logger.info(
                "LLM adapter score %.2f below threshold; trying deterministic template",
                report.score,
            )
            code = generate_adapter_code(
                platform_name=spec.get("platform_name", "generated_site"),
                url_patterns=spec.get("url_patterns", []),
                fields=fields,
                selectors=spec.get("selectors", {}),
            )
            report = await critic.validate(code, snapshots, required_fields=fields)
            if report.score < score_threshold:
                raise ValueError(
                    f"Adapter for {url} failed validation after {max_repair_iterations} "
                    f"repair attempts and deterministic fallback (score {report.score}).",
                )

        adapter = self._register_adapter_code(code)
        adapter.manifest.confidence = report.score
        if persist:
            platform = spec.get("platform_name", adapter.manifest.platforms[0])
            self._writer.write(platform, code)
            logger.info("Persisted generated adapter '%s' for %s", platform, url)
            if with_fixtures and self._fixture_generator is not None:
                extracted_outputs = [report.extracted_fields for _ in snapshots]
                self._fixture_generator.generate(platform, snapshots, extracted_outputs)

        return adapter, report

    def _get_critic(self) -> AdapterCritic:
        """Return the configured critic or a default instance."""
        if self._critic is None:
            self._critic = AdapterCritic()
        return self._critic

    def _register_adapter_code(self, code: str) -> BaseAdapter:
        """Compile ``code`` and register the resulting adapter with the router.

        Args:
            code: Python source for the adapter.

        Returns:
            Instantiated adapter.

        Raises:
            ValueError: If the code does not contain a valid BaseAdapter subclass.
        """
        namespace: dict[str, Any] = {}
        exec(code, namespace)  # noqa: S102
        adapter_class = self._find_adapter_class(namespace)
        if adapter_class is None:
            raise ValueError("Generated code does not contain a BaseAdapter subclass")
        adapter = adapter_class()
        self._router.plugin_loader.register(adapter)
        return adapter

    async def discover(
        self,
        query: str,
        *,
        engine: str = "duckduckgo",
        max_results: int = 10,
    ) -> list[SearchResult]:
        """Discover candidate URLs for ``query`` using the configured researcher.

        Args:
            query: Natural-language goal or search query.
            engine: Search engine to use (``duckduckgo`` or ``serpapi``).
            max_results: Maximum candidate URLs to return.

        Returns:
            List of ranked search results.
        """
        return await self._researcher.discover(
            query,
            engine=engine,
            max_results=max_results,
        )

    async def generate_adapters_for_goal(  # noqa: PLR0913
        self,
        goal: str,
        *,
        max_pages: int = 3,
        max_results: int = 5,
        score_threshold: float = _DEFAULT_SCORE_THRESHOLD,
        persist: bool = True,
        engine: str = "duckduckgo",
        with_fixtures: bool = False,
    ) -> list[dict[str, object]]:
        """Discover URLs for ``goal`` and generate an adapter for each candidate.

        Args:
            goal: Natural-language scraping goal.
            max_pages: Maximum pagination pages to explore per candidate.
            max_results: Maximum URLs to discover.
            score_threshold: Minimum Critic score to accept an adapter.
            persist: Whether to write generated adapters to disk.
            engine: Search engine to use for discovery.
            with_fixtures: Whether to generate fixtures and unit tests.

        Returns:
            Summary list with adapter name, URL, platform, and score.
        """
        candidates = await self.discover(
            goal,
            engine=engine,
            max_results=max_results,
        )
        results: list[dict[str, object]] = []
        for candidate in candidates:
            if self.find_existing_adapter(candidate.url) is not None:
                logger.info("Skipping %s; existing adapter found", candidate.url)
                continue
            try:
                adapter, report = await self.generate_adapter(
                    candidate.url,
                    max_pages=max_pages,
                    score_threshold=score_threshold,
                    persist=persist,
                    with_fixtures=with_fixtures,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to generate adapter for %s: %s", candidate.url, exc)
                continue
            results.append(
                {
                    "url": candidate.url,
                    "platform": adapter.manifest.platforms[0],
                    "name": adapter.manifest.name,
                    "score": report.score,
                },
            )
        return results

    @staticmethod
    def _find_adapter_class(namespace: dict[str, Any]) -> type[BaseAdapter] | None:
        """Return the first BaseAdapter subclass in ``namespace``."""
        for obj in namespace.values():
            if isinstance(obj, type) and issubclass(obj, BaseAdapter) and obj is not BaseAdapter:
                return obj
        return None

    def load_generated_adapters(self) -> list[BaseAdapter]:
        """Import and register previously persisted generated adapters.

        Returns:
            List of registered adapters.
        """
        loaded: list[BaseAdapter] = []
        for path in self._writer.list_adapters():
            try:
                adapter = self._register_adapter_code(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to load generated adapter %s: %s", path, exc)
                continue
            loaded.append(adapter)
        return loaded


__all__ = ["PhoenixArchitect"]
