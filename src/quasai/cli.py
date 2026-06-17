import typer

app = typer.Typer()


@app.command()
def generate(
    input: str = typer.Argument(..., help="Path to input Markdown file"),
    output: str | None = typer.Option(None, "-o", help="Path to output JSON file"),
) -> None:
    ...
