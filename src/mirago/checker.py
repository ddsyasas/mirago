"""Main checker: combines AST parsing with PyPI existence lookups."""

from dataclasses import dataclass
from pathlib import Path

from mirago.parser import extract_imports
from mirago.pypi import package_exists_on_pypi


@dataclass
class Issue:
    """A single hallucination found in a source file."""

    line: int
    code: str
    message: str
    suggestion: str | None = None


def check_file(file_path: Path, use_cache: bool = True) -> list[Issue]:
    """Check one Python file for hallucinated imports.

    Returns a list of Issue objects, empty if nothing was found.
    Each unique package is only looked up once per call.
    """
    issues: list[Issue] = []
    imports = extract_imports(file_path)

    # Memoize within this file so we don't hit PyPI more than once per package.
    seen: dict[str, bool] = {}

    for imp in imports:
        if imp.module not in seen:
            seen[imp.module] = package_exists_on_pypi(imp.module, use_cache=use_cache)

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
