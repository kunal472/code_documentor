import pytest
from app.models import FileNode
from app.parsers.dependency_analyzer import (
    _resolve_relative_import,
    build_dependency_graph,
    find_circular_dependencies
)


@pytest.fixture
def mock_file_nodes() -> dict[str, FileNode]:
    """
    Creates a mock file system structure.

    - app/main.py
    - app/utils/helpers.py
    - app/services/user_service.py
    - app/services/auth_service.py
    """
    return {
        "app/main.py": FileNode(
            path="app/main.py", language="python", size=100,
            imports=["./services/user_service", "./services/auth_service"]
        ),
        "app/utils/helpers.py": FileNode(
            path="app/utils/helpers.py", language="python", size=50,
            imports=[]  # Isolated
        ),
        "app/services/user_service.py": FileNode(
            path="app/services/user_service.py", language="python", size=100,
            imports=["../utils/helpers.py", "./auth_service"]  # Cycle
        ),
        "app/services/auth_service.py": FileNode(
            path="app/services/auth_service.py", language="python", size=100,
            imports=["./user_service"]  # Cycle
        ),
    }


def test_resolve_relative_import(mock_file_nodes):
    current_file = mock_file_nodes["app/main.py"]

    # Test 1: ./services/user_service -> app/services/user_service.py
    resolved = _resolve_relative_import(
        "./services/user_service", current_file, mock_file_nodes
    )
    assert resolved == "app/services/user_service.py"

    current_file = mock_file_nodes["app/services/user_service.py"]

    # Test 2: ../utils/helpers.py -> app/utils/helpers.py
    resolved = _resolve_relative_import(
        "../utils/helpers.py", current_file, mock_file_nodes
    )
    assert resolved == "app/utils/helpers.py"

    # Test 3: Non-existent file
    resolved = _resolve_relative_import(
        "./non_existent", current_file, mock_file_nodes
    )
    assert resolved is None


def test_build_dependency_graph(mock_file_nodes):
    graph = build_dependency_graph(mock_file_nodes)

    assert "app/main.py" in graph
    assert "app/services/user_service.py" in graph
    assert "app/services/auth_service.py" in graph
    assert "app/utils/helpers.py" not in graph  # No outgoing imports

    assert "app/services/user_service.py" in graph["app/main.py"]
    assert "app/services/auth_service.py" in graph["app/main.py"]

    assert "app/utils/helpers.py" in graph["app/services/user_service.py"]
    assert "app/services/auth_service.py" in graph["app/services/user_service.py"]

    assert "app/services/user_service.py" in graph["app/services/auth_service.py"]


def test_find_circular_dependencies(mock_file_nodes):
    graph = build_dependency_graph(mock_file_nodes)
    cycles = find_circular_dependencies(graph)

    assert len(cycles) == 1
    cycle_nodes = cycles[0].nodes

    # Sort for consistent comparison
    cycle_nodes = sorted(cycle_nodes)
    assert cycle_nodes == [
        "app/services/auth_service.py",
        "app/services/user_service.py"
    ]