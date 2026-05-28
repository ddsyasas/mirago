"""CLI entry point for mirago. Run via `mirago check file.py`."""

from pathlib import Path

import typer
from rich.console import Console

from mirago import __version__
from mirago.checker import check_file

app = typer.Typer(
    name="mirago",
    help="Catch AI code hallucinations before they ship.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"mirago {__version__}")
        raise typer.Exit()


@app.callback()
def _main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """mirago: the linter for AI-generated code."""


@app.command()
def check(
    files: list[Path] = typer.Argument(..., help="Python files to check."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable the PyPI lookup cache."),
) -> None:
    """Scan Python files for AI-hallucinated imports."""
    total_issues = 0
    checked_files = 0

    for file_path in files:
        if not file_path.exists():
            console.print(f"[red]error[/red]  file not found: {file_path}")
            raise typer.Exit(code=2)

        if file_path.suffix != ".py":
            console.print(f"[yellow]skip[/yellow]   non-Python file: {file_path}")
            continue

        checked_files += 1
        issues = check_file(file_path, use_cache=not no_cache)
        total_issues += len(issues)

        if issues:
            plural = "s" if len(issues) != 1 else ""
            console.print(
                f"\n[bold red]🚨 {len(issues)} hallucination{plural} in {file_path}[/bold red]\n"
            )
            for issue in issues:
                console.print(f"  [bold]Line {issue.line}:[/bold] {issue.code}")
                console.print(f"    [red]→[/red] {issue.message}")
                if issue.suggestion:
                    console.print(f"    [green]suggestion:[/green] {issue.suggestion}")
                console.print()
        else:
            console.print(f"[green]✓[/green] {file_path}: no hallucinations found")

    if total_issues > 0:
        console.print(
            f"\n[bold red]Found {total_issues} issue(s) across {checked_files} file(s).[/bold red]"
        )
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
