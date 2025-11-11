import os
from pathlib import Path
from typing import List, Set

from app.config import settings

# Files and directories to ignore during traversal
DEFAULT_IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".vscode",
    ".idea",
    "venv",
    ".env",
    "dist",
    "build",
}

# --- MODIFIED: Added JS/TS extensions ---
SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
}


# --- END MODIFICATION ---

def get_language_from_extension(ext: str) -> str:
    """
    Maps a file extension to its programming language.
    """
    # --- MODIFIED: Added JS/TS languages ---
    if ext == ".py":
        return "python"
    if ext in {".js", ".jsx"}:
        return "javascript"
    if ext in {".ts", ".tsx"}:
        return "typescript"
    # --- END MODIFICATION ---
    return "unknown"


def walk_directory(
        start_path: Path,
        ignore_dirs: Set[str] = DEFAULT_IGNORE_DIRS
) -> List[Path]:
    """
    Walks a directory and returns a list of paths to supported files.

    Filters out:
    - Directories in ignore_dirs
    - Files larger than MAX_FILE_SIZE_BYTES
    - Files without a supported extension
    """
    supported_files: List[Path] = []

    for root, dirs, files in os.walk(start_path, topdown=True):
        # Modify dirs in-place to prune traversal
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file_name in files:
            file_path = Path(root) / file_name

            # 1. Check extension
            ext = file_path.suffix
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            try:
                # 2. Check file size
                file_size = file_path.stat().st_size
                if file_size > settings.MAX_FILE_SIZE_BYTES:
                    print(f"Skipping large file: {file_path} ({file_size} bytes)")
                    continue
                if file_size == 0:
                    # Skip empty files
                    continue

                supported_files.append(file_path)

            except (IOError, OSError) as e:
                print(f"Error accessing file {file_path}: {e}")

    return supported_files