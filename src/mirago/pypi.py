"""PyPI existence checker with on-disk cache and stdlib short-circuit."""

from __future__ import annotations

import contextlib
import json
import sys
import time
from pathlib import Path

import httpx
from platformdirs import user_cache_dir

# Stdlib modules don't need a PyPI lookup. Python 3.10+ provides this set built-in.
_STDLIB: set[str] = (
    set(sys.stdlib_module_names)
    if hasattr(sys, "stdlib_module_names")
    else {
        "abc", "argparse", "ast", "asyncio", "base64", "collections", "contextlib",
        "copy", "csv", "dataclasses", "datetime", "decimal", "enum", "functools",
        "glob", "hashlib", "http", "io", "itertools", "json", "logging", "math",
        "os", "pathlib", "pickle", "random", "re", "shutil", "socket", "sqlite3",
        "string", "subprocess", "sys", "tempfile", "threading", "time", "typing",
        "urllib", "uuid", "warnings", "xml", "zipfile",
    }
)

CACHE_DIR = Path(user_cache_dir("mirago"))
CACHE_FILE = CACHE_DIR / "pypi_cache.json"
CACHE_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days


def _load_cache() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Cache failures are non-fatal; we just won't speed up the next run.
    with contextlib.suppress(OSError):
        CACHE_FILE.write_text(json.dumps(cache))


def package_exists_on_pypi(name: str, use_cache: bool = True) -> bool:
    """Return True if the given package exists on PyPI (or is a stdlib module).

    Network errors are treated as 'exists' to avoid false positives when offline.
    Results are cached on disk for 7 days under the platform user cache dir.
    """
    if name in _STDLIB:
        return True

    name_lower = name.lower()
    cache = _load_cache() if use_cache else {}

    if use_cache and name_lower in cache:
        entry = cache[name_lower]
        if time.time() - entry.get("checked_at", 0) < CACHE_TTL_SECONDS:
            return bool(entry.get("exists", True))

    try:
        response = httpx.get(
            f"https://pypi.org/pypi/{name_lower}/json",
            timeout=5.0,
            follow_redirects=True,
        )
        exists = response.status_code == 200
    except httpx.HTTPError:
        # Network failure: don't flag the user's code as hallucinated.
        return True

    if use_cache:
        cache[name_lower] = {"exists": exists, "checked_at": time.time()}
        _save_cache(cache)

    return exists
