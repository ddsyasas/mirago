"""Tests for the orchestrating checker (parser + PyPI together)."""

from pathlib import Path
from unittest.mock import patch

from mirago.checker import check_file


def test_no_issues_when_all_imports_real(tmp_path: Path) -> None:
    f = tmp_path / "good.py"
    f.write_text("import os\nimport sys\nfrom pathlib import Path\n")

    with patch("mirago.checker.package_exists_on_pypi", return_value=True):
        issues = check_file(f, use_cache=False)

    assert issues == []


def test_flags_hallucinated_import(tmp_path: Path) -> None:
    f = tmp_path / "bad.py"
    f.write_text("import fake_nonexistent_pkg\n")

    with patch("mirago.checker.package_exists_on_pypi", return_value=False):
        issues = check_file(f, use_cache=False)

    assert len(issues) == 1
    assert "fake_nonexistent_pkg" in issues[0].message
    assert issues[0].line == 1


def test_each_package_only_looked_up_once(tmp_path: Path) -> None:
    f = tmp_path / "sample.py"
    f.write_text(
        "import requests\n"
        "from requests import get\n"
        "from requests.auth import HTTPBasicAuth\n"
    )

    with patch(
        "mirago.checker.package_exists_on_pypi", return_value=True
    ) as mock_check:
        check_file(f, use_cache=False)

    # Three imports, but only one unique top-level package.
    assert mock_check.call_count == 1
