import asyncio
from pathlib import Path
from typing import List, Dict, Tuple
from fastapi import BackgroundTasks
import dagre_py
from app.models import (
    RepoRequest,
    AnalysisResponse,
    FileNode,
    FolderNode,
    RepositoryNode,
    GraphAnalysisResponse,
    GraphNode,
    GraphEdge,
    DependencyAnalysis,
    CircularDependency
)
from app.parsers.python_parser import parse_python_file
from app.utils.github_cloner import clone_repo
from app.utils.file_walker import walk_directory, get_language_from_extension
from app.parsers.manager import parse_file
from app.parsers.dependency_analyzer import (
    build_dependency_graph,
    analyze_dependencies,
    find_circular_dependencies
)


async def _parse_all_files(
        repo_path: Path,
        file_paths: List[Path]
) -> Dict[str, FileNode]:
    """
    Parses all files concurrently using the parser manager.
    """
    file_nodes: Dict[str, FileNode] = {}
    tasks = []

    for file_path in file_paths:
        language = get_language_from_extension(file_path.suffix)
        tasks.append(
            _parse_single_file(repo_path, file_path, language)
        )

    results = await asyncio.gather(*tasks)

    for result in results:
        if result:
            file_nodes[result.path] = result

    return file_nodes


async def _parse_single_file(
        repo_path: Path,
        file_path: Path,
        language: str
) -> FileNode | None:
    """
    Helper coroutine for parsing a single file.
    """
    try:
        relative_path_str = str(file_path.relative_to(repo_path)).replace("\\", "/")
        elements, imports = await parse_file(file_path, language)

        return FileNode(
            path=relative_path_str,
            language=language,
            size=file_path.stat().st_size,
            elements=elements,
            imports=imports,
        )
    except Exception as e:
        print(f"Failed to parse {file_path}: {e}")
        return None


def build_file_tree(
        repo_path: Path,
        file_nodes: Dict[str, FileNode]
) -> FolderNode:
    """
    Converts a flat dict of file nodes into a nested FolderNode tree.
    """
    root = FolderNode(path=".")
    folder_map: Dict[str, FolderNode] = {".": root}

    sorted_paths = sorted(file_nodes.keys())

    for file_path_str in sorted_paths:
        file_node = file_nodes[file_path_str]
        parts = file_path_str.split("/")

        current_parent_folder_node = root
        current_path_str = "."

        for part in parts[:-1]:  # Iterate through folders
            if current_path_str == ".":
                current_path_str = part
            else:
                current_path_str = f"{current_path_str}/{part}"

            if current_path_str not in folder_map:
                new_folder = FolderNode(path=current_path_str)
                folder_map[current_path_str] = new_folder
                current_parent_folder_node.children.append(new_folder)
                current_parent_folder_node = new_folder
            else:
                current_parent_folder_node = folder_map[current_path_str]

        current_parent_folder_node.children.append(file_node)

    return root


def _layout_graph_with_dagre(
        nodes: List[GraphNode],
        edges: List[GraphEdge]
) -> List[GraphNode]:
    """
    Uses Dagre to calculate node positions for auto-layout.
    """
    g = dagre_py.Dagre()
    g.set_graph_options(rankdir='TB', nodesep=50, ranksep=100)  # Top-to-Bottom

    # Add nodes to Dagre
    for node in nodes:
        g.add_node(
            node.id,
            label=node.data.get('label', ''),
            width=250,  # Set a default width
            height=50  # Set a default height
        )

    # Add edges to Dagre
    for edge in edges:
        g.add_edge(edge.source, edge.target)

    # Run layout
    g.layout()

    # Update node positions
    for node in nodes:
        layout_node = g.get_node(node.id)
        node.position = {"x": layout_node.x, "y": layout_node.y}

    return nodes


