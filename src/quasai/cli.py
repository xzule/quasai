import asyncio
import json
import sys
from pathlib import Path

import httpx
import typer

from quasai.generator import OllamaProvider, generate as generate_cases
from quasai.parser import parse_markdown
from quasai.serializer import to_json

app = typer.Typer()


@app.command()
def generate(
    input: str = typer.Argument(..., help="Path to input Markdown file"),
    output: str | None = typer.Option(None, "-o", help="Path to output JSON file"),
) -> None:
    in_path = Path(input)
    if not in_path.exists():
        print("Файл не найден", file=sys.stderr)
        raise typer.Exit(code=1)

    out_path = Path(output) if output else in_path.with_suffix(".json")

    print("Парсинг требований")
    try:
        requirements = parse_markdown(str(in_path))
    except ValueError as e:
        print(e, file=sys.stderr)
        raise typer.Exit(code=1)

    provider = OllamaProvider()
    try:
        cases = asyncio.run(generate_cases(requirements, provider, progress=lambda msg: print(msg, flush=True)))
    except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadTimeout):
        print("Ошибка подключения к LLM", file=sys.stderr)
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as e:
        print(f"Ошибка LLM (HTTP {e.response.status_code})", file=sys.stderr)
        raise typer.Exit(code=1)
    except json.JSONDecodeError as e:
        print(f"Ошибка разбора ответа LLM: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

    print("Сохранение результата")
    to_json(cases, str(out_path))
    print(f"Результат сохранён в {out_path}")
