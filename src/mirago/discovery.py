"""Find the Python files to check under a directory.

Used when a user points mirago at a folder (`mirago check .`) instead of naming files.
Skips folders that would be noise or slow to scan (virtualenvs, caches, version control,
build output), pruning them during the walk so we never descend into them.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_IGNORE_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "env",
        ".env",
        ".tox",
        ".nox",
        "node_modules",
        "build",
        "dist",
        ".eggs",
        "site-packages",
    }
)


def collect_python_files(
    directory: Path, ignore_dirs: frozenset[str] = DEFAULT_IGNORE_DIRS
) -> list[Path]:
    """Recursively collect ``.py`` files under ``directory``, skipping noise folders."""
    found: list[Path] = []
    for root, dirs, filenames in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for name in filenames:
            if name.endswith(".py"):
                found.append(Path(root) / name)
    return sorted(found)
