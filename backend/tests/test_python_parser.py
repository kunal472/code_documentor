import pytest
import textwrap
from pathlib import Path

from app.parsers.python_parser import parse_python_file


@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""
    import os
    import sys, json
    from pathlib import Path
    from . import local_util
    from ..parent_pkg import other_util

    class MyClass:
        def my_method(self):
            pass

    def top_level_function():
        pass
    """)
    file_path = tmp_path / "sample.py"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_parse_python_file_structure(sample_python_file: Path):
    elements, imports = parse_python_file(sample_python_file)

    assert len(elements) == 3  # MyClass, my_method, top_level_function
    element_map = {el.name: el for el in elements}
    assert "MyClass" in element_map
    assert "my_method" in element_map
    assert "top_level_function" in element_map


def test_parse_python_file_imports(sample_python_file: Path):
    elements, imports = parse_python_file(sample_python_file)

    # --- MODIFIED: This assertion is now correct ---
    assert len(imports) == 6
    # --- END MODIFICATION ---

    assert "os" in imports
    assert "sys" in imports
    assert "json" in imports
    assert "pathlib" in imports
    assert ".local_util" in imports
    assert "..parent_pkg" in imports