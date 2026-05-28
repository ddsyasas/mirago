"""Package-registry adapters.

The seam that lets the checker ask "does this package exist?" without knowing which
ecosystem answers. PyPI today; npm later; a fake in tests.
"""

from __future__ import annotations

from typing import Protocol

from mirago.pypi import package_exists_on_pypi


class Registry(Protocol):
    """A package registry the checker can query for existence."""

    def exists(self, name: str) -> bool:
        """Return True if a package by this name exists (or should be treated as existing)."""
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
        return package_exists_on_pypi(name, use_cache=self._use_cache)
