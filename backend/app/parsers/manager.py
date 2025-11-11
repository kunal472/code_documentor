import asyncio
from pathlib import Path
from typing import List, Tuple

from app.models import CodeElement
from app.parsers.python_parser import parse_python_file
from app.parsers.javascript_parser import parse_javascript_file


async def parse_file(
        file_path: Path,
        language: str
) -> Tuple[List[CodeElement], List[str]]:
    """
    Orchestrates parsing for a given file based on its language.

    Returns a tuple of (code_elements, import_statements).
    """
    if language == "python":
        # Python parser is synchronous, wrap in to_thread
        return await asyncio.to_thread(parse_python_file, file_path)

    if language in ("javascript", "typescript"):
        # JS parser is already async (it wraps a subprocess)
        return await parse_javascript_file(file_path)

    # Default for unknown but supported extensions
    return [], []