"""Data models for Phoenix Engine."""

from __future__ import annotations

from phoenix.models.classification import URLClassification
from phoenix.models.config import Config
from phoenix.models.document import HTMLDocument, RawResponse
from phoenix.models.output import (
    CollectionResult,
    Diagnostics,
    ErrorRecord,
    ScrapingResult,
    UnifiedOutput,
)
from phoenix.models.session import Session
from phoenix.models.strategy import ScrapingStrategy, StrategySelection
from phoenix.options import CollectionOptions, ScrapingOptions

__all__ = [
    "CollectionOptions",
    "CollectionResult",
    "Config",
    "Diagnostics",
    "ErrorRecord",
    "HTMLDocument",
    "RawResponse",
    "ScrapingOptions",
    "ScrapingResult",
    "ScrapingStrategy",
    "Session",
    "StrategySelection",
    "URLClassification",
    "UnifiedOutput",
]
