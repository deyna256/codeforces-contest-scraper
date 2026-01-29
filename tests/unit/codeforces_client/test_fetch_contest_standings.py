from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.codeforces_client import CodeforcesApiClient
from infrastructure.errors import ContestNotFoundError, NetworkError


@pytest.mark.asyncio
async def test_fetch_contest_standings_success(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
    sample_contest_standings_response: dict,
) -> None:
    setup_mock_response(sample_contest_standings_response)

    result = await codeforces_client.fetch_contest_standings("1000")

    assert result == sample_contest_standings_response
    assert result["status"] == "OK"
    assert "contest" in result["result"]
    assert "problems" in result["result"]
    assert result["result"]["contest"]["id"] == 1000
    assert len(result["result"]["problems"]) == 2


@pytest.mark.asyncio
async def test_fetch_contest_standings_contest_not_found(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    setup_mock_response(
        {"status": "FAILED", "comment": "contestId: Contest with id 99999 not found"}
    )

    with pytest.raises(ContestNotFoundError) as exc_info:
        await codeforces_client.fetch_contest_standings("99999")

    assert "Contest 99999 not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_contest_standings_invalid_json(
    codeforces_client: CodeforcesApiClient,
    mock_http_client: AsyncMock,
) -> None:
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_http_client.get.return_value = mock_response

    with pytest.raises(NetworkError) as exc_info:
        await codeforces_client.fetch_contest_standings("1000")

    assert "Invalid response from Codeforces API" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_contest_standings_api_error_status(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    setup_mock_response({"status": "FAILED", "comment": "Some other error occurred"})

    with pytest.raises(NetworkError) as exc_info:
        await codeforces_client.fetch_contest_standings("1000")

    assert "Codeforces API error: FAILED" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_contest_standings_http_error(
    codeforces_client: CodeforcesApiClient,
    mock_http_client: AsyncMock,
) -> None:
    mock_http_client.get.side_effect = Exception("Connection timeout")

    with pytest.raises(Exception) as exc_info:
        await codeforces_client.fetch_contest_standings("1000")

    assert "Connection timeout" in str(exc_info.value)


@pytest.mark.asyncio
async def test_fetch_contest_standings_empty_problems(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    setup_mock_response(
        {
            "status": "OK",
            "result": {
                "contest": {"id": 1000, "name": "Empty Contest"},
                "problems": [],
                "rows": [],
            },
        }
    )

    result = await codeforces_client.fetch_contest_standings("1000")

    assert result["status"] == "OK"
    assert result["result"]["problems"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "comment",
    [
        "contestId: Contest with id 12345 not found",
        "Contest not found",
        "NOT FOUND",
        "The contest is not found in the database",
    ],
)
async def test_fetch_contest_standings_handles_not_found(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
    comment: str,
) -> None:
    setup_mock_response({"status": "FAILED", "comment": comment})

    with pytest.raises(ContestNotFoundError):
        await codeforces_client.fetch_contest_standings("12345")
