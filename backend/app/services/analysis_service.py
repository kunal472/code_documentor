from pathlib import Path
from typing import List, Dict
from fastapi import BackgroundTasks

from app.models import RepoRequest, AnalysisResponse, FileNode, FolderNode, RepositoryNode
from app.utils.github_cloner import clone_repo
from app.utils.file_walker import walk_directory, get_language_from_extension
from app.parsers.python_parser import parse_python_file


# In Phase 2, we'll add:
# from app.parsers.javascript_parser import parse_javascript_file

async def analyze_repository(
        request: RepoRequest,
        background_tasks: BackgroundTasks
) -> AnalysisResponse:
    """
    Orchestrates the analysis of a GitHub repository.
    1. Clones the repo
    2. Walks the file system
    3. Parses supported files
    4. Builds the file hierarchy
    """
    repo_path = await clone_repo(request.url, background_tasks)

    file_paths = walk_directory(repo_path)

    file_nodes: Dict[Path, FileNode] = {}

    for file_path in file_paths:
        relative_path_str = str(file_path.relative_to(repo_path))
        language = get_language_from_extension(file_path.suffix)

        elements = []
        if language == "python":
            elements = parse_python_file(file_path)
        # elif language in ("javascript", "typescript"):
        # elements = await parse_javascript_file(file_path) # Phase 2

        file_nodes[file_path] = FileNode(
            path=relative_path_str.replace("\\", "/"),  # Normalize path separators
            language=language,
            size=file_path.stat().st_size,
            elements=elements,
        )

    # Build the hierarchical tree structure
    root_node = build_file_tree(repo_path, file_nodes)

    return AnalysisResponse(
        repository_url=request.url,
        total_files_scanned=len(file_nodes),
        file_hierarchy=root_node,
    )


def build_file_tree(
        repo_path: Path,
        file_nodes: Dict[Path, FileNode]
) -> FolderNode:
    """
    Converts a flat list of file nodes into a nested FolderNode tree.
    """
    root = FolderNode(path=".")
    folder_map: Dict[Path, FolderNode] = {repo_path: root}

    # Sort paths to ensure parents are created before children
    sorted_paths = sorted(file_nodes.keys())

    for file_path in sorted_paths:
        # Get the FileNode we already created
        file_node = file_nodes[file_path]

        # Find or create parent FolderNodes
        current_parent_folder_node = root
        current_parent_path = repo_path

        parts = file_path.relative_to(repo_path).parts

        # Iterate through parts to build folder hierarchy
        # e.g., for 'app/services/analysis.py'
        # parts = ('app', 'services', 'analysis.py')

        for part in parts[:-1]:  # Iterate through 'app', 'services'
            current_parent_path = current_parent_path / part

            if current_parent_path not in folder_map:
                # Create new FolderNode if it doesn't exist
                new_folder = FolderNode(
                    path=str(current_parent_path.relative_to(repo_path)).replace("\\", "/")
                )
                folder_map[current_parent_path] = new_folder
                current_parent_folder_node.children.append(new_folder)
                current_parent_folder_node = new_folder
            else:
                # Use existing FolderNode
                current_parent_folder_node = folder_map[current_parent_path]

        # Add the file node to its direct parent
        current_parent_folder_node.children.append(file_node)

    return root