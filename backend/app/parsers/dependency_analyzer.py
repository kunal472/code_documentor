import os
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict, Counter

from app.models import FileNode, DependencyAnalysis, DependencyInfo, CircularDependency


# ... (_resolve_relative_import and build_dependency_graph are unchanged) ...
def _resolve_relative_import(
        import_path: str,
        current_file: FileNode,
        all_files: Dict[str, FileNode]
) -> str | None:
    current_dir = Path(current_file.path).parent
    resolved_path_str = os.path.normpath(current_dir / import_path)
    extensions_to_try = [
        "", ".py", ".js", ".ts", ".jsx", ".tsx",
        "/__init__.py", "/index.js", "/index.ts",
    ]
    if resolved_path_str in all_files:
        return resolved_path_str
    for ext in extensions_to_try:
        path_with_ext = f"{resolved_path_str}{ext}".replace("\\", "/")
        if path_with_ext in all_files:
            return path_with_ext
    return None


def build_dependency_graph(
        all_files: Dict[str, FileNode]
) -> Dict[str, List[str]]:
    graph = defaultdict(list)
    for file_path, file_node in all_files.items():
        for import_path in file_node.imports:
            if not import_path.startswith("."):
                continue
            resolved = _resolve_relative_import(import_path, file_node, all_files)
            if resolved and resolved in all_files:
                graph[file_path].append(resolved)
    return graph


# ... (analyze_dependencies is unchanged) ...
def analyze_dependencies(
        all_files: Dict[str, FileNode],
        graph: Dict[str, List[str]]
) -> DependencyAnalysis:
    imported_by_counter = Counter()
    for dependencies in graph.values():
        imported_by_counter.update(dependencies)

    imports_counter = {}
    isolated_files = []
    all_file_paths = set(all_files.keys())
    files_in_graph = set(graph.keys()) | set(imported_by_counter.keys())

    for file_path in all_file_paths:
        imports_count = len(graph.get(file_path, []))
        imports_counter[file_path] = imports_count
        imported_by_count = imported_by_counter.get(file_path, 0)
        if imports_count == 0 and imported_by_count == 0 and file_path in all_file_paths:
            isolated_files.append(file_path)

    dep_info = [
        DependencyInfo(
            path=path,
            imported_by_count=imported_by_counter.get(path, 0),
            imports_count=imports_counter.get(path, 0)
        ) for path in files_in_graph
    ]

    most_imported = sorted(dep_info, key=lambda x: x.imported_by_count, reverse=True)[:10]
    most_importing = sorted(dep_info, key=lambda x: x.imports_count, reverse=True)[:10]

    return DependencyAnalysis(
        most_imported=most_imported,
        most_importing=most_importing,
        isolated_files=isolated_files,
        circular_dependencies=[]
    )


# --- MODIFIED: This function is fixed ---
def _find_cycles_dfs(
        node: str,
        graph: Dict[str, List[str]],
        visited: Set[str],
        # MODIFIED: Changed from Set[str] to List[str] to act as an ordered stack
        recursion_stack: List[str],
        all_cycles: Set[Tuple[str, ...]]
):
    """
    DFS helper to find cycles.
    """
    visited.add(node)
    # MODIFIED: Use append
    recursion_stack.append(node)

    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            _find_cycles_dfs(neighbor, graph, visited, recursion_stack, all_cycles)
        elif neighbor in recursion_stack:
            # Cycle detected!
            try:
                # MODIFIED: Find the start of the cycle in the ordered stack
                start_index = recursion_stack.index(neighbor)
                # The cycle is all nodes from the start_index to the end
                cycle = tuple(sorted(recursion_stack[start_index:]))
                all_cycles.add(cycle)
            except ValueError:
                pass  # Should not happen

    # MODIFIED: Use pop
    recursion_stack.pop()


# --- END MODIFICATION ---


def find_circular_dependencies(
        graph: Dict[str, List[str]]
) -> List[CircularDependency]:
    """
    Finds all circular dependencies (strongly connected components) in the graph
    using Depth First Search (DFS).
    """
    visited = set()
    recursion_stack: List[str] = []
    all_cycles: Set[Tuple[str, ...]] = set()

    nodes = list(graph.keys())
    for node in nodes:
        if node not in visited:
            _find_cycles_dfs(node, graph, visited, recursion_stack, all_cycles)

    return [CircularDependency(nodes=list(cycle)) for cycle in all_cycles]