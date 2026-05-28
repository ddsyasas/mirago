"""'Did you mean' suggestions for non-existent package names.

Matches a misspelled import against a bundled list of well-known PyPI packages, using
stdlib difflib. The corpus is deliberately *popular-only*, not all of PyPI: suggesting an
obscure package as a "did you mean" would be low quality and could even nudge a user
toward a typosquat. No network, no extra dependency.
"""

from __future__ import annotations

import difflib
from collections.abc import Callable
from functools import lru_cache
from importlib import resources

_CUTOFF = 0.84


@lru_cache(maxsize=1)
def load_corpus() -> tuple[str, ...]:
    try:
        text = (
            resources.files("mirago")
            .joinpath("data/popular_packages.txt")
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, OSError):
        return ()
    return tuple(
        line.strip().lower()
        for line in text.splitlines()
        if line.strip() and not line.startswith("#")
    )


def did_you_mean(name: str, corpus: list[str] | tuple[str, ...] | None = None) -> str | None:
    """Closest well-known package name to `name`, or None. Pure (no I/O when `corpus` given)."""
    names = corpus if corpus is not None else load_corpus()
    if not names:
        return None
    target = name.lower()
    # Cheap prefilter (same first char, similar length) keeps difflib fast.
    candidates = [
        c for c in names if c[:1] == target[:1] and abs(len(c) - len(target)) <= 2
    ]
    matches = difflib.get_close_matches(target, candidates, n=1, cutoff=_CUTOFF)
    return matches[0] if matches else None


def default_suggester(use_cache: bool = True) -> Callable[[str], str | None]:
    """A name -> suggestion function backed by the bundled popular-packages corpus.

    `use_cache` is accepted for call-site symmetry with the registry; the corpus is
    bundled and offline, so there is nothing to cache.
    """
    return did_you_mean
