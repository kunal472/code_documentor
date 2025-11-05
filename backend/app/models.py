from pydantic import BaseModel, Field
from typing import List, Dict, Any, Literal


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
    # Dependencies will be added in Phase 2
    # imports: List[str] = []


class FolderNode(BaseModel):
    """
    Represents a folder in the repository graph.
    """
    path: str
    children: List["RepositoryNode"] = []


# This allows FolderNode to recursively contain itself or FileNode
RepositoryNode = FileNode | FolderNode
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
    # Add more as needed


class AnalysisResponse(BaseModel):
    """
    Response model for the basic analysis endpoint.
    """
    repository_url: str
    total_files_scanned: int
    file_hierarchy: RepositoryNode