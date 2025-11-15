import pytest
import textwrap
from pathlib import Path
import subprocess
import os

from app.parsers.javascript_parser import parse_javascript_file
from app.config import BASE_DIR


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


@pytest.fixture(scope="session", autouse=True)
def install_node_deps():
    backend_dir = BASE_DIR
    if not (backend_dir / "node_modules").exists():
        print("\nInstalling Node.js dependencies for tests...")
        subprocess.run(
            ["npm", "install"],
            cwd=backend_dir,
            check=True,
            capture_output=True,
            shell=True  # Added for Windows compatibility
        )


@pytest.mark.asyncio
async def test_parse_javascript_file(sample_tsx_file: Path):
    elements, imports = await parse_javascript_file(sample_tsx_file)

    assert len(imports) == 3
    assert "react" in imports
    assert "./components/Button" in imports
    assert "../api/client" in imports

    assert len(elements) >= 3

    element_map = {el.name: el for el in elements}

    assert "MyComponent" in element_map
    comp = element_map["MyComponent"]
    assert comp.type == "function"
    assert "This is a sample component." in comp.docstring
    assert comp.parameters == ["name"]
    assert comp.return_type == "string"

    assert "MyClass" in element_map
    cls = element_map["MyClass"]
    assert cls.type == "class"

    assert "myMethod" in element_map
    method = element_map["myMethod"]
    assert method.type == "method"