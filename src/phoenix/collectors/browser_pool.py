"""Playwright browser context pool for headless collection."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from playwright.async_api import Browser, BrowserContext, Playwright, async_playwright

from phoenix.stealth.profile import StealthProfile, profile_presets

if TYPE_CHECKING:
    from phoenix.options import CollectionOptions
    from phoenix.stealth.rotator import ProxyRotator


@dataclass(frozen=True)
class _ContextKey:
    """Identity used to reuse contexts with matching stealth settings."""

    profile_id: str
    proxy_server: str


class BrowserPool:
    """Pool of reusable Playwright browser contexts.

    The pool limits the number of concurrent browser contexts and reuses
    released contexts across collection operations. It is responsible for
    launching the browser, creating contexts, and cleaning up resources on
    shutdown.
    """

    def __init__(  # noqa: PLR0913
        self,
        max_contexts: int = 2,
        browser_type: str = "chromium",
        playwright: Playwright | None = None,
        *,
        stealth_enabled: bool = False,
        stealth_profile: StealthProfile | None = None,
        proxy_rotator: ProxyRotator | None = None,
    ) -> None:
        """Initialize the browser pool.

        Args:
            max_contexts: Maximum number of browser contexts to keep open.
            browser_type: Playwright browser engine (``chromium``, ``firefox``,
                or ``webkit``).
            playwright: Optional pre-initialized Playwright instance. If
                provided, the pool will not start or stop Playwright itself.
            stealth_enabled: Whether to create contexts with anti-detection
                settings when no explicit profile is requested.
            stealth_profile: Default profile to apply to new contexts. If
                ``None`` and ``stealth_enabled`` is ``True``, a Chrome/Windows
                preset is used.
            proxy_rotator: Optional proxy rotator used when a request does not
                specify a proxy explicitly.
        """
        self._max_contexts = max(max_contexts, 1)
        self._browser_type = browser_type
        self._playwright = playwright
        self._owns_playwright = playwright is None
        self._browser: Browser | None = None
        self._contexts: list[BrowserContext] = []
        self._context_keys: dict[int, _ContextKey] = {}
        self._available: asyncio.Queue[BrowserContext] = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._closed = False
        self._stealth_enabled = stealth_enabled
        self._default_profile = stealth_profile or profile_presets()["chrome_windows"]
        self._proxy_rotator = proxy_rotator

    async def _ensure_browser(self) -> Browser:
        """Return an open browser instance, launching one if necessary."""
        if self._browser is None:
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            launcher = getattr(self._playwright, self._browser_type)
            launch_args: list[str] = []
            if self._stealth_enabled or self._proxy_rotator is not None:
                launch_args.extend(
                    [
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=IsolateOrigins,site-per-process",
                    ],
                )
            self._browser = await launcher.launch(headless=True, args=launch_args)
        return self._browser

    def _resolve_profile(self, options: CollectionOptions | None) -> StealthProfile:
        """Pick a profile for a context based on options and defaults."""
        if options is not None and options.stealth_enabled and options.stealth_profile:
            presets = profile_presets()
            if options.stealth_profile in presets:
                return presets[options.stealth_profile]
        if self._stealth_enabled:
            return self._default_profile
        return StealthProfile(
            profile_id="default",
            user_agent="",
            viewport={"width": 1280, "height": 720},
        )

    def _resolve_proxy(self, options: CollectionOptions | None) -> dict[str, str] | None:
        """Pick a proxy for a context based on options and defaults."""
        if options is not None and options.proxy:
            return {"server": options.proxy}
        if self._proxy_rotator is not None:
            return self._proxy_rotator.next()
        return None

    def _context_key(
        self,
        profile: StealthProfile,
        proxy: dict[str, str] | None,
    ) -> _ContextKey:
        """Build a reusable identity for a context configuration."""
        proxy_server = proxy.get("server", "") if proxy is not None else ""
        return _ContextKey(profile_id=profile.profile_id, proxy_server=proxy_server)

    async def acquire(self, options: CollectionOptions | None = None) -> BrowserContext:
        """Acquire a browser context from the pool.

        Args:
            options: Optional collection options used to select a matching
                stealth profile and proxy.

        Returns:
            A Playwright ``BrowserContext`` ready for page navigation.

        Raises:
            RuntimeError: If the pool has already been closed.
        """
        if self._closed:
            raise RuntimeError("BrowserPool has been closed")

        profile = self._resolve_profile(options)
        proxy = self._resolve_proxy(options)
        key = self._context_key(profile, proxy)

        async with self._lock:
            # Try to reuse an already-created context with the same settings.
            available: list[BrowserContext] = []
            while not self._available.empty():
                ctx = self._available.get_nowait()
                ctx_key = self._context_keys.get(id(ctx))
                if ctx_key == key:
                    return ctx
                available.append(ctx)
            for ctx in available:
                await self._available.put(ctx)

            if len(self._contexts) < self._max_contexts:
                browser = await self._ensure_browser()
                context_kwargs = profile.with_proxy(proxy).context_kwargs()
                # Playwright proxy is passed at context level for chromium and
                # firefox; webkit ignores it but is not the default.
                if proxy is not None and self._browser_type != "webkit":
                    context_kwargs["proxy"] = proxy
                context = await browser.new_context(**context_kwargs)
                self._contexts.append(context)
                self._context_keys[id(context)] = key
                return context

        # All contexts are in use; wait until one is released.
        return await self._available.get()

    async def release(self, context: BrowserContext) -> None:
        """Release a context back to the pool for reuse.

        Args:
            context: The context to return to the pool.
        """
        if self._closed:
            return
        await self._available.put(context)

    async def close_all(self) -> None:
        """Close all contexts, the browser, and stop Playwright if owned."""
        self._closed = True
        for context in self._contexts:
            await context.close()
        if self._browser is not None:
            await self._browser.close()
            self._browser = None
        if self._owns_playwright and self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None
        self._contexts.clear()
        self._context_keys.clear()
        while not self._available.empty():
            self._available.get_nowait()


__all__ = ["BrowserPool"]
