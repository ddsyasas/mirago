"""CLI entry point for mirago. Run via `mirago check file.py`."""

import json
import re
import sys
from pathlib import Path

import typer
from rich.console import Console

from mirago import __version__, suggest
from mirago.checker import Issue, check_file

_PACKAGE_RE = re.compile(r"Package '([^']+)'")

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


def _apply_fixes(file_path: Path, errors: list[Issue]) -> None:
    """Interactively replace misspelled imports with their suggestions."""
    fixable = [i for i in errors if i.suggestion]
    if not fixable:
        return
    if not sys.stdin.isatty():
        console.print("[yellow]--fix needs an interactive terminal; skipping.[/yellow]")
        return

    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = False
    for issue in fixable:
        match = _PACKAGE_RE.search(issue.message)
        if not match:
            continue
        bad = match.group(1)
        if typer.confirm(f"Replace '{bad}' with '{issue.suggestion}' on line {issue.line}?"):
            idx = issue.line - 1
            if 0 <= idx < len(lines) and issue.suggestion is not None:
                lines[idx] = lines[idx].replace(bad, issue.suggestion, 1)
                changed = True
    if changed:
        file_path.write_text("".join(lines), encoding="utf-8")
        console.print("[green]applied fixes[/green]")


@app.command()
def check(
    files: list[Path] = typer.Argument(..., help="Python files to check."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable the PyPI lookup cache."),
    json_output: bool = typer.Option(
        False, "--json", help="Output results as JSON instead of formatted text."
    ),
    fail_on: str = typer.Option(
        "error", "--fail-on", help="Minimum severity that fails the run: 'error' or 'warning'."
    ),
    fix: bool = typer.Option(
        False, "--fix", help="Interactively replace misspelled imports with suggestions."
    ),
) -> None:
    """Scan Python files for hallucinated (non-existent) or suspicious imports."""
    if fail_on not in ("error", "warning"):
        console.print("[red]error[/red]  --fail-on must be 'error' or 'warning'")
        raise typer.Exit(code=2)
    fail_on_warning = fail_on == "warning"

    suggester = suggest.default_suggester(use_cache=not no_cache)
    error_count = 0
    warning_count = 0
    checked_files = 0
    json_results: list[dict[str, object]] = []

    for file_path in files:
        if not file_path.exists():
            if not json_output:
                console.print(f"[red]error[/red]  file not found: {file_path}")
            raise typer.Exit(code=2)

        if file_path.suffix != ".py":
            if not json_output:
                console.print(f"[yellow]skip[/yellow]   non-Python file: {file_path}")
            continue

        checked_files += 1
        issues = check_file(file_path, use_cache=not no_cache, suggester=suggester)
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        error_count += len(errors)
        warning_count += len(warnings)

        if json_output:
            json_results.extend(
                {
                    "file": str(file_path),
                    "line": issue.line,
                    "code": issue.code,
                    "message": issue.message,
                    "severity": issue.severity,
                    "suggestion": issue.suggestion,
                    "signals": issue.signals,
                }
                for issue in issues
            )
            continue

        if errors:
            plural = "s" if len(errors) != 1 else ""
            console.print(
                f"\n[bold red]🚨 {len(errors)} hallucination{plural} in {file_path}[/bold red]\n"
            )
            for issue in errors:
                console.print(f"  [bold]Line {issue.line}:[/bold] {issue.code}")
                console.print(f"    [red]→[/red] {issue.message}")
                if issue.suggestion:
                    console.print(f"    [green]suggestion:[/green] {issue.suggestion}")
                console.print()

        if warnings:
            plural = "s" if len(warnings) != 1 else ""
            console.print(
                f"\n[bold yellow]⚠️  {len(warnings)} suspicious package{plural} "
                f"in {file_path}[/bold yellow]\n"
            )
            for issue in warnings:
                console.print(f"  [bold]Line {issue.line}:[/bold] {issue.code}")
                console.print(f"    [yellow]→[/yellow] {issue.message}")
                console.print()

        if not errors and not warnings:
            console.print(f"[green]✓[/green] {file_path}: no hallucinations found")

        if fix and errors:
            _apply_fixes(file_path, errors)

    if json_output:
        print(json.dumps(json_results, indent=2))
        if error_count or (warning_count and fail_on_warning):
            raise typer.Exit(code=1)
        return

    if error_count:
        console.print(
            f"\n[bold red]Found {error_count} issue(s) across {checked_files} file(s).[/bold red]"
        )
    if warning_count:
        plural = "s" if warning_count != 1 else ""
        console.print(
            f"[bold yellow]{warning_count} suspicious package{plural} flagged "
            f"(exists but low-trust).[/bold yellow]"
        )

    if error_count or (warning_count and fail_on_warning):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