def _build_react_flow_graph(
        all_files: Dict[str, FileNode],
        graph: Dict[str, List[str]],
        circular_deps: List[CircularDependency]
) -> Tuple[List[GraphNode], List[GraphEdge]]:
    """
    Converts the adjacency list graph into React Flow nodes and edges.
    """
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []

    # Create a set of all nodes in cycles for quick lookup
    nodes_in_cycle = {
        node for cycle in circular_deps for node in cycle.nodes
    }

    # 1. Create nodes
    for file_path, file_node in all_files.items():
        node_type = "custom"
        if file_path in nodes_in_cycle:
            # This data will be used by the frontend
            node_type = "customError"

        nodes.append(
            GraphNode(
                id=file_path,
                type=node_type,
                data={"label": file_path, "language": file_node.language},
                position={"x": 0, "y": 0}  # Dagre will overwrite this
            )
        )

    # 2. Create edges
    for source_file, dependencies in graph.items():
        for target_file in dependencies:
            is_circular = (
                    source_file in nodes_in_cycle and target_file in nodes_in_cycle
            )

            edges.append(
                GraphEdge(
                    id=f"{source_file}__TO__{target_file}",
                    source=source_file,
                    target=target_file,
                    animated=False,
                    # Add red styling for circular dependencies
                    style={"stroke": "red"} if is_circular else None
                )
            )

    # 3. Apply automatic layout
    nodes = _layout_graph_with_dagre(nodes, edges)

    return nodes, edges


# --- MODIFIED: This is now the main service function for Phase 2 ---
async def analyze_repository_graph(
        request: RepoRequest,
        background_tasks: BackgroundTasks
) -> GraphAnalysisResponse:
    """
    Orchestrates the FULL analysis of a GitHub repository for Phase 2.
    1. Clones the repo
    2. Walks the file system
    3. Parses all files concurrently
    4. Builds the file hierarchy
    5. Builds the dependency graph
    6. Analyzes dependencies (most imported, cycles, etc.)
    7. Generates the React Flow graph structure
    """
    repo_path = await clone_repo(request.url, background_tasks)

    # 1. Walk directory
    file_paths = walk_directory(repo_path)

    # 2. Parse all files
    all_files: Dict[str, FileNode] = await _parse_all_files(repo_path, file_paths)

    # 3. Build file hierarchy
    hierarchy = build_file_tree(repo_path, all_files)

    # 4. Build dependency graph
    dep_graph = build_dependency_graph(all_files)

    # 5. Analyze dependencies
    dep_analysis = analyze_dependencies(all_files, dep_graph)

    # 6. Find circular dependencies
    cycles = find_circular_dependencies(dep_graph)
    dep_analysis.circular_dependencies = cycles

    # 7. Generate React Flow graph
    graph_nodes, graph_edges = _build_react_flow_graph(
        all_files, dep_graph, cycles
    )

    return GraphAnalysisResponse(
        graph_nodes=graph_nodes,
        graph_edges=graph_edges,
        hierarchy=hierarchy,
        dependencies=dep_analysis,
    )


# --- This is the original Phase 1 function, kept for the /analyze endpoint ---
async def analyze_repository_basic(
        request: RepoRequest,
        background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """
    Orchestrates the BASIC analysis of a GitHub repository (Phase 1).
    """
    repo_path = await clone_repo(request.url, background_tasks)
    file_paths = walk_directory(repo_path)

    # Parse only Python files, and do it simply
    file_nodes: Dict[str, FileNode] = {}
    for file_path in file_paths:
        language = get_language_from_extension(file_path.suffix)
        if language == "python":  # Phase 1 only did Python
            elements, _ = parse_python_file(file_path)
            relative_path_str = str(file_path.relative_to(repo_path)).replace("\\", "/")

            file_nodes[relative_path_str] = FileNode(
                path=relative_path_str,
                language=language,
                size=file_path.stat().st_size,
                elements=elements,
            )

    root_node = build_file_tree(repo_path, file_nodes)

    return AnalysisResponse(
        repository_url=request.url,
        total_files_scanned=len(file_nodes),
        file_hierarchy=root_node,
    )