"""PyPI existence checker with on-disk cache and stdlib short-circuit."""

from __future__ import annotations

import contextlib
import datetime
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
METADATA_CACHE_FILE = CACHE_DIR / "pypi_metadata_cache.json"
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


def _load_metadata_cache() -> dict:
    if not METADATA_CACHE_FILE.exists():
        return {}
    try:
        return json.loads(METADATA_CACHE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_metadata_cache(cache: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        METADATA_CACHE_FILE.write_text(json.dumps(cache))


def _parse_iso(ts: str) -> datetime.datetime | None:
    try:
        dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def _age_days_from_json(data: dict) -> int | None:
    """Earliest release upload time -> age in days. None if no timestamps available."""
    releases = data.get("releases") or {}
    earliest: datetime.datetime | None = None
    for files in releases.values():
        for f in files:
            ts = f.get("upload_time_iso_8601") or f.get("upload_time")
            if not ts:
                continue
            dt = _parse_iso(ts)
            if dt is not None and (earliest is None or dt < earliest):
                earliest = dt
    if earliest is None:
        return None
    now = datetime.datetime.now(datetime.timezone.utc)
    return max((now - earliest).days, 0)


def _fetch_downloads_last_month(name_lower: str) -> int | None:
    """Recent monthly downloads from pypistats. None on any error (fail-open)."""
    try:
        response = httpx.get(
            f"https://pypistats.org/api/packages/{name_lower}/recent",
            timeout=5.0,
            follow_redirects=True,
        )
        if response.status_code == 200:
            value = response.json().get("data", {}).get("last_month")
            return int(value) if isinstance(value, int) else None
    except (httpx.HTTPError, ValueError):
        return None
    return None


def fetch_metadata(name: str, use_cache: bool = True) -> dict:
    """Return {'exists', 'age_days', 'downloads_last_month'} for a package.

    Age comes from the single /pypi/<name>/json response (no extra call). Only the
    download count uses a second (pypistats) request, and only when the package exists.
    Fail-open everywhere: a network error -> exists True (never flag real code), and any
    unknown signal -> None (treated as safe by the risk scorer). Cached on disk for 7 days.
    """
    if name in _STDLIB:
        return {"exists": True, "age_days": None, "downloads_last_month": None}

    name_lower = name.lower()
    cache = _load_metadata_cache() if use_cache else {}

    if use_cache and name_lower in cache:
        entry = cache[name_lower]
        if time.time() - entry.get("checked_at", 0) < CACHE_TTL_SECONDS:
            return {k: entry.get(k) for k in ("exists", "age_days", "downloads_last_month")}

    age_days: int | None = None
    downloads: int | None = None
    try:
        response = httpx.get(
            f"https://pypi.org/pypi/{name_lower}/json",
            timeout=5.0,
            follow_redirects=True,
        )
        if response.status_code == 200:
            exists = True
            age_days = _age_days_from_json(response.json())
        elif response.status_code == 404:
            exists = False
        else:
            exists = True  # ambiguous status -> fail open
    except (httpx.HTTPError, ValueError):
        # Network failure: don't flag real code, and don't cache the miss.
        return {"exists": True, "age_days": None, "downloads_last_month": None}

    if exists:
        downloads = _fetch_downloads_last_month(name_lower)

    result = {"exists": exists, "age_days": age_days, "downloads_last_month": downloads}
    if use_cache:
        cache[name_lower] = {**result, "checked_at": time.time()}
        _save_metadata_cache(cache)
    return result
