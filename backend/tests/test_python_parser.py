import pytest
import textwrap
from pathlib import Path

from app.parsers.python_parser import parse_python_file


# Use pytest's tmp_path fixture to create a temporary file
@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """
    Creates a temporary Python file with sample code.
    """
    content = textwrap.dedent("""
    import os

    '''
    This is a module docstring.
    '''

    class MyClass:
        \"\"\"
        This is a class docstring.
        \"\"\"
        def __init__(self, value: int):
            self.value = value

        async def my_method(self, name: str) -> str:
            # This is a method
            return f"Hello, {name}"

    def top_level_function(a: list[str], b) -> None:
        \"\"\"This is a function docstring.\"\"\"
        pass

    async def another_async_func():
        pass
    """)

    file_path = tmp_path / "sample.py"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_parse_python_file(sample_python_file: Path):
    """
    Tests that the Python parser correctly extracts classes, methods, and functions.
    """
    elements = parse_python_file(sample_python_file)

    assert len(elements) == 5  # MyClass, __init__, my_method, top_level_function, another_async_func

    # Find elements by name
    element_map = {el.name: el for el in elements}

    # Test Class
    assert "MyClass" in element_map
    my_class = element_map["MyClass"]
    assert my_class.type == "class"
    assert "This is a class docstring." in my_class.docstring

    # Test Method
    assert "__init__" in element_map
    init_method = element_map["__init__"]
    assert init_method.type == "method"
    assert init_method.parameters == ["self", "value"]

    # Test Async Method
    assert "my_method" in element_map
    my_method = element_map["my_method"]
    assert my_method.type == "method"
    assert my_method.parameters == ["self", "name"]
    assert my_method.return_type == "str"

    # Test Function
    assert "top_level_function" in element_map
    top_func = element_map["top_level_function"]
    assert top_func.type == "function"
    assert top_func.parameters == ["a", "b"]
    assert top_func.return_type == "None"
    assert "This is a function docstring." in top_func.docstring

    # Test Async Function
    assert "another_async_func" in element_map
    async_func = element_map["another_async_func"]
    assert async_func.type == "function"