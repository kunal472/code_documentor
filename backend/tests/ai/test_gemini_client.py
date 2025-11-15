import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings
from app.ai.gemini_client import GeminiClient


# Mock settings for tests
@pytest.fixture
def mock_settings():
    # Provide a dummy value for GEMINI_API_KEY
    return Settings(
        GEMINI_API_KEY="test_key",
        MAX_CONCURRENT_LLM_CALLS=1  # Set to 1 for easy semaphore testing
    )


# Fixture for the semaphore
@pytest_asyncio.fixture
async def mock_semaphore(mock_settings):
    """Provides a semaphore instance for the client."""
    return asyncio.Semaphore(mock_settings.MAX_CONCURRENT_LLM_CALLS)


# Patch the genai library
@pytest.fixture
def mock_genai():
    with patch('app.ai.gemini_client.genai') as mock_genai_lib:
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(
            return_value=MagicMock(text="Mocked AI response")
        )
        mock_genai_lib.GenerativeModel.return_value = mock_model
        yield mock_genai_lib


@pytest.mark.asyncio
async def test_gemini_client_init(mock_settings, mock_genai, mock_semaphore):
    """Tests client initialization."""
    client = GeminiClient(mock_settings, mock_semaphore)
    assert client.semaphore._value == 1
    mock_genai.configure.assert_called_with(api_key="test_key")


@pytest.mark.asyncio
async def test_gemini_client_semaphore(mock_settings, mock_genai, mock_semaphore):
    """
    Tests that the semaphore correctly limits concurrency to 1.
    """
    client = GeminiClient(mock_settings, mock_semaphore)

    # --- MODIFICATION: Fix the side_effect ---
    # Define an async function to be the side effect
    async def mock_side_effect(*args, **kwargs):
        await asyncio.sleep(0.02)
        # Return the MOCK OBJECT, which has .text
        return MagicMock(text="Mocked AI response")

    # Mock the underlying generate_content_async to have a slight delay
    mock_genai.GenerativeModel.return_value.generate_content_async = AsyncMock(
        side_effect=mock_side_effect  # Use the new async function
    )
    # --- END MODIFICATION ---

    start_time = asyncio.get_event_loop().time()

    task1 = asyncio.create_task(client.generate_lite("prompt 1"))
    task2 = asyncio.create_task(client.generate_advanced("prompt 2"))

    await asyncio.gather(task1, task2)

    end_time = asyncio.get_event_loop().time()

    # With concurrency=1 and sleep=0.02, total time should be > 0.04
    assert (end_time - start_time) > 0.039

    # Check that both calls were made
    assert mock_genai.GenerativeModel.return_value.generate_content_async.call_count == 2