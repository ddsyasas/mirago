"""Package-registry adapters.

The seam that lets the checker ask "does this package exist?" without knowing which
ecosystem answers. PyPI today; npm later; a fake in tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mirago.pypi import fetch_metadata, package_exists_on_pypi


@dataclass
class PackageInfo:
    """Existence plus the risk metadata the v0.2 scorer grades on.

    `None` for a signal means "unknown" — which the scorer treats as safe (fail-open).
    """

    exists: bool
    age_days: int | None = None
    downloads_last_month: int | None = None


class Registry(Protocol):
    """A package registry the checker can query."""

    def exists(self, name: str) -> bool:
        """Return True if a package by this name exists (or should be treated as existing)."""
        ...

    def info(self, name: str) -> PackageInfo:
        """Return existence + risk metadata for a package."""
        ...


class PyPIRegistry:
    """PyPI-backed registry.

    Wraps the pypi module, which owns the Python stdlib short-circuit and the on-disk
    cache. The stdlib short-circuit lives here (not in the engine) because it is
    Python-specific; a future npm registry would not have it.
    """

    def __init__(self, use_cache: bool = True) -> None:
        self._use_cache = use_cache

    def exists(self, name: str) -> bool:
        # Existence-only fast path (e.g. for a latency-sensitive guardrail hook):
        # one request, no download lookup.
        return package_exists_on_pypi(name, use_cache=self._use_cache)

    def info(self, name: str) -> PackageInfo:
        meta = fetch_metadata(name, use_cache=self._use_cache)
        return PackageInfo(
            exists=meta["exists"],
            age_days=meta["age_days"],
            downloads_last_month=meta["downloads_last_month"],
        )
