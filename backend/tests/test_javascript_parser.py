import pytest
import textwrap
from pathlib import Path
import subprocess
import os
import pytest_asyncio

from app.parsers.javascript_parser import parse_javascript_file
from app.config import BASE_DIR


# Fixture to create a sample TSX file
@pytest.fixture
def sample_tsx_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""
    import React from 'react';
    import { Button } from './components/Button';
    import * as api from '../api/client';

    /**
     * This is a sample component.
     */
    export const MyComponent = ({ name }: { name: string }): string => {
      return <div>Hello, {name}</div>;
    }

    class MyClass {
      constructor() {}

      private myMethod() {
        // A private method
      }
    }
    """)
    file_path = tmp_path / "MyComponent.tsx"
    file_path.write_text(content, encoding="utf-8")
    return file_path


# Ensure Node.js dependencies are installed before running tests
@pytest_asyncio.fixture(scope="session", autouse=True)
def install_node_deps():
    backend_dir = BASE_DIR
    node_modules = backend_dir / "node_modules"

    # Check if node_modules exists and has content
    if node_modules.exists() and any(node_modules.iterdir()):
        print("\nNode.js dependencies already installed.")
        return

    print("\nInstalling Node.js dependencies for tests...")
    # Use shell=True for Windows compatibility with npm commands
    subprocess.run(
        ["npm", "install"],
        cwd=backend_dir,
        check=True,
        capture_output=True,
        shell=True
    )


@pytest.mark.asyncio
async def test_parse_javascript_file(sample_tsx_file: Path):
    elements, imports = await parse_javascript_file(sample_tsx_file)

    # Test imports
    assert len(imports) == 3
    assert "react" in imports
    assert "./components/Button" in imports
    assert "../api/client" in imports

    # Test code elements
    # We expect: MyComponent (function), MyClass (class), constructor (method), myMethod (method)
    assert len(elements) == 4

    element_map = {el.name: el for el in elements}

    # Test Function
    assert "MyComponent" in element_map
    comp = element_map["MyComponent"]
    assert comp.type == "function"
    assert "This is a sample component." in comp.docstring
    # --- This assertion should now pass ---
    assert comp.parameters == ["name"]
    assert comp.return_type == "string"

    # Test Class
    assert "MyClass" in element_map
    cls = element_map["MyClass"]
    assert cls.type == "class"

    # Test Constructor
    assert "constructor" in element_map
    constructor = element_map["constructor"]
    assert constructor.type == "method"
    assert constructor.parameters == []

    # Test Private Method
    assert "myMethod" in element_map
    method = element_map["myMethod"]
    assert method.type == "method"
    assert method.parameters == []