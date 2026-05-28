"""Tests for lockfile detection and parsing."""

from pathlib import Path

from mirago.lockfile import canonicalize, find_lockfile


def test_canonicalize() -> None:
    assert canonicalize("Foo_Bar.Baz") == "foo-bar-baz"


def test_requirements_txt(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "requests==2.31.0\n"
        "Flask>=2\n"
        "# a comment\n"
        "-e .\n"
        "httpx[http2]~=0.27 ; python_version>'3'\n"
    )
    lf = find_lockfile(tmp_path)
    assert lf.exists
    assert lf.has("requests")
    assert lf.has("flask")
    assert lf.has("httpx")


def test_pyproject_pep621(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["requests>=2", "rich"]\n'
        '[project.optional-dependencies]\ndev = ["pytest"]\n'
    )
    lf = find_lockfile(tmp_path)
    assert lf.has("requests")
    assert lf.has("rich")
    assert lf.has("pytest")


def test_pyproject_without_dependencies_is_not_a_manifest(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[build-system]\nrequires = ["setuptools"]\n')
    assert find_lockfile(tmp_path).exists is False


def test_poetry_lock(tmp_path: Path) -> None:
    (tmp_path / "poetry.lock").write_text(
        '[[package]]\nname = "requests"\nversion = "2.31.0"\n\n'
        '[[package]]\nname = "Click"\nversion = "8.1.0"\n'
    )
    lf = find_lockfile(tmp_path)
    assert lf.has("requests")
    assert lf.has("click")


def test_no_lockfile_found(tmp_path: Path) -> None:
    assert find_lockfile(tmp_path).exists is False


def test_walks_up_from_file_to_project_root(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests\n")
    sub = tmp_path / "src" / "pkg"
    sub.mkdir(parents=True)
    module = sub / "mod.py"
    module.write_text("import requests\n")

    lf = find_lockfile(module)
    assert lf.exists
    assert lf.has("requests")
