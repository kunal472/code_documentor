from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

from app.config import settings
from app.models import (
    RepoRequest,
    AnalysisResponse,
    HealthResponse,
    StatsResponse
)
from app.services.analysis_service import analyze_repository
from app.utils.github_cloner import get_active_clones_count

# Initialize the FastAPI app
app = FastAPI(
    title="AI-Powered Code Documentation Generator",
    description="Analyzes GitHub repos and generates documentation using AI.",
    version="0.1.0",
    debug=settings.DEBUG,
)

# --- Middleware ---

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    # In production, list your frontend URL: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


# --- API Endpoints (Phase 1) ---

@app.get(
    "/health",
    tags=["Server"],
    summary="Health Check",
    response_model=HealthResponse,
)
async def get_health():
    """
    Endpoint to check if the server is running.
    """
    return HealthResponse(status="ok")


@app.get(
    "/stats",
    tags=["Server"],
    summary="Server Statistics",
    response_model=StatsResponse,
)
async def get_stats():
    """
    Endpoint to get basic server statistics.
    """
    return StatsResponse(
        cloned_repos_count=get_active_clones_count()
    )


@app.post(
    "/analyze",
    tags=["Analysis"],
    summary="Basic Repository Analysis",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def post_analyze(
        request: RepoRequest,
        background_tasks: BackgroundTasks
):
    """
    Accepts a GitHub URL, clones the repository, parses all (Python) files,
    and returns a hierarchical graph of the file structure and code elements.

    The cloned repository is cleaned up in a background task.
    """
    try:
        response_data = await analyze_repository(request, background_tasks)
        return response_data
    except HTTPException:
        # Re-raise known HTTP exceptions from services
        raise
    except Exception as e:
        # Catch any unexpected errors
        print(f"Unexpected error in /analyze endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected server error occurred: {str(e)}"
        )


# --- API Endpoints (Placeholders for future phases) ---

# @app.post("/analyze/graph", tags=["Analysis"])
# async def post_analyze_graph(request: RepoRequest):
#     return {"message": "Endpoint not implemented", "url": request.url}

# @app.post("/analyze/dependencies", tags=["Analysis"])
# async def post_analyze_dependencies(request: RepoRequest):
#     return {"message": "Endpoint not implemented", "url": request.url}

# @app.get("/generate/documentation/stream", tags=["AI Generation"])
# async def get_generate_documentation_stream():
#     return {"message": "Endpoint not implemented (requires SSE)"}

# ... and so on for other endpoints


# --- Server Startup ---

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )