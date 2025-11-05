import asyncio
import git
import shutil
import uuid
from pathlib import Path
from fastapi import BackgroundTasks, HTTPException
from starlette import status

from app.config import settings

# Store paths of active clones to prevent accidental deletion
# In a real production app, this state might be managed in Redis or a DB
active_clones = set()


async def clone_repo(url: str, background_tasks: BackgroundTasks) -> Path:
    """
    Clones a public GitHub repository into a temporary directory.

    Uses asyncio.to_thread to avoid blocking the main event loop.
    Schedules a background task to clean up the repo afterward.
    """
    # Generate a unique directory name
    repo_id = str(uuid.uuid4())
    repo_path = settings.TEMP_REPO_DIR / repo_id

    if repo_path.exists():
        # This should be extremely rare, but handle it
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Temporary directory collision for {repo_path}"
        )

    try:
        print(f"Cloning {url} into {repo_path}...")
        active_clones.add(str(repo_path))

        # Run the blocking I/O operation in a separate thread
        await asyncio.to_thread(
            git.Repo.clone_from,
            url,
            repo_path,
            depth=1  # Only clone the latest commit
        )

        print(f"Successfully cloned {url}.")

        # Schedule the cleanup task
        background_tasks.add_task(cleanup_repo, repo_path)

        return repo_path

    except git.exc.GitCommandError as e:
        print(f"Error cloning repo: {e}")
        # Clean up any partial clone
        await cleanup_repo(repo_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to clone repository. Is the URL valid? Error: {e.strerror}"
        )
    except Exception as e:
        print(f"An unexpected error occurred during cloning: {e}")
        await cleanup_repo(repo_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during the cloning process."
        )


async def cleanup_repo(repo_path: Path):
    """
    Removes the cloned repository directory.
    Uses asyncio.to_thread for the blocking rmtree call.
    """
    repo_path_str = str(repo_path)
    if not repo_path.exists():
        print(f"Cleanup not needed (already gone): {repo_path}")
        if repo_path_str in active_clones:
            active_clones.remove(repo_path_str)
        return

    print(f"Cleaning up {repo_path}...")
    try:
        # Run the blocking I/O operation in a separate thread
        await asyncio.to_thread(shutil.rmtree, repo_path)
        print(f"Successfully cleaned up {repo_path}.")
    except OSError as e:
        # This can happen on Windows if files are locked
        print(f"Warning: Failed to cleanup {repo_path}. Error: {e}")
    finally:
        if repo_path_str in active_clones:
            active_clones.remove(repo_path_str)


def get_active_clones_count() -> int:
    """
    Returns the count of repositories currently being processed.
    """
    return len(active_clones)