from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.codeforces_client import CodeforcesApiClient
from infrastructure.errors import NetworkError


@pytest.mark.asyncio
async def test_fetch_problemset_problems_success(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
    sample_problemset_response: dict,
) -> None:
    setup_mock_response(sample_problemset_response)

    result = await codeforces_client.fetch_problemset_problems()

    assert result == sample_problemset_response
    assert result["status"] == "OK"
    assert "problems" in result["result"]
    assert len(result["result"]["problems"]) == 3


@pytest.mark.asyncio
async def test_fetch_problemset_problems_invalid_json(
    codeforces_client: CodeforcesApiClient,
    mock_http_client: AsyncMock,
) -> None:
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_http_client.get.return_value = mock_response

    with pytest.raises(NetworkError) as exc_info:
        await codeforces_client.fetch_problemset_problems()

    assert "Invalid response from Codeforces API" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_problemset_problems_api_error_status(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    setup_mock_response({"status": "FAILED", "comment": "Some error occurred"})

    with pytest.raises(NetworkError) as exc_info:
        await codeforces_client.fetch_problemset_problems()

    assert "Codeforces API error: FAILED" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_problemset_problems_http_error(
    codeforces_client: CodeforcesApiClient,
    mock_http_client: AsyncMock,
) -> None:
    mock_http_client.get.side_effect = Exception("Connection error")

    with pytest.raises(Exception) as exc_info:
        await codeforces_client.fetch_problemset_problems()

    assert "Connection error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_problemset_problems_empty_result(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    setup_mock_response({"status": "OK", "result": {"problems": [], "problemStatistics": []}})

    result = await codeforces_client.fetch_problemset_problems()

    assert result["status"] == "OK"
    assert result["result"]["problems"] == []
