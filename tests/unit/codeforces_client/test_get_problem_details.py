import pytest

from infrastructure.codeforces_client import CodeforcesApiClient
from infrastructure.errors import ProblemNotFoundError


@pytest.mark.asyncio
async def test_get_problem_details_success(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
    sample_problemset_response: dict,
) -> None:
    setup_mock_response(sample_problemset_response)

    result = await codeforces_client.get_problem_details("1000", "A")

    assert result["contestId"] == 1000
    assert result["index"] == "A"
    assert result["name"] == "Problem A Title"
    assert result["rating"] == 800
    assert "math" in result["tags"]
    assert "implementation" in result["tags"]


@pytest.mark.asyncio
async def test_get_problem_details_multiple_contests(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
    sample_problemset_response: dict,
) -> None:
    setup_mock_response(sample_problemset_response)

    result = await codeforces_client.get_problem_details("2000", "A")

    assert result["contestId"] == 2000
    assert result["index"] == "A"
    assert result["name"] == "Another Problem"
    assert result["rating"] == 900


@pytest.mark.asyncio
async def test_get_problem_details_problem_not_found(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
    sample_problemset_response: dict,
) -> None:
    setup_mock_response(sample_problemset_response)

    with pytest.raises(ProblemNotFoundError) as exc_info:
        await codeforces_client.get_problem_details("9999", "Z")

    assert "Problem 9999/Z not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_problem_details_empty_problemset(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    setup_mock_response({"status": "OK", "result": {"problems": [], "problemStatistics": []}})

    with pytest.raises(ProblemNotFoundError):
        await codeforces_client.get_problem_details("1000", "A")


@pytest.mark.asyncio
async def test_get_problem_details_malformed_problem_data(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    setup_mock_response(
        {
            "status": "OK",
            "result": {
                "problems": [
                    {"index": "A", "name": "Problem A"},
                    {"contestId": 1000, "name": "Problem B"},
                ],
            },
        }
    )

    with pytest.raises(ProblemNotFoundError):
        await codeforces_client.get_problem_details("1000", "A")


@pytest.mark.asyncio
async def test_get_problem_details_case_sensitivity(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
    sample_problemset_response: dict,
) -> None:
    setup_mock_response(sample_problemset_response)

    with pytest.raises(ProblemNotFoundError):
        await codeforces_client.get_problem_details("1000", "a")


@pytest.mark.asyncio
async def test_get_problem_details_with_extended_index(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    setup_mock_response(
        {
            "status": "OK",
            "result": {
                "problems": [
                    {
                        "contestId": 1500,
                        "index": "B1",
                        "name": "Problem B1",
                        "rating": 1100,
                        "tags": ["dp"],
                    },
                    {
                        "contestId": 1500,
                        "index": "B2",
                        "name": "Problem B2",
                        "rating": 1400,
                        "tags": ["dp", "greedy"],
                    },
                ],
            },
        }
    )

    result = await codeforces_client.get_problem_details("1500", "B1")

    assert result["contestId"] == 1500
    assert result["index"] == "B1"
    assert result["name"] == "Problem B1"
