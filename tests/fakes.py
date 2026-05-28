"""Test doubles for mirago."""

from __future__ import annotations


class FakeRegistry:
    """In-memory Registry for offline tests.

    `known` maps package name -> exists. Unknown names default to False (does not
    exist). Records every lookup in `calls` so tests can assert on memoization.
    """

    def __init__(self, known: dict[str, bool]) -> None:
        self.known = known
        self.calls: list[str] = []

    def exists(self, name: str) -> bool:
        self.calls.append(name)
        return self.known.get(name, False)
