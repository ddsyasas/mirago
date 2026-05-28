"""Tests for the orchestrating checker (parser + registry together)."""

from pathlib import Path
from unittest.mock import patch

from mirago.checker import check_file, check_source
from mirago.lockfile import Lockfile
from mirago.registry import PackageInfo
from tests.fakes import FakeRegistry


def test_no_issues_when_all_imports_real() -> None:
    registry = FakeRegistry({"os": True, "requests": True})
    issues = check_source("import os\nimport requests\n", registry=registry)
    assert issues == []


def test_flags_hallucinated_import() -> None:
    registry = FakeRegistry({})  # nothing exists
    issues = check_source("import fake_nonexistent_pkg\n", registry=registry)

    assert len(issues) == 1
    assert "fake_nonexistent_pkg" in issues[0].message
    assert issues[0].line == 1


def test_each_package_only_looked_up_once() -> None:
    registry = FakeRegistry({"requests": True})
    check_source(
        "import requests\n"
        "from requests import get\n"
        "from requests.auth import HTTPBasicAuth\n",
        registry=registry,
    )

    # Three imports, one unique top-level package → one registry lookup.
    assert registry.calls == ["requests"]


def test_check_file_delegates_to_check_source(tmp_path: Path) -> None:
    f = tmp_path / "sample.py"
    f.write_text("import fake_nonexistent_pkg\n")

    with patch("mirago.checker.check_source", return_value=[]) as mock_source:
        check_file(f, use_cache=False)

    mock_source.assert_called_once()
    # The file's text is passed through to the engine.
    assert mock_source.call_args.args[0] == "import fake_nonexistent_pkg\n"


def test_suspicious_package_is_a_warning() -> None:
    registry = FakeRegistry(
        {"sketchy": PackageInfo(exists=True, age_days=2, downloads_last_month=5)}
    )
    issues = check_source("import sketchy\n", registry=registry)

    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert issues[0].signals["age_days"] == 2
    assert issues[0].signals["downloads_last_month"] == 5


def test_lockfile_membership_suppresses_warning() -> None:
    registry = FakeRegistry(
        {"sketchy": PackageInfo(exists=True, age_days=2, downloads_last_month=5)}
    )
    lock = Lockfile(exists=True, packages={"sketchy"})
    issues = check_source("import sketchy\n", registry=registry, lockfile=lock)

    assert issues == []


def test_suggester_attaches_to_error_only() -> None:
    registry = FakeRegistry(
        {"sketchy": PackageInfo(exists=True, age_days=2, downloads_last_month=5)}
    )
    issues = check_source(
        "import requets\nimport sketchy\n",
        registry=registry,
        suggester=lambda name: "requests" if name == "requets" else None,
    )

    by_sev = {i.severity: i for i in issues}
    assert by_sev["error"].suggestion == "requests"  # error gets a suggestion
    assert by_sev["warning"].suggestion is None  # warning does not


def test_metadata_false_is_existence_only() -> None:
    # A suspicious-but-existing package must NOT warn on the fast path.
    registry = FakeRegistry(
        {"sketchy": PackageInfo(exists=True, age_days=1, downloads_last_month=1)}
    )
    issues = check_source("import sketchy\n", registry=registry, metadata=False)

    assert issues == []
