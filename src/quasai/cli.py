import asyncio
import json
import sys
from pathlib import Path

import httpx
import typer

from quasai.generator import OllamaProvider, generate as generate_cases
from quasai.parser import parse_markdown
from quasai.serializer import to_csv, to_json

app = typer.Typer()


@app.command()
def generate(
    input: str = typer.Argument(..., help="Path to input Markdown file"),
) -> None:
    in_path = Path(input)
    if not in_path.exists():
        print("File not found", file=sys.stderr, flush=True)
        raise typer.Exit(code=1)

    stem = in_path.stem
    out_dir = Path("/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / f"{stem}.json"
    out_csv = out_dir / f"{stem}.csv"

    print("Parsing requirements", flush=True)
    try:
        requirements = parse_markdown(str(in_path))
    except ValueError as e:
        print(e, file=sys.stderr, flush=True)
        raise typer.Exit(code=1)

    provider = OllamaProvider()
    try:
        cases = asyncio.run(generate_cases(requirements, provider, progress=lambda msg: print(msg, flush=True)))
    except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadTimeout):
        print("LLM connection failed", file=sys.stderr, flush=True)
        raise typer.Exit(code=1)
    except httpx.HTTPStatusError as e:
        print(f"LLM error (HTTP {e.response.status_code})", file=sys.stderr, flush=True)
        raise typer.Exit(code=1)
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM response: {e}", file=sys.stderr, flush=True)
        raise typer.Exit(code=1)

    print("Saving results", flush=True)
    to_json(cases, str(out_json))
    try:
        to_csv(cases, str(out_csv))
    except PermissionError:
        print(f"Warning: could not write {out_csv.name}", file=sys.stderr, flush=True)
    print("Results saved in:", flush=True)
    print(f"  ./output/{stem}.json", flush=True)
    print(f"  ./output/{stem}.csv", flush=True)
