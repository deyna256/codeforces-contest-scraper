from unittest.mock import AsyncMock

import pytest

from domain.models.identifiers import ProblemIdentifier
from domain.models.problem import Problem
from infrastructure.codeforces_client import CodeforcesApiClient
from infrastructure.errors import ProblemNotFoundError


@pytest.mark.asyncio
async def test_get_problem_success(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
    sample_problem_data: dict,
) -> None:
    setup_mock_response({"status": "OK", "result": {"problems": [sample_problem_data]}})

    identifier = ProblemIdentifier(
        contest_id="1000",
        problem_id="A",
    )

    problem = await codeforces_client.get_problem(identifier)

    assert isinstance(problem, Problem)
    assert problem.contest_id == "1000"
    assert problem.id == "A"
    assert problem.statement == "Test Problem"
    assert problem.rating == 800
    assert problem.tags == ["math", "implementation"]


@pytest.mark.asyncio
async def test_get_problem_with_optional_fields(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    problem_data = {
        "contestId": 2000,
        "index": "B",
        "name": "Minimal Problem",
    }
    setup_mock_response({"status": "OK", "result": {"problems": [problem_data]}})

    identifier = ProblemIdentifier(contest_id="2000", problem_id="B")

    problem = await codeforces_client.get_problem(identifier)

    assert problem.contest_id == "2000"
    assert problem.id == "B"
    assert problem.statement == "Minimal Problem"
    assert problem.rating is None
    assert problem.tags == []


@pytest.mark.asyncio
async def test_get_problem_not_found(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    setup_mock_response({"status": "OK", "result": {"problems": []}})

    identifier = ProblemIdentifier(contest_id="9999", problem_id="Z")

    with pytest.raises(ProblemNotFoundError) as exc_info:
        await codeforces_client.get_problem(identifier)

    assert "Problem 9999/Z not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_problem_contest_id_type_conversion(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    problem_data = {
        "contestId": 1234,
        "index": "A",
        "name": "Test Problem",
    }
    setup_mock_response({"status": "OK", "result": {"problems": [problem_data]}})

    identifier = ProblemIdentifier(contest_id="1234", problem_id="A")

    problem = await codeforces_client.get_problem(identifier)

    assert problem.contest_id == "1234"
    assert isinstance(problem.contest_id, str)


@pytest.mark.asyncio
async def test_get_problem_empty_name(
    codeforces_client: CodeforcesApiClient,
    setup_mock_response,
) -> None:
    problem_data = {
        "contestId": 1000,
        "index": "A",
        "name": "",
        "tags": [],
    }
    setup_mock_response({"status": "OK", "result": {"problems": [problem_data]}})

    identifier = ProblemIdentifier(contest_id="1000", problem_id="A")

    problem = await codeforces_client.get_problem(identifier)

    assert problem.statement == ""
    assert problem.id == "A"


@pytest.mark.asyncio
async def test_get_problem_network_error_propagates(
    codeforces_client: CodeforcesApiClient,
    mock_http_client: AsyncMock,
) -> None:
    mock_http_client.get.side_effect = Exception("Network failure")

    identifier = ProblemIdentifier(contest_id="1000", problem_id="A")

    with pytest.raises(Exception) as exc_info:
        await codeforces_client.get_problem(identifier)

    assert "Network failure" in str(exc_info.value)
