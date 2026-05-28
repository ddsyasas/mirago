"""AST-based parser for extracting imports from Python source files."""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Import:
    """A single import statement extracted from source code."""

    module: str          # top-level package, e.g. "requests" from "from requests.auth import X"
    name: str | None     # imported symbol, e.g. "get" from "from requests import get"
    line: int            # 1-indexed line number where the import appears
    code: str            # the actual source line, for display in reports
    is_from: bool        # True for "from x import y", False for "import x"


class _ImportExtractor(ast.NodeVisitor):
    """AST visitor that collects every import statement in a Python module."""

    def __init__(self, source_lines: list[str]) -> None:
        self.imports: list[Import] = []
        self._source_lines = source_lines

    def visit_Import(self, node: ast.Import) -> None:
        """Handle 'import x' and 'import x as y'."""
        for alias in node.names:
            self.imports.append(
                Import(
                    module=alias.name.split(".")[0],
                    name=None,
                    line=node.lineno,
                    code=self._get_source_line(node.lineno),
                    is_from=False,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Handle 'from x import y'. Skip relative imports."""
        if node.module is None or node.level > 0:
            return

        top_module = node.module.split(".")[0]
        for alias in node.names:
            self.imports.append(
                Import(
                    module=top_module,
                    name=alias.name,
                    line=node.lineno,
                    code=self._get_source_line(node.lineno),
                    is_from=True,
                )
            )
        self.generic_visit(node)

    def _get_source_line(self, lineno: int) -> str:
        idx = lineno - 1
        if 0 <= idx < len(self._source_lines):
            return self._source_lines[idx].strip()
        return ""


def extract_imports_from_source(source: str, filename: str = "<string>") -> list[Import]:
    """Parse Python source text and return every import it contains.

    Raises ValueError if the source cannot be parsed (syntax error).
    """
    source_lines = source.splitlines()

    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as e:
        raise ValueError(f"Could not parse {filename}: {e}") from e

    extractor = _ImportExtractor(source_lines)
    extractor.visit(tree)
    return extractor.imports


def extract_imports(file_path: Path) -> list[Import]:
    """Parse a Python file and return every import it contains.

    Raises ValueError if the file cannot be parsed (syntax error).
    """
    return extract_imports_from_source(file_path.read_text(encoding="utf-8"), str(file_path))
