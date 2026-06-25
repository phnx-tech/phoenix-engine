"""End-to-end HTTP scrape against a real site."""

from __future__ import annotations

import asyncio
import json

from phoenix import PhoenixEngine
from phoenix.collectors.direct import DirectCollector
from phoenix.collectors.base import StubCollector
from phoenix.infrastructure.rate_limiter import RateLimiter
from phoenix.models.config import Config


async def main() -> None:
    config = Config(
        ai_enabled=False,
        archive_enabled=False,
        timeout=30.0,
    )
    rate_limiter = RateLimiter(config)
    collectors = {
        "http": DirectCollector(config, rate_limiter),
        "browser": StubCollector(strategy="browser"),
    }

    async with PhoenixEngine(config=config, collectors=collectors) as engine:
        result = await engine.scrape(
            "https://quotes.toscrape.com/",
            strategy="http",
        )

    print(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))

    if result.success:
        print("\n✅ E2E scrape succeeded")
        if result.ai_assisted:
            print("🤖 AI extraction was used")
    else:
        print("\n❌ E2E scrape failed")


if __name__ == "__main__":
    asyncio.run(main())
