"""Anti-bot recovery intelligence for Phoenix Engine.

Detects blocking/challenge pages and suggests recovery strategies using
heuristics and local AI. Strategies can then be applied by the collector or
orchestrator.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor

logger = logging.getLogger(__name__)

_RATE_LIMIT_STATUS: int = 429
_FORBIDDEN_STATUS: int = 403
_AI_CONFIDENCE_THRESHOLD: float = 0.7

_BLOCK_INDICATORS: tuple[str, ...] = (
    "captcha",
    "cloudflare",
    "cf-browser-verification",
    "access denied",
    "blocked",
    "rate limit",
    "too many requests",
    "please verify",
    "are you human",
    "security check",
    "ddos-guard",
    "perimeterx",
    "datadome",
    "forbidden",
)

_RECOVERY_STRATEGIES: tuple[str, ...] = (
    "increase_delay",
    "switch_to_browser",
    "rotate_user_agent",
    "clear_cookies",
    "use_proxy",
    "warm_session",
    "cooldown",
)


class AntiBotRecovery:
    """Analyze block pages and suggest recovery strategies."""

    def __init__(self, extractor: PhoenixAIExtractor | None = None) -> None:
        """Initialize with an optional Phoenix AI extractor.

        Args:
            extractor: AI extractor used to analyze complex block pages. If
                ``None``, only heuristic detection is available.
        """
        self._extractor = extractor

    def detect(self, html: str, status_code: int) -> dict[str, Any]:
        """Detect whether ``html`` is a block/challenge page.

        Args:
            html: Raw HTML response.
            status_code: HTTP status code.

        Returns:
            Detection result with ``blocked``, ``reason``, and ``indicators``.
        """
        html_lower = html.lower()
        indicators = [i for i in _BLOCK_INDICATORS if i in html_lower]
        if "cf-browser-verification" in indicators and "cloudflare" not in indicators:
            indicators.append("cloudflare")
        blocked = bool(indicators) or status_code in {_FORBIDDEN_STATUS, _RATE_LIMIT_STATUS, 503}
        reason = indicators[0] if indicators else "status_code"
        return {
            "blocked": blocked,
            "reason": reason,
            "indicators": indicators,
            "status_code": status_code,
        }

    async def suggest_strategy(
        self,
        html: str,
        status_code: int,
        platform: str = "generic",
    ) -> dict[str, Any]:
        """Suggest a recovery strategy for a blocked page.

        First applies heuristic rules, then optionally asks the local AI for
        a more nuanced suggestion.

        Args:
            html: Block page HTML.
            status_code: HTTP status code.
            platform: Platform identifier for context.

        Returns:
            Suggestion with ``strategy``, ``confidence``, and ``actions``.
        """
        detection = self.detect(html, status_code)
        if not detection["blocked"]:
            return {
                "blocked": False,
                "strategy": None,
                "confidence": 1.0,
                "actions": [],
            }

        reason = detection["reason"]
        strategy = self._heuristic_strategy(reason, status_code)

        if self._extractor is not None:
            try:
                ai_strategy = await self._ai_suggest_strategy(
                    html,
                    status_code,
                    platform,
                    reason,
                )
                if ai_strategy.get("confidence", 0.0) > _AI_CONFIDENCE_THRESHOLD:
                    strategy = ai_strategy
            except Exception as exc:  # noqa: BLE001
                logger.warning("AI anti-bot recovery failed: %s", exc)

        return {
            "blocked": True,
            **strategy,
            "detection": detection,
        }

    def _heuristic_strategy(self, reason: str, status_code: int) -> dict[str, Any]:
        """Return a recovery strategy based on simple rules."""
        if status_code == _RATE_LIMIT_STATUS or "rate limit" in reason or "too many" in reason:
            return {
                "strategy": "increase_delay",
                "confidence": 0.85,
                "actions": ["double_per_domain_delay", "enable_exponential_backoff"],
            }
        if "captcha" in reason or "verify" in reason or "human" in reason:
            return {
                "strategy": "switch_to_browser",
                "confidence": 0.8,
                "actions": ["use_browser_collector", "enable_stealth_profile"],
            }
        if "cloudflare" in reason or "ddos" in reason or "perimeterx" in reason:
            return {
                "strategy": "warm_session",
                "confidence": 0.75,
                "actions": ["warm_session", "use_browser_collector", "increase_delay"],
            }
        if status_code == _FORBIDDEN_STATUS or "blocked" in reason or "denied" in reason:
            return {
                "strategy": "rotate_user_agent",
                "confidence": 0.7,
                "actions": ["rotate_user_agent", "use_proxy", "clear_cookies"],
            }
        return {
            "strategy": "cooldown",
            "confidence": 0.6,
            "actions": ["pause_scraping", "retry_after_cooldown"],
        }

    async def _ai_suggest_strategy(
        self,
        html: str,
        status_code: int,
        platform: str,
        reason: str,
    ) -> dict[str, Any]:
        """Ask the local AI to suggest a recovery strategy."""
        if self._extractor is None:
            return {"strategy": "cooldown", "confidence": 0.0, "actions": []}
        extractor = self._extractor
        schema = (
            "Return a JSON object with exactly these fields:\n"
            "  strategy: one of: increase_delay, switch_to_browser, "
            "rotate_user_agent, clear_cookies, use_proxy, warm_session, cooldown\n"
            "  confidence: number between 0.0 and 1.0\n"
            "  actions: list of concrete steps to try\n\n"
            f"Context: HTTP {status_code}, detected reason: {reason}."
        )
        result = await extractor.extract(
            html=html[:4000],
            url="",
            platform=platform,
            content_type="block_page",
            schema_description=schema,
            strict=False,
        )
        if isinstance(result, list) and result:
            result = result[0]
        if not isinstance(result, dict):
            return {"strategy": "cooldown", "confidence": 0.0, "actions": []}
        return {
            "strategy": result.get("strategy", "cooldown"),
            "confidence": float(result.get("confidence", 0.0)),
            "actions": result.get("actions", []),
        }


__all__ = ["AntiBotRecovery"]
