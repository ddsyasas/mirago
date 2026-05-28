"""Tests for recursive Python-file discovery."""

from pathlib import Path

from mirago.discovery import collect_python_files


def test_finds_nested_and_skips_noise(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import os\n")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "b.py").write_text("x = 1\n")
    (tmp_path / "notes.txt").write_text("not python\n")
    # noise dirs that must be skipped
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "lib.py").write_text("x = 1\n")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "c.py").write_text("x = 1\n")

    found = collect_python_files(tmp_path)
    names = {p.name for p in found}

    assert names == {"a.py", "b.py"}


def test_empty_directory_returns_nothing(tmp_path: Path) -> None:
    assert collect_python_files(tmp_path) == []
