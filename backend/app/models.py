from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal, Union


# --- API Request Models ---

class RepoRequest(BaseModel):
    """
    Request model for analyzing a repository.
    """
    url: str = Field(..., description="A valid public GitHub repository URL.")


# --- Internal Data Structure Models ---

class CodeElement(BaseModel):
    """
    Represents a single code structure (function, class, method).
    """
    type: Literal["function", "class", "method"]
    name: str
    start_line: int
    end_line: int
    docstring: str | None = None
    parameters: List[str] = []
    return_type: str | None = None  # For functions/methods
    base_classes: List[str] = []  # For classes


class FileNode(BaseModel):
    """
    Represents a single file in the repository graph.
    """
    path: str
    language: Literal["python", "javascript", "typescript", "unknown"]
    size: int
    elements: List[CodeElement] = []
    # --- NEW: Added imports ---
    imports: List[str] = []
    # --- END NEW ---


class FolderNode(BaseModel):
    """
    Represents a folder in the repository graph.
    """
    path: str
    children: List["RepositoryNode"] = []


# This allows FolderNode to recursively contain itself or FileNode
RepositoryNode = Union[FileNode, FolderNode]
FolderNode.model_rebuild()


# --- API Response Models ---

class HealthResponse(BaseModel):
    """
    Response model for the health check endpoint.
    """
    status: Literal["ok"] = "ok"


class StatsResponse(BaseModel):
    """
    Response model for server statistics.
    """
    cloned_repos_count: int


class AnalysisResponse(BaseModel):
    """
    Response model for the basic analysis endpoint (Phase 1).
    """
    repository_url: str
    total_files_scanned: int
    file_hierarchy: RepositoryNode


# --- NEW: Phase 2 Response Models ---

class GraphNode(BaseModel):
    """
    A node for React Flow.
    """
    id: str = Field(..., description="Unique node ID (e.g., file path)")
    type: str = Field("custom", description="Node type for React Flow")
    data: Dict[str, Any] = Field(..., description="Data payload for the node (label, etc.)")
    position: Dict[str, float] = Field(..., description="X, Y coordinates for layout")


class GraphEdge(BaseModel):
    """
    An edge for React Flow.
    """
    id: str = Field(..., description="Unique edge ID (e.g., source-target)")
    source: str = Field(..., description="ID of the source node")
    target: str = Field(..., description="ID of the target node")
    animated: bool = False
    style: Dict[str, str] | None = None


class DependencyInfo(BaseModel):
    """
    Statistics for a single file's dependencies.
    """
    path: str
    imported_by_count: int
    imports_count: int


class CircularDependency(BaseModel):
    """
    Represents a single cycle in the dependency graph.
    """
    nodes: List[str] = Field(..., description="List of file paths forming a cycle")


class DependencyAnalysis(BaseModel):
    """
    Detailed dependency analysis results.
    """
    most_imported: List[DependencyInfo]
    most_importing: List[DependencyInfo]
    isolated_files: List[str]
    circular_dependencies: List[CircularDependency]


class GraphAnalysisResponse(BaseModel):
    """
    The full response for the graph analysis endpoint.
    """
    graph_nodes: List[GraphNode]
    graph_edges: List[GraphEdge]
    hierarchy: RepositoryNode
    dependencies: DependencyAnalysis

# --- END NEW ---