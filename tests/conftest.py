import pytest

from unittest.mock import AsyncMock


@pytest.fixture(scope="function")
def mock_clients() -> dict[str, AsyncMock]:
    """Provide mock clients for testing."""
    return {
        "http_client": AsyncMock(),
        "ai_client": AsyncMock(),
        "cache_client": AsyncMock(),
    }
