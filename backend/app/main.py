from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

from app.config import settings
from app.models import (
    RepoRequest,
    AnalysisResponse,
    HealthResponse,
    StatsResponse,
    GraphAnalysisResponse, # NEW
    DependencyAnalysis     # NEW
)
# MODIFIED: Import new services
from app.services.analysis_service import (
    analyze_repository_basic,
    analyze_repository_graph
)
from app.utils.github_cloner import get_active_clones_count

app = FastAPI(
    title="AI-Powered Code Documentation Generator",
    description="Analyzes GitHub repos and generates documentation using AI.",
    version="0.2.0", # Bump version
    debug=settings.DEBUG,
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints (Server) ---

@app.get("/health", tags=["Server"], response_model=HealthResponse)
async def get_health():
    return HealthResponse(status="ok")

@app.get("/stats", tags=["Server"], response_model=StatsResponse)
async def get_stats():
    return StatsResponse(cloned_repos_count=get_active_clones_count())

# --- API Endpoints (Analysis) ---

@app.post(
    "/analyze",
    tags=["Analysis"],
    summary="Basic Repository Analysis (Phase 1)",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def post_analyze_basic(
    request: RepoRequest,
    background_tasks: BackgroundTasks
):
    """
    (Phase 1 Endpoint)
    Accepts a GitHub URL, clones, and returns a simple file hierarchy.
    """
    try:
        # Use the original Phase 1 service function
        response_data = await analyze_repository_basic(request, background_tasks)
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in /analyze endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {str(e)}"
        )

# --- NEW: Phase 2 Endpoints ---

@app.post(
    "/analyze/graph",
    tags=["Analysis"],
    summary="Full Graph & Dependency Analysis",
    response_model=GraphAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def post_analyze_graph(
    request: RepoRequest,
    background_tasks: BackgroundTasks
):
    """
    (Phase 2 Endpoint)
    Accepts a GitHub URL, clones, parses all files, builds a full
    dependency graph, and returns data formatted for React Flow.
    """
    try:
        # Use the new Phase 2 service function
        response_data = await analyze_repository_graph(request, background_tasks)
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in /analyze/graph endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {str(e)}"
        )

@app.post(
    "/analyze/dependencies",
    tags=["Analysis"],
    summary="Detailed Dependency Statistics",
    response_model=DependencyAnalysis,
    status_code=status.HTTP_200_OK,
)
async def post_analyze_dependencies(
    request: RepoRequest,
    background_tasks: BackgroundTasks
):
    """
    (Phase 2 Endpoint)
    A lighter endpoint that returns only the dependency analysis statistics
    (most imported, cycles, etc.) without the full graph layout.
    """
    try:
        # We can reuse the main service function and just return part of it
        full_response = await analyze_repository_graph(request, background_tasks)
        return full_response.dependencies
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in /analyze/dependencies endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {str(e)}"
        )

# --- API Endpoints (Placeholders for Phase 3) ---

# @app.get("/generate/documentation/stream", tags=["AI Generation"])
# ...

# --- Server Startup ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )