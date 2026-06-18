from pathlib import Path

import pytest

from quasai.parser import count_items, parse_markdown
from quasai.types import Requirements, Section


def test_parse_basic_markdown(tmp_path: Path) -> None:
    content = """# My Requirements

## Section 1
Some description text.

- First requirement
- Second requirement

## Section 2
- Only list items"""
    path = tmp_path / "input.md"
    path.write_text(content)

    result = parse_markdown(str(path))

    assert result.title == "My Requirements"
    assert len(result.sections) == 2
    assert result.sections[0].heading == "Section 1"
    assert result.sections[1].heading == "Section 2"


def test_parse_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.md"
    path.write_text("")

    with pytest.raises(ValueError, match="Файл не содержит требований"):
        parse_markdown(str(path))


def test_parse_nested_headings(tmp_path: Path) -> None:
    content = """# Project

## Chapter 1
### Subsection A
Detail text.

### Subsection B
More detail.

## Chapter 2
Flat content."""
    path = tmp_path / "nested.md"
    path.write_text(content)

    result = parse_markdown(str(path))

    assert result.title == "Project"
    assert len(result.sections) == 2
    assert len(result.sections[0].subsections) == 2
    assert result.sections[0].subsections[0].heading == "Subsection A"


def test_parse_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        parse_markdown("/nonexistent/path.md")


def test_parse_no_headings(tmp_path: Path) -> None:
    content = "Just a paragraph.\n\nAnother paragraph without headings."
    path = tmp_path / "noheadings.md"
    path.write_text(content)

    with pytest.raises(ValueError, match="Файл не содержит требований"):
        parse_markdown(str(path))


def test_count_items() -> None:
    assert count_items("1.1 (P0) First.\n1.2 (P0) Second.\n1.3 (P0) Third.") == 3


def test_count_items_empty() -> None:
    assert count_items("") == 0


def test_count_items_no_numbered() -> None:
    assert count_items("Just text.") == 0


def test_count_items_multi_level() -> None:
    content = "4.1.1 (P1) Sub-item.\n6.2.1 (P0) Deep.\n8.1 User scenario."
    assert count_items(content) == 3
