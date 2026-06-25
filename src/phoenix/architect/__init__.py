"""PhoenixArchitect autonomous adapter-generation components."""

from __future__ import annotations

from phoenix.architect.critic import AdapterCritic, AdapterValidationReport
from phoenix.architect.explorer import BrowserExplorer, PageSnapshot
from phoenix.architect.orchestrator import PhoenixArchitect

__all__ = [
    "AdapterCritic",
    "AdapterValidationReport",
    "BrowserExplorer",
    "PageSnapshot",
    "PhoenixArchitect",
]
