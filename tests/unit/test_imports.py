"""Import smoke tests for Phoenix Engine modules."""

from __future__ import annotations

import importlib

import pytest

_MODULES = [
    "phoenix",
    "phoenix.__main__",
    "phoenix.adapters",
    "phoenix.adapters.base",
    "phoenix.cli",
    "phoenix.cli.main",
    "phoenix.collectors",
    "phoenix.collectors.base",
    "phoenix.engine",
    "phoenix.exceptions",
    "phoenix.infrastructure",
    "phoenix.infrastructure.audit_logger",
    "phoenix.infrastructure.config",
    "phoenix.infrastructure.rate_limiter",
    "phoenix.infrastructure.session_manager",
    "phoenix.infrastructure.storage",
    "phoenix.infrastructure.vault",
    "phoenix.models",
    "phoenix.models.config",
    "phoenix.models.document",
    "phoenix.models.output",
    "phoenix.models.session",
    "phoenix.scrapers",
    "phoenix.scrapers.base",
    "phoenix.scrapers.browser",
    "phoenix.scrapers.http",
    "phoenix.scrapers.selector_engine",
    "phoenix.plugins",
    "phoenix.plugins.loader",
    "phoenix.plugins.manifest",
    "phoenix.processing",
    "phoenix.processing.ai_assistant",
    "phoenix.processing.archiver",
    "phoenix.processing.html_extractor",
    "phoenix.processing.phoenix_ai_extractor",
    "phoenix.processing.normalizer",
    "phoenix.intelligence",
    "phoenix.intelligence.classifier",
    "phoenix.intelligence.entities",
    "phoenix.intelligence.selector_repair",
]


@pytest.mark.parametrize("module_name", _MODULES)
def test_module_imports(module_name: str) -> None:
    """Every Phoenix Engine module should import without errors."""
    importlib.import_module(module_name)
