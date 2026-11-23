import ast
import io
import tokenize
from pathlib import Path

import pytest

SOURCE_FILES = sorted(Path(__file__).resolve().parents[1].joinpath("src").rglob("*.py"))


@pytest.mark.parametrize("path", SOURCE_FILES, ids=lambda path: path.name)
def test_source_has_no_comments(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    comments = [
        token.string
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
    ]
    assert comments == []


@pytest.mark.parametrize("path", SOURCE_FILES, ids=lambda path: path.name)
def test_source_has_no_docstrings(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    documented = [
        getattr(node, "name", "<module>")
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        and ast.get_docstring(node) is not None
    ]
    assert documented == []
