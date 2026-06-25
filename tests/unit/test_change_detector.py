"""Unit tests for the change detector."""

from __future__ import annotations

import pytest

from phoenix.infrastructure.storage import SQLiteStorageBackend
from phoenix.intelligence.change_detector import ChangeDetector
from phoenix.models.document import RawResponse
from phoenix.models.output import UnifiedOutput


@pytest.fixture
def storage() -> SQLiteStorageBackend:
    """Return an in-memory SQLite storage backend."""
    backend = SQLiteStorageBackend(path=":memory:")
    try:
        yield backend
    finally:
        backend.close()


def test_fingerprint_stable_for_equivalent_html() -> None:
    """The structural fingerprint is stable across text changes."""
    html1 = '<html><body><div id="a" class="x"><p>Hello</p></div></body></html>'
    html2 = '<html><body><div id="b" class="y"><p>World</p></div></body></html>'

    detector = ChangeDetector()

    assert detector.structural_fingerprint(html1) == detector.structural_fingerprint(html2)


def test_fingerprint_changes_for_layout_rewrite() -> None:
    """A different tag hierarchy produces a different fingerprint."""
    html1 = "<html><body><article><h1>Title</h1></article></body></html>"
    html2 = "<html><body><div><h1>Title</h1></div></body></html>"

    detector = ChangeDetector()

    assert detector.structural_fingerprint(html1) != detector.structural_fingerprint(html2)


def test_selector_snapshot_extracts_field_selectors() -> None:
    """Selector snapshots capture per-field selector results."""
    extracted = {
        "title": {"selector_used": "h1", "matched": True, "confidence": 1.0},
        "text": {"selector_used": ".content", "matched": False},
        "selectors_used": ["h1", ".content"],
    }

    snapshot = ChangeDetector.selector_snapshot(extracted)

    assert snapshot["title"]["selector"] == "h1"
    assert snapshot["title"]["matched"] is True
    assert snapshot["text"]["matched"] is False
    assert snapshot["_page"]["selectors"] == ["h1", ".content"]


@pytest.mark.asyncio
async def test_detect_creates_baseline_on_first_scrape(storage: SQLiteStorageBackend) -> None:
    """The first scrape for a URL creates a baseline and emits no alert."""
    detector = ChangeDetector(storage=storage)
    raw = RawResponse(
        url="https://example.com/post/1",
        status_code=200,
        html="<html><body><h1>Title</h1></body></html>",
        strategy="http",
    )

    alert = await detector.detect(
        url=raw.url,
        platform="generic",
        content_type="article",
        raw_response=raw,
        extracted={"title": {"selector_used": "h1", "matched": True}},
        output=UnifiedOutput(url=raw.url, platform="generic", title="Title"),
    )

    assert alert is None
    baseline = storage.get_latest_baseline(raw.url)
    assert baseline is not None
    assert baseline["structural_fingerprint"] == detector.structural_fingerprint(raw.html)


@pytest.mark.asyncio
async def test_detect_structural_change_alert(storage: SQLiteStorageBackend) -> None:
    """A changed DOM skeleton produces a structural_change alert."""
    detector = ChangeDetector(storage=storage)
    url = "https://example.com/post/1"
    baseline_html = "<html><body><h1>Title</h1></body></html>"
    changed_html = "<html><body><div><h1>Title</h1></div></body></html>"

    await detector.detect(
        url=url,
        platform="generic",
        content_type="article",
        raw_response=RawResponse(url=url, status_code=200, html=baseline_html, strategy="http"),
        extracted={"title": {"selector_used": "h1", "matched": True}},
        output=UnifiedOutput(url=url, platform="generic", title="Title"),
    )

    alert = await detector.detect(
        url=url,
        platform="generic",
        content_type="article",
        raw_response=RawResponse(url=url, status_code=200, html=changed_html, strategy="http"),
        extracted={"title": {"selector_used": "h1", "matched": True}},
        output=UnifiedOutput(url=url, platform="generic", title="Title"),
    )

    assert alert is not None
    assert "structural_change" in alert.alert_type
    assert alert.severity == "warning"


@pytest.mark.asyncio
async def test_detect_selector_degradation_alert(storage: SQLiteStorageBackend) -> None:
    """A selector that previously matched but now fails triggers degradation."""
    detector = ChangeDetector(storage=storage)
    url = "https://example.com/post/1"
    html = "<html><body><h1>Title</h1></body></html>"

    await detector.detect(
        url=url,
        platform="generic",
        content_type="article",
        raw_response=RawResponse(url=url, status_code=200, html=html, strategy="http"),
        extracted={"title": {"selector_used": "h1", "matched": True, "confidence": 1.0}},
        output=UnifiedOutput(url=url, platform="generic", title="Title"),
    )

    alert = await detector.detect(
        url=url,
        platform="generic",
        content_type="article",
        raw_response=RawResponse(url=url, status_code=200, html=html, strategy="http"),
        extracted={"title": {"selector_used": "h1", "matched": False, "confidence": 0.0}},
        output=UnifiedOutput(url=url, platform="generic", title=None),
    )

    assert alert is not None
    assert "selector_degradation" in alert.alert_type


@pytest.mark.asyncio
async def test_detect_size_anomaly_alert(storage: SQLiteStorageBackend) -> None:
    """A large HTML size delta triggers a size_anomaly alert."""
    detector = ChangeDetector(storage=storage)
    url = "https://example.com/post/1"

    await detector.detect(
        url=url,
        platform="generic",
        content_type="article",
        raw_response=RawResponse(url=url, status_code=200, html="<html>a</html>", strategy="http"),
        extracted={},
        output=UnifiedOutput(url=url, platform="generic"),
    )

    large_html = "<html>" + ("x" * 2000) + "</html>"
    alert = await detector.detect(
        url=url,
        platform="generic",
        content_type="article",
        raw_response=RawResponse(
            url=url,
            status_code=200,
            html=large_html,
            strategy="http",
        ),
        extracted={},
        output=UnifiedOutput(url=url, platform="generic"),
    )

    assert alert is not None
    assert "size_anomaly" in alert.alert_type


@pytest.mark.asyncio
async def test_detect_no_alert_when_unchanged(storage: SQLiteStorageBackend) -> None:
    """Identical scrapes do not produce alerts after the baseline is set."""
    detector = ChangeDetector(storage=storage)
    url = "https://example.com/post/1"
    html = "<html><body><h1>Title</h1></body></html>"

    await detector.detect(
        url=url,
        platform="generic",
        content_type="article",
        raw_response=RawResponse(url=url, status_code=200, html=html, strategy="http"),
        extracted={"title": {"selector_used": "h1", "matched": True}},
        output=UnifiedOutput(url=url, platform="generic", title="Title"),
    )

    alert = await detector.detect(
        url=url,
        platform="generic",
        content_type="article",
        raw_response=RawResponse(url=url, status_code=200, html=html, strategy="http"),
        extracted={"title": {"selector_used": "h1", "matched": True}},
        output=UnifiedOutput(url=url, platform="generic", title="Title"),
    )

    assert alert is None
