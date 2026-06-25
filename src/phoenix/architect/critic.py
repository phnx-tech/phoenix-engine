"""Adapter critic for PhoenixArchitect.

Validates generated adapter code against collected page snapshots and builds
feedback prompts so the architect can iterate toward a working adapter.
"""

from __future__ import annotations

import asyncio
import builtins
import json
import logging
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

from bs4 import BeautifulSoup

from phoenix.adapters.base import BaseAdapter
from phoenix.models.document import RawResponse

if TYPE_CHECKING:
    from phoenix.architect.explorer import PageSnapshot

logger = logging.getLogger(__name__)

_CSS_SELECTOR_RE = re.compile(
    r"(?:find_all|find|select|cssselect|query_selector|query_selector_all)\s*\(\s*['\"]([^'\"]+)['\"]",
)


class AdapterValidationReport:
    """Result of validating generated adapter code."""

    def __init__(self) -> None:
        self.compiles: bool = False
        self.compile_error: str | None = None
        self.execution_error: str | None = None
        self.selectors: dict[str, int] = {}
        self.missing_fields: list[str] = []
        self.field_mentions: dict[str, bool] = {}
        self.extracted_fields: dict[str, Any] = {}
        self.score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return the report as a JSON-serializable dict."""
        return {
            "compiles": self.compiles,
            "compile_error": self.compile_error,
            "execution_error": self.execution_error,
            "selectors": self.selectors,
            "missing_fields": self.missing_fields,
            "field_mentions": self.field_mentions,
            "extracted_fields": self.extracted_fields,
            "score": self.score,
        }


class AdapterCritic:
    """Critic that checks generated adapter code against real HTML snapshots."""

    async def validate(
        self,
        code: str,
        snapshots: list[PageSnapshot],
        *,
        required_fields: list[str] | None = None,
    ) -> AdapterValidationReport:
        """Validate ``code`` against ``snapshots``.

        Checks performed:
        - Code compiles to valid Python syntax.
        - Required fields are referenced in the code.
        - CSS selectors used in the code match elements in the snapshots.
        - The adapter can be instantiated and its ``extract`` method returns
          the required fields for at least one snapshot.

        Args:
            code: Generated adapter Python source.
            snapshots: Collected page snapshots to validate against.
            required_fields: Fields the adapter should extract. Defaults to
                ``["title", "text", "author"]``.

        Returns:
            Validation report with score and detailed findings.
        """
        report = AdapterValidationReport()
        required_fields = required_fields or ["title", "text", "author"]

        # 1. Syntax check.
        try:
            compile(code, "<generated_adapter>", "exec")
            report.compiles = True
        except SyntaxError as exc:
            report.compile_error = str(exc)
            return report

        # 2. Field mentions.
        code_lower = code.lower()
        for field in required_fields:
            report.field_mentions[field] = field in code_lower
        report.missing_fields = [
            field for field, present in report.field_mentions.items() if not present
        ]

        # 3. Selector match counts.
        selectors = self._extract_selectors(code)
        if snapshots and selectors:
            soup = BeautifulSoup(snapshots[0].html, "html.parser")
            for selector in selectors:
                try:
                    count = len(soup.select(selector))
                except Exception:  # noqa: BLE001
                    count = 0
                report.selectors[selector] = count

        # 4. Runtime validation.
        if snapshots:
            extracted = await self._run_adapter(code, snapshots[0])
            if isinstance(extracted, dict):
                report.extracted_fields = {field: extracted.get(field) for field in required_fields}
                empty_fields = [
                    field
                    for field, value in report.extracted_fields.items()
                    if value is None or (isinstance(value, str) and value.strip() == "")
                ]
                report.missing_fields = list(
                    dict.fromkeys(report.missing_fields + empty_fields),
                )
            else:
                report.execution_error = str(extracted)

        # 5. Overall score.
        score = 0.0
        if report.compiles:
            score += 0.2
        if not report.missing_fields:
            score += 0.2
        if not report.execution_error:
            score += 0.4
            matched_selectors = [sel for sel, count in report.selectors.items() if count > 0]
            if selectors:
                score += 0.2 * (len(matched_selectors) / len(selectors))
        report.score = round(score, 2)

        return report

    @staticmethod
    def _extract_selectors(code: str) -> list[str]:
        """Return CSS/selectors found in ``code``."""
        seen: set[str] = set()
        selectors: list[str] = []
        for match in _CSS_SELECTOR_RE.finditer(code):
            selector = match.group(1)
            if selector not in seen:
                seen.add(selector)
                selectors.append(selector)
        return selectors

    async def _run_adapter(
        self,
        code: str,
        snapshot: PageSnapshot,
    ) -> dict[str, Any] | Exception:
        """Compile, instantiate, and run the adapter's ``extract`` and ``normalize`` methods.

        Args:
            code: Adapter source code.
            snapshot: Snapshot to extract from.

        Returns:
            Extracted dict on success, or the raised exception on failure.
        """
        namespace = dict(self._safe_globals())
        try:
            exec(code, namespace)  # noqa: S102
            adapter_class = self._find_adapter_class(namespace)
            if adapter_class is None:
                return ValueError("No BaseAdapter subclass found in generated code")
            adapter = adapter_class()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Generated adapter failed to import/instantiate: %s", exc)
            return exc

        raw_response = RawResponse(
            url=snapshot.url,
            final_url=snapshot.url,
            status_code=200,
            html=snapshot.html,
            strategy="browser",
            timestamp=datetime.now(UTC),
        )
        try:
            if asyncio.iscoroutinefunction(adapter.extract):
                result = await adapter.extract(raw_response)
            else:
                result = adapter.extract(raw_response)
        except Exception as exc:  # noqa: BLE001
            return exc

        extracted = result
        if not isinstance(extracted, dict):
            return ValueError("extract() must return a dictionary")
        extracted = cast("dict[str, Any]", extracted)

        try:
            if asyncio.iscoroutinefunction(adapter.normalize):
                await adapter.normalize(extracted, snapshot.url, "browser")
            else:
                adapter.normalize(extracted, snapshot.url, "browser")
        except Exception as exc:  # noqa: BLE001
            return exc

        return extracted

    @staticmethod
    def _safe_globals() -> dict[str, Any]:
        """Return a restricted globals dict for executing generated adapters."""
        safe_names = {
            "True",
            "False",
            "None",
            "abs",
            "all",
            "any",
            "bool",
            "bin",
            "chr",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "Exception",
            "filter",
            "float",
            "format",
            "frozenset",
            "hasattr",
            "getattr",
            "hex",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "map",
            "max",
            "min",
            "next",
            "object",
            "oct",
            "ord",
            "pow",
            "print",
            "property",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "sorted",
            "staticmethod",
            "str",
            "sum",
            "super",
            "tuple",
            "type",
            "ValueError",
            "AttributeError",
            "KeyError",
            "TypeError",
            "ImportError",
            "ModuleNotFoundError",
            "zip",
            "__build_class__",
        }
        allowed_builtins = {
            name: getattr(builtins, name) for name in safe_names if hasattr(builtins, name)
        }
        allowed_builtins["__import__"] = __import__
        return {
            "__builtins__": allowed_builtins,
            "__name__": "__generated_adapter__",
        }

    @staticmethod
    def _find_adapter_class(namespace: dict[str, Any]) -> type[Any] | None:
        """Return the first BaseAdapter subclass defined in ``namespace``."""
        for obj in namespace.values():
            if isinstance(obj, type) and issubclass(obj, BaseAdapter) and obj is not BaseAdapter:
                return obj
        return None

    def build_fix_prompt(
        self,
        code: str,
        report: AdapterValidationReport,
        snapshots: list[PageSnapshot],
    ) -> str:
        """Build a prompt asking the LLM to fix the generated adapter.

        Args:
            code: Current generated adapter source.
            report: Validation report with errors.
            snapshots: Collected snapshots the adapter must handle.

        Returns:
            Prompt string for the LLM.
        """
        sample_html = snapshots[0].html[:4000] if snapshots else ""
        return (
            "The following Phoenix Engine adapter failed validation. "
            "Fix it so it compiles, references the required fields, "
            "uses CSS selectors that actually match the provided HTML, "
            "and successfully extracts the required fields.\n\n"
            f"Validation report:\n{json.dumps(report.to_dict(), indent=2)}\n\n"
            f"Current adapter code:\n```python\n{code}\n```\n\n"
            f"HTML sample:\n```html\n{sample_html}\n```\n\n"
            "Return ONLY the corrected Python code inside a markdown code block."
        )


__all__ = ["AdapterCritic", "AdapterValidationReport"]
