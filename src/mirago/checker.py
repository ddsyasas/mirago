"""Main checker: combines AST parsing with PyPI existence lookups."""

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from mirago.lockfile import Lockfile, find_lockfile
from mirago.parser import extract_imports_from_source
from mirago.registry import PackageInfo, PyPIRegistry, Registry
from mirago.risk import Verdict, assess

Suggester = Callable[[str], "str | None"]


@dataclass
class Issue:
    """A single problem found in a source file."""

    line: int
    code: str
    message: str
    suggestion: str | None = None
    severity: str = "error"  # "error" (doesn't exist) | "warning" (suspicious-but-exists)
    signals: dict[str, object] = field(default_factory=dict)


def check_source(
    source: str,
    filename: str = "<string>",
    registry: Registry | None = None,
    use_cache: bool = True,
    metadata: bool = True,
    lockfile: Lockfile | None = None,
    suggester: Suggester | None = None,
) -> list[Issue]:
    """Check Python source text for hallucinated or suspicious imports.

    Returns a list of Issue objects, empty if nothing was found. Each unique package is
    only looked up once per call.

    - `metadata=True` grades risk (existence + age + downloads + lockfile). `metadata=False`
      is an existence-only fast path (only flags non-existent packages) for latency-sensitive
      callers such as a guardrail hook.
    - `lockfile` supplies the trust signal; defaults to "none found".
    - `suggester` attaches a "did you mean" suggestion to errors; optional (kept out of the
      engine so unit tests stay offline).
    """
    if registry is None:
        registry = PyPIRegistry(use_cache=use_cache)
    if lockfile is None:
        lockfile = Lockfile(exists=False)

    issues: list[Issue] = []
    imports = extract_imports_from_source(source, filename)

    # Memoize within this run so we don't hit the registry more than once per package.
    seen: dict[str, Verdict | None] = {}

    for imp in imports:
        if imp.module not in seen:
            if metadata:
                info = registry.info(imp.module)
            else:
                info = PackageInfo(exists=registry.exists(imp.module))
            seen[imp.module] = assess(imp.module, info, lockfile)

        verdict = seen[imp.module]
        if verdict is None:
            continue

        suggestion = None
        if verdict.severity == "error" and suggester is not None:
            suggestion = suggester(imp.module)

        issues.append(
            Issue(
                line=imp.line,
                code=imp.code,
                message=verdict.message,
                suggestion=suggestion,
                severity=verdict.severity,
                signals=verdict.signals,
            )
        )

    return issues


def check_file(
    file_path: Path,
    use_cache: bool = True,
    metadata: bool = True,
    suggester: Suggester | None = None,
) -> list[Issue]:
    """Check one Python file. Thin wrapper over check_source that reads the file and
    locates the nearest project lockfile (the trust signal)."""
    source = file_path.read_text(encoding="utf-8")
    lockfile = find_lockfile(file_path) if metadata else None
    return check_source(
        source,
        str(file_path),
        use_cache=use_cache,
        metadata=metadata,
        lockfile=lockfile,
        suggester=suggester,
    )
