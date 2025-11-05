import pathlib
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the base directory of the project
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    # Server settings
    DEBUG: bool = True
    PORT: int = 8000

    # Project paths
    TEMP_REPO_DIR: pathlib.Path = BASE_DIR.parent / "temp_repos"

    # File limits
    MAX_FILE_SIZE_BYTES: int = 500000

    # Phase 3 settings (placeholders for now)
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL_ADVANCED: str = "gemini-2.5-flash"
    GEMINI_MODEL_LITE: str = "gemini-2.5-flash-lite"
    MAX_CONCURRENT_LLM_CALLS: int = 5

    # Pydantic model config
    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env",
        env_file_encoding='utf-8',
        case_sensitive=False
    )


# Create a single instance to be imported by other modules
settings = Settings()

# Ensure the temp directory exists
settings.TEMP_REPO_DIR.mkdir(parents=True, exist_ok=True)