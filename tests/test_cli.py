"""Tests for the CLI, focused on the --json output mode."""

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from mirago.checker import Issue
from mirago.cli import app

runner = CliRunner()


def test_json_output_empty_for_clean_file(tmp_path: Path) -> None:
    f = tmp_path / "ok.py"
    f.write_text("import os\n")  # stdlib short-circuits, no network

    result = runner.invoke(app, ["check", str(f), "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_json_output_lists_issues(tmp_path: Path) -> None:
    f = tmp_path / "bad.py"
    f.write_text("import fastjson_validator\n")
    fake = Issue(
        line=1,
        code="import fastjson_validator",
        message="Package 'fastjson_validator' does not exist on PyPI",
    )

    with patch("mirago.cli.check_file", return_value=[fake]):
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
            "signals": {},
        }
    ]
