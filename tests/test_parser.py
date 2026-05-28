"""Tests for the AST import extractor."""

from pathlib import Path

import pytest

from mirago.parser import extract_imports


def test_extracts_simple_import(tmp_path: Path) -> None:
    f = tmp_path / "sample.py"
    f.write_text("import requests\n")

    imports = extract_imports(f)
    assert len(imports) == 1
    assert imports[0].module == "requests"
    assert imports[0].is_from is False
    assert imports[0].line == 1


def test_extracts_from_import(tmp_path: Path) -> None:
    f = tmp_path / "sample.py"
    f.write_text("from requests import get\n")

    imports = extract_imports(f)
    assert len(imports) == 1
    assert imports[0].module == "requests"
    assert imports[0].name == "get"
    assert imports[0].is_from is True


def test_handles_multiple_imports(tmp_path: Path) -> None:
    f = tmp_path / "sample.py"
    f.write_text("import os\nimport sys\nfrom pathlib import Path\n")

    imports = extract_imports(f)
    assert len(imports) == 3


def test_skips_relative_imports(tmp_path: Path) -> None:
    f = tmp_path / "sample.py"
    f.write_text("from . import helper\n")

    imports = extract_imports(f)
    assert len(imports) == 0


def test_dotted_imports_collapse_to_top_level(tmp_path: Path) -> None:
    f = tmp_path / "sample.py"
    f.write_text("import os.path\n")

    imports = extract_imports(f)
    assert imports[0].module == "os"


def test_raises_on_syntax_error(tmp_path: Path) -> None:
    f = tmp_path / "broken.py"
    f.write_text("def x(:\n")

    with pytest.raises(ValueError):
        extract_imports(f)


def test_captures_source_line(tmp_path: Path) -> None:
    f = tmp_path / "sample.py"
    f.write_text("import requests\n")

    imports = extract_imports(f)
    assert imports[0].code == "import requests"
