"""Main checker: combines AST parsing with PyPI existence lookups."""

from dataclasses import dataclass, field
from pathlib import Path

from mirago.parser import extract_imports_from_source
from mirago.registry import PyPIRegistry, Registry


@dataclass
class Issue:
    """A single hallucination found in a source file."""

    line: int
    code: str
    message: str
    suggestion: str | None = None
    severity: str = "error"  # "error" | "warning" | "info" — v0.2 grades risk with this
    signals: dict[str, object] = field(default_factory=dict)  # populated by the v0.2 metadata tier


def check_source(
    source: str,
    filename: str = "<string>",
    registry: Registry | None = None,
    use_cache: bool = True,
) -> list[Issue]:
    """Check Python source text for hallucinated imports.

    Returns a list of Issue objects, empty if nothing was found.
    Each unique package is only looked up once per call. Pass a custom `registry`
    to query a different ecosystem (or a fake in tests); defaults to PyPI.
    """
    if registry is None:
        registry = PyPIRegistry(use_cache=use_cache)

    issues: list[Issue] = []
    imports = extract_imports_from_source(source, filename)

    # Memoize within this run so we don't hit the registry more than once per package.
    seen: dict[str, bool] = {}

    for imp in imports:
        if imp.module not in seen:
            seen[imp.module] = registry.exists(imp.module)

        if not seen[imp.module]:
            issues.append(
                Issue(
                    line=imp.line,
                    code=imp.code,
                    message=f"Package '{imp.module}' does not exist on PyPI",
                    suggestion=None,
                )
            )

    return issues


def check_file(file_path: Path, use_cache: bool = True) -> list[Issue]:
    """Check one Python file for hallucinated imports.

    Thin wrapper over check_source that reads the file from disk.
    """
    source = file_path.read_text(encoding="utf-8")
    return check_source(source, str(file_path), use_cache=use_cache)
