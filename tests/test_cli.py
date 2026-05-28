"""Tests for the CLI: JSON output, severity exit codes, and --fix."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import typer
from typer.testing import CliRunner

from mirago.checker import Issue
from mirago.cli import _apply_fixes, app

runner = CliRunner()


def _error_issue() -> Issue:
    return Issue(
        line=1,
        code="import fastjson_validator",
        message="Package 'fastjson_validator' does not exist on PyPI",
        severity="error",
        signals={"exists": False, "risk_factors": ["not_on_pypi"]},
    )


def _warning_issue() -> Issue:
    return Issue(
        line=2,
        code="import sketchy",
        message="Package 'sketchy' exists but looks suspicious (created 2d ago, 5 downloads/month)",
        severity="warning",
        signals={"exists": True, "age_days": 2, "downloads_last_month": 5},
    )


def test_json_output_empty_for_clean_file(tmp_path: Path) -> None:
    f = tmp_path / "ok.py"
    f.write_text("import os\n")  # stdlib short-circuits, no network

    result = runner.invoke(app, ["check", str(f), "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_json_output_lists_issue_with_full_signals(tmp_path: Path) -> None:
    f = tmp_path / "bad.py"
    f.write_text("import fastjson_validator\n")

    with patch("mirago.cli.check_file", return_value=[_error_issue()]):
        result = runner.invoke(app, ["check", str(f), "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload == [
        {
            "file": str(f),
            "line": 1,
            "code": "import fastjson_validator",
            "message": "Package 'fastjson_validator' does not exist on PyPI",
            "severity": "error",
            "suggestion": None,
            "signals": {"exists": False, "risk_factors": ["not_on_pypi"]},
        }
    ]


def test_error_exits_1(tmp_path: Path) -> None:
    f = tmp_path / "bad.py"
    f.write_text("import fastjson_validator\n")

    with patch("mirago.cli.check_file", return_value=[_error_issue()]):
        result = runner.invoke(app, ["check", str(f)])

    assert result.exit_code == 1
    assert "hallucination" in result.stdout


def test_warning_is_non_fatal_by_default(tmp_path: Path) -> None:
    f = tmp_path / "susp.py"
    f.write_text("import sketchy\n")

    with patch("mirago.cli.check_file", return_value=[_warning_issue()]):
        result = runner.invoke(app, ["check", str(f)])

    assert result.exit_code == 0  # warnings don't fail the run by default
    assert "suspicious" in result.stdout


def test_fail_on_warning_escalates(tmp_path: Path) -> None:
    f = tmp_path / "susp.py"
    f.write_text("import sketchy\n")

    with patch("mirago.cli.check_file", return_value=[_warning_issue()]):
        result = runner.invoke(app, ["check", str(f), "--fail-on", "warning"])

    assert result.exit_code == 1


def test_directory_check_walks_all_files(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import os\n")  # stdlib only -> no network
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("import sys\n")

    result = runner.invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 0
    assert "Checked 2 file" in result.stdout


def test_directory_check_skips_noise_dirs(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("import os\n")
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "lib.py").write_text("import os\n")  # must be skipped

    result = runner.invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 0
    assert "Checked 1 file" in result.stdout


def test_fix_replaces_misspelled_import(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    f = tmp_path / "typo.py"
    f.write_text("import requets\n")
    issue = Issue(
        line=1,
        code="import requets",
        message="Package 'requets' does not exist on PyPI",
        suggestion="requests",
        severity="error",
    )

    monkeypatch.setattr("mirago.cli.sys.stdin.isatty", lambda: True, raising=False)
    monkeypatch.setattr(typer, "confirm", lambda *a, **k: True)

    _apply_fixes(f, [issue])

    assert f.read_text() == "import requests\n"
