"""PhoenixArchitect Coder role.

Turns a site analysis spec into a compilable Phoenix Engine adapter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from phoenix.architect.explorer import PageSnapshot
    from phoenix.processing.phoenix_ai_extractor import PhoenixAIExtractor


class Coder:
    """Generate Phoenix Engine adapter source code from a site spec."""

    def __init__(self, extractor: PhoenixAIExtractor) -> None:
        """Initialize the coder with a Phoenix AI extractor.

        Args:
            extractor: AI extractor used to generate adapter source code.
        """
        self._extractor = extractor

    async def generate(
        self,
        spec: dict[str, Any],
        snapshot: PageSnapshot,
        url: str,
    ) -> str:
        """Return a Python adapter module for ``spec``.

        Args:
            spec: Site analysis produced by the Inspector.
            snapshot: Representative page snapshot.
            url: Source URL.

        Returns:
            Python source code for the adapter.
        """
        schema = self._build_schema(spec)
        result = await self._extractor.extract(
            html=snapshot.html[:16000],
            url=url,
            platform=spec.get("platform_name", "unknown"),
            content_type=spec.get("content_type", "generic"),
            schema_description=schema,
            strict=True,
        )
        if isinstance(result, list) and result:
            result = result[0]
        if not isinstance(result, dict):
            return ""
        return str(result.get("code", ""))

    async def repair(self, prompt: str) -> str:
        """Return a corrected adapter module given a fix ``prompt``.

        Args:
            prompt: Detailed prompt describing validation failures.

        Returns:
            Corrected Python source code.
        """
        schema = (
            "Return a JSON object with exactly these fields:\n"
            "  code: string - the complete corrected Python adapter module\n"
            "  platform_name: string - confirmed snake_case platform identifier\n"
            "  url_patterns: list of regex URL patterns the adapter handles"
        )
        result = await self._extractor.extract(
            html=prompt[:20000],
            url="",
            platform="unknown",
            content_type="adapter_fix",
            schema_description=schema,
            strict=True,
        )
        if isinstance(result, list) and result:
            result = result[0]
        if not isinstance(result, dict):
            return ""
        return str(result.get("code", ""))

    @staticmethod
    def _build_schema(spec: dict[str, Any]) -> str:
        """Build the JSON schema/instructions for code generation."""
        fields = spec.get("data_fields") or ["title", "text", "author"]
        selectors = spec.get("selectors") or {}
        platform_name = spec.get("platform_name", "unknown")
        return (
            "Return a JSON object with exactly these fields:\n"
            "  code: string - the complete Python adapter module. "
            "The string must contain valid Python source code.\n"
            "  platform_name: string - confirmed snake_case platform identifier\n"
            "  url_patterns: list of regex URL patterns the adapter handles\n"
            "  generated: boolean - must be true\n\n"
            "Required imports (include all of them):\n"
            "  import re\n"
            "  from typing import Any\n"
            "  from bs4 import BeautifulSoup\n"
            "  from phoenix.adapters.base import BaseAdapter\n"
            "  from phoenix.models.document import RawResponse\n"
            "  from phoenix.models.output import UnifiedOutput\n"
            "  from phoenix.plugins.manifest import PluginManifest\n"
            "  from phoenix.processing.normalizer import Normalizer\n\n"
            "The adapter code must:\n"
            "1. Subclass BaseAdapter.\n"
            "2. Define a 'manifest' property returning PluginManifest with "
            "name, version, platforms=[platform_name], url_patterns, and "
            "generated=True.\n"
            "3. Implement supported_patterns() returning a list of compiled regex "
            "patterns: [re.compile(p) for p in self.manifest.url_patterns].\n"
            "4. Implement async collect(url, strategy, collector, options) that "
            "returns the RawResponse from collector.collect(url, options) after "
            "checking self._is_public_content(raw_response.html).\n"
            "5. Implement async extract(raw_response) that parses "
            "raw_response.html (a string) with "
            "BeautifulSoup(raw_response.html, 'html.parser'). Return a flat "
            "dictionary whose keys exactly match the requested field names: "
            f"{fields!r}. Use soup.select(...) or soup.find_all(...) with plain "
            "CSS selectors only. Use element.get_text(strip=True) for text and "
            "element.get('href') or element.get('src') for attributes. Do NOT "
            "use Scrapy-style pseudo selectors like ::text or ::attr(...), and "
            "do NOT call .cssselect() on raw_response.html.\n"
            "6. Implement async normalize(extracted, url, strategy) that returns "
            "a UnifiedOutput by awaiting "
            f"Normalizer().normalize(extracted, {platform_name!r}, url, strategy).\n"
            "7. Include type hints and docstrings.\n"
            "8. Do NOT include a main block, test code, or relative imports.\n\n"
            "Example extract() shape (do not copy the field names):\n"
            "    async def extract(self, raw_response: RawResponse) -> dict[str, Any]:\n"
            "        soup = BeautifulSoup(raw_response.html, 'html.parser')\n"
            "        return {\n"
            "            'title': soup.select_one('h1').get_text(strip=True) "
            "if soup.select_one('h1') else None,\n"
            "            'links': [a.get('href') for a in soup.select('a.link')],\n"
            "        }\n\n"
            "Site analysis to implement:\n"
            f"platform_name={platform_name!r}\n"
            f"content_type={spec.get('content_type', 'generic')!r}\n"
            f"data_fields={fields!r}\n"
            f"selectors={selectors!r}\n"
            f"url_patterns={spec.get('url_patterns', [])!r}\n"
            f"notes={spec.get('notes', '')!r}"
        )


__all__ = ["Coder"]
