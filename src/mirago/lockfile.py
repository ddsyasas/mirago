"""Detect and parse the nearest project lockfile / dependency manifest.

This is a TRUST signal, not a risk signal: a package already declared in your project
is one you depend on, so it is never flagged suspicious. If no lockfile is found, the
signal is simply unavailable and contributes nothing (fail-open: safe).
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

_CANON_RE = re.compile(r"[-_.]+")
_NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")

# Fixed-name dependency files we recognize (requirements*.txt is globbed separately).
_TOML_LOCKS = ("poetry.lock", "uv.lock", "pdm.lock")


def canonicalize(name: str) -> str:
    """PEP 503 name normalization: 'Foo_Bar.baz' -> 'foo-bar-baz'."""
    return _CANON_RE.sub("-", name).strip().lower()


@dataclass
class Lockfile:
    """The set of dependency names declared in a project.

    `exists` is False when no recognized dependency file was found at all — in which case
    the "not in lockfile" signal is unavailable (treated as safe).
    """

    exists: bool
    packages: set[str] = field(default_factory=set)  # canonicalized names
    path: Path | None = None  # directory the manifest(s) were found in

    def has(self, name: str) -> bool:
        return canonicalize(name) in self.packages


def _first_name(spec: str) -> str | None:
    spec = spec.strip()
    if not spec or spec.startswith(("#", "-")):
        return None
    match = _NAME_RE.match(spec)
    return canonicalize(match.group(1)) if match else None


def _parse_requirements(path: Path) -> set[str]:
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        name = _first_name(line)
        if name:
            names.add(name)
    return names


def _parse_pipfile_lock(path: Path) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for section in ("default", "develop"):
        for name in data.get(section) or {}:
            names.add(canonicalize(name))
    return names


def _parse_toml_lock(path: Path) -> set[str]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for pkg in data.get("package", []):
        name = pkg.get("name")
        if name:
            names.add(canonicalize(name))
    return names


def _parse_pyproject(path: Path) -> set[str] | None:
    """Return declared deps, or None if this pyproject declares no dependencies at all
    (i.e. it isn't acting as a dependency manifest)."""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    found = False

    project = data.get("project", {})
    if "dependencies" in project or "optional-dependencies" in project:
        found = True
        for dep in project.get("dependencies", []):
            name = _first_name(dep)
            if name:
                names.add(name)
        for group in (project.get("optional-dependencies") or {}).values():
            for dep in group:
                name = _first_name(dep)
                if name:
                    names.add(name)

    poetry = data.get("tool", {}).get("poetry", {})
    if "dependencies" in poetry:
        found = True
        for name in poetry.get("dependencies", {}):
            if name.lower() != "python":
                names.add(canonicalize(name))

    return names if found else None


def _collect_from_dir(directory: Path) -> set[str] | None:
    """Merge dependency names from every recognized file in one directory.
    Returns None if the directory holds no recognized dependency file."""
    names: set[str] = set()
    found = False

    for fname in _TOML_LOCKS:
        path = directory / fname
        if path.is_file():
            names |= _parse_toml_lock(path)
            found = True

    pipfile = directory / "Pipfile.lock"
    if pipfile.is_file():
        names |= _parse_pipfile_lock(pipfile)
        found = True

    for req in sorted(directory.glob("requirements*.txt")):
        if req.is_file():
            names |= _parse_requirements(req)
            found = True

    pyproject = directory / "pyproject.toml"
    if pyproject.is_file():
        declared = _parse_pyproject(pyproject)
        if declared is not None:
            names |= declared
            found = True

    return names if found else None


def find_lockfile(start: Path) -> Lockfile:
    """Walk up from `start` (a file or directory) to the first directory that declares
    dependencies. Stops at a `.git` repo boundary. Parse errors degrade to "not found"."""
    base = start if start.is_dir() else start.parent
    for directory in [base, *base.parents]:
        try:
            names = _collect_from_dir(directory)
        except (OSError, ValueError, KeyError):
            names = None  # malformed manifest -> treat as unavailable (fail-open)
        if names is not None:
            return Lockfile(exists=True, packages=names, path=directory)
        if (directory / ".git").exists():
            break
    return Lockfile(exists=False)
