"""Unit tests for the fixture generator."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from phoenix.architect.explorer import PageSnapshot
from phoenix.architect.fixture_generator import FixtureGenerator


@pytest.fixture
def generator(tmp_path: Path) -> FixtureGenerator:
    """Return a fixture generator writing into ``tmp_path``."""
    return FixtureGenerator(
        fixtures_dir=tmp_path / "fixtures",
        tests_dir=tmp_path / "unit",
    )


def test_generate_creates_html_fixtures(generator: FixtureGenerator, tmp_path: Path) -> None:
    """HTML snapshots are written to the platform fixture directory."""
    snapshots = [
        PageSnapshot(url="https://example.com/1", html="<h1>One</h1>", page_number=1),
        PageSnapshot(url="https://example.com/2", html="<h1>Two</h1>", page_number=2),
    ]

    fixture_set = generator.generate("example_site", snapshots)

    assert fixture_set.fixture_dir.exists()
    assert (fixture_set.fixture_dir / "page_1.html").read_text() == "<h1>One</h1>"
    assert (fixture_set.fixture_dir / "page_2.html").read_text() == "<h1>Two</h1>"


def test_generate_creates_meta_yaml(generator: FixtureGenerator, tmp_path: Path) -> None:
    """A meta.yaml is created with expected fields for each snapshot."""
    snapshots = [PageSnapshot(url="https://example.com/1", html="<h1>One</h1>", page_number=1)]
    extracted = {"title": "One", "media_urls": ["https://example.com/img.png"]}

    fixture_set = generator.generate("example_site", snapshots, [extracted])

    assert fixture_set.meta_path.exists()
    content = fixture_set.meta_path.read_text(encoding="utf-8")
    assert "source_url: https://example.com/1" in content
    assert "fixture: page_1.html" in content
    assert "expected_fields" in content


def test_generate_creates_unit_test_file(generator: FixtureGenerator, tmp_path: Path) -> None:
    """A runnable-looking unit test file is generated."""
    snapshots = [PageSnapshot(url="https://example.com/1", html="<h1>One</h1>", page_number=1)]

    fixture_set = generator.generate("example_site", snapshots)

    assert fixture_set.test_path.exists()
    source = fixture_set.test_path.read_text(encoding="utf-8")
    assert "ExampleSiteAdapter" in source
    assert "from phoenix.adapters.generated.example_site import ExampleSiteAdapter" in source
    assert "test_extract_required_fields" in source
    assert "test_normalize_returns_unified_output" in source


def test_generated_test_compiles(generator: FixtureGenerator, tmp_path: Path) -> None:
    """The generated test file is syntactically valid Python."""
    snapshots = [PageSnapshot(url="https://example.com/1", html="<h1>One</h1>", page_number=1)]

    fixture_set = generator.generate("example_site", snapshots)
    source = fixture_set.test_path.read_text(encoding="utf-8")

    compile(source, fixture_set.test_path.name, "exec")


def test_generate_requires_matching_output_length(generator: FixtureGenerator) -> None:
    """Mismatched snapshots/extracted_outputs lengths raise ValueError."""
    snapshots = [PageSnapshot(url="https://example.com/1", html="<h1>One</h1>", page_number=1)]

    with pytest.raises(ValueError, match="same length"):
        generator.generate("example_site", snapshots, [{}, {}])
