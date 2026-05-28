"""Test doubles for mirago."""

from __future__ import annotations

from mirago.registry import PackageInfo


class FakeRegistry:
    """In-memory Registry for offline tests.

    `packages` maps name -> PackageInfo, or name -> bool as a shorthand for
    PackageInfo(exists=bool). Unknown names default to "does not exist". Records every
    lookup in `calls` so tests can assert on memoization.
    """

    def __init__(self, packages: dict[str, PackageInfo | bool]) -> None:
        self._packages: dict[str, PackageInfo] = {
            name: (value if isinstance(value, PackageInfo) else PackageInfo(exists=bool(value)))
            for name, value in packages.items()
        }
        self.calls: list[str] = []

    def info(self, name: str) -> PackageInfo:
        self.calls.append(name)
        return self._packages.get(name, PackageInfo(exists=False))

    def exists(self, name: str) -> bool:
        return self.info(name).exists
