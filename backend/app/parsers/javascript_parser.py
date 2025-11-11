import asyncio
import json
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any

from app.models import CodeElement
from app.config import BASE_DIR

# Path to the Node.js parser script
NODE_PARSER_SCRIPT = BASE_DIR/ "parsers" / "javascript_parser.js"


async def parse_javascript_file(
        file_path: Path
) -> Tuple[List[CodeElement], List[str]]:
    """
    Calls the Node.js Babel parser script as a subprocess.

    Returns a tuple of (code_elements, import_statements).
    """

    # Ensure the script exists
    if not NODE_PARSER_SCRIPT.exists():
        print(f"Error: Node parser script not found at {NODE_PARSER_SCRIPT}")
        return [], []

    command = ["node", str(NODE_PARSER_SCRIPT), str(file_path)]

    try:
        # Run the blocking subprocess in a separate thread
        process = await asyncio.to_thread(
            subprocess.run,
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,  # Raise error if exit code is non-zero
            cwd=BASE_DIR  # Run from the 'backend' directory
        )

        # Parse the JSON output from stdout
        result = json.loads(process.stdout)

        # Validate and convert elements to Pydantic models
        parsed_elements = [
            CodeElement(**el) for el in result.get("elements", [])
        ]
        imports = result.get("imports", [])

        return parsed_elements, imports

    except subprocess.CalledProcessError as e:
        print(f"Error running Node.js parser on {file_path}:")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return [], []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Node.js parser for {file_path}: {e}")
        return [], []
    except Exception as e:
        print(f"Unexpected error parsing JS/TS file {file_path}: {e}")
        return [], []