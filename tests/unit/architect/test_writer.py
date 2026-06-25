"""Tests for the generated adapter writer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from phoenix.architect.writer import GeneratedAdapterWriter

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def writer(tmp_path: Path) -> GeneratedAdapterWriter:
    return GeneratedAdapterWriter(output_dir=tmp_path)


def test_write_and_read(writer: GeneratedAdapterWriter) -> None:
    code = "class ExampleAdapter:\n    pass\n"
    path = writer.write("Example-Platform", code)
    assert path.exists()
    assert path.name == "example_platform.py"
    assert writer.read("Example-Platform") == code


def test_write_rejects_empty_platform(writer: GeneratedAdapterWriter) -> None:
    with pytest.raises(ValueError, match="Invalid platform identifier"):
        writer.write("", "code")


def test_write_rejects_path_escape(writer: GeneratedAdapterWriter) -> None:
    with pytest.raises(ValueError, match="contains path separators"):
        writer.write("../escaped", "code")


def test_list_adapters(writer: GeneratedAdapterWriter) -> None:
    writer.write("alpha", "code")
    writer.write("beta", "code")
    assert {p.name for p in writer.list_adapters()} == {"alpha.py", "beta.py"}


def test_to_dict(writer: GeneratedAdapterWriter) -> None:
    writer.write("gamma", "code")
    summary = writer.to_dict()
    assert summary["output_dir"] == str(writer.output_dir)
    assert summary["adapter_count"] == 1
