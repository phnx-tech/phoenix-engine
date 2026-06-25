"""Strategy selector for Phoenix Engine.

Selects the optimal collection strategy (HTTP vs browser) for a URL based on
platform rules, optional user overrides, and remembered domain history.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

from phoenix.models import ScrapingStrategy, StrategySelection

if TYPE_CHECKING:
    from phoenix.models import Config
    from phoenix.processing.domain_memory import DomainMemory


# Platforms where JavaScript rendering is required for reliable extraction.
_BROWSER_PRIMARY_PLATFORMS: set[str] = {"instagram", "tiktok", "linkedin", "facebook"}

# Platforms where HTTP usually works but browser fallback helps.
_HTTP_WITH_BROWSER_FALLBACK: set[str] = {"x", "youtube", "generic"}

_VALID_STRATEGIES: set[str] = {"http", "browser"}


class StrategySelector:
    """Selects the primary collection strategy and fallback chain for a URL."""

    def __init__(
        self,
        config: Config,
        domain_memory: DomainMemory | None = None,
    ) -> None:
        """Initialize with application configuration.

        Args:
            config: Phoenix Engine configuration.
            domain_memory: Optional persistent domain memory used to prime
                per-domain strategy decisions.
        """
        self.config = config
        self._domain_memory: dict[str, dict[str, object]] = {}
        self._persistent_memory = domain_memory

    def _domain(self, url: str) -> str:
        """Extract the registered domain from ``url``."""
        netloc = urlparse(url).netloc.lower()
        if "." in netloc and netloc.startswith("www."):
            return netloc[4:]
        return netloc

    def record_success(self, url: str, strategy: str) -> None:
        """Record that ``strategy`` succeeded for ``url``'s domain.

        Args:
            url: URL that was successfully collected.
            strategy: Strategy that succeeded (``http`` or ``browser``).
        """
        if strategy not in _VALID_STRATEGIES:
            return
        domain = self._domain(url)
        entry = self._domain_memory.setdefault(domain, {})
        entry[strategy] = True

    async def select(
        self,
        url: str,
        platform: str,
        user_override: str | ScrapingStrategy | None = None,
    ) -> StrategySelection:
        """Select the collection strategy for ``url``.

        Args:
            url: Target URL (normalized).
            platform: Platform identifier from the router.
            user_override: Optional forced strategy (``http`` or ``browser``).

        Returns:
            ``StrategySelection`` with primary strategy and fallback chain.

        Raises:
            ValueError: If ``user_override`` is not a valid strategy.
        """
        override_value = str(user_override) if user_override is not None else None
        if override_value is not None and override_value not in _VALID_STRATEGIES:
            raise ValueError(f"Invalid strategy override: {override_value}")

        domain = self._domain(url)
        memory = self._domain_memory.get(domain, {})
        if self._persistent_memory is not None:
            persisted = self._persistent_memory.get(domain)
            for strategy in ("http", "browser"):
                if persisted.strategy_memory.get(strategy, {}).get("success"):
                    memory[strategy] = True

        primary, fallbacks, reason = self._default_strategy(platform)

        if override_value:
            primary = override_value
            reason = f"User override: {override_value}"
            other = self._other_strategy(override_value)
            if other and other not in fallbacks:
                fallbacks = [other, *fallbacks]
        elif memory.get("browser") and primary != "browser":
            reason = "Domain memory indicates browser strategy succeeds"
            fallbacks = [primary, *(fb for fb in fallbacks if fb != primary)]
            primary = "browser"
        elif memory.get("http") and primary != "http":
            reason = "Domain memory indicates HTTP strategy succeeds"
            fallbacks = [primary, *(fb for fb in fallbacks if fb != primary)]
            primary = "http"

        # Ensure the primary strategy does not appear in fallbacks.
        fallbacks = [fb for fb in fallbacks if fb != primary]
        return StrategySelection(
            primary=primary,
            fallbacks=fallbacks,
            reason=reason,
        )

    def _default_strategy(self, platform: str) -> tuple[str, list[str], str]:
        """Return the default strategy, fallbacks, and reason for a platform."""
        if platform in _BROWSER_PRIMARY_PLATFORMS:
            return (
                "browser",
                ["http"],
                f"{platform} requires JavaScript rendering",
            )
        if platform in _HTTP_WITH_BROWSER_FALLBACK:
            return (
                "http",
                ["browser"],
                f"{platform} prefers HTTP with browser fallback",
            )
        return (
            "http",
            ["browser"],
            "Generic/static pages default to HTTP",
        )

    def _other_strategy(self, strategy: str) -> str | None:
        """Return the strategy opposite to ``strategy``."""
        return "browser" if strategy == "http" else "http"
