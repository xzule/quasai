import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
from typer.testing import CliRunner

from quasai.cli import app
from quasai.types import Requirements

runner = CliRunner()


def test_generate_with_output(tmp_path: Path) -> None:
    input_path = tmp_path / "input.md"
    input_path.write_text("# Test")
    out_path = tmp_path / "result.json"

    with patch("quasai.cli.parse_markdown", return_value=Requirements(title="")):
        with patch("quasai.cli.generate_cases", new_callable=AsyncMock, return_value=[]):
            with patch("quasai.cli.to_json") as mock_serialize:
                result = runner.invoke(app, [str(input_path), "-o", str(out_path)])

    assert result.exit_code == 0
    mock_serialize.assert_called_once()


def test_generate_default_output(tmp_path: Path) -> None:
    input_path = tmp_path / "input.md"
    input_path.write_text("# Test")

    with patch("quasai.cli.parse_markdown", return_value=Requirements(title="")):
        with patch("quasai.cli.generate_cases", new_callable=AsyncMock, return_value=[]):
            with patch("quasai.cli.to_json") as mock_serialize:
                result = runner.invoke(app, [str(input_path)])

    assert result.exit_code == 0
    mock_serialize.assert_called_once()
    args, _ = mock_serialize.call_args
    assert args[1].endswith("input.json")


def test_generate_file_not_found(tmp_path: Path) -> None:
    result = runner.invoke(app, [str(tmp_path / "nonexistent.md")])

    assert result.exit_code == 1


def test_generate_parse_error(tmp_path: Path) -> None:
    path = tmp_path / "empty.md"
    path.write_text("")

    result = runner.invoke(app, [str(path)])

    assert result.exit_code == 1


def test_generate_llm_connect_error(tmp_path: Path) -> None:
    input_path = tmp_path / "input.md"
    input_path.write_text("# Test")

    with patch("quasai.cli.parse_markdown", return_value=Requirements(title="")):
        with patch(
            "quasai.cli.generate_cases",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            result = runner.invoke(app, [str(input_path)])

    assert result.exit_code == 1


def test_generate_llm_json_error(tmp_path: Path) -> None:
    input_path = tmp_path / "input.md"
    input_path.write_text("# Test")

    with patch("quasai.cli.parse_markdown", return_value=Requirements(title="")):
        with patch(
            "quasai.cli.generate_cases",
            new_callable=AsyncMock,
            side_effect=json.JSONDecodeError("Expecting value", "", 0),
        ):
            result = runner.invoke(app, [str(input_path)])

    assert result.exit_code == 1


def test_generate_progress_messages(tmp_path: Path) -> None:
    input_path = tmp_path / "input.md"
    input_path.write_text("# Test")

    with patch("quasai.cli.parse_markdown", return_value=Requirements(title="")):
        with patch("quasai.cli.generate_cases", new_callable=AsyncMock, return_value=[]):
            with patch("quasai.cli.to_json"):
                result = runner.invoke(app, [str(input_path)])

    assert result.exit_code == 0
    assert "Парсинг требований" in result.stdout
    assert "Генерация box-сценариев" in result.stdout
    assert "Сохранение результата" in result.stdout
