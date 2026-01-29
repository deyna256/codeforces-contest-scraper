import pytest
from unittest.mock import AsyncMock, MagicMock

from domain.models.identifiers import ProblemIdentifier
from domain.models.problem import Problem
from services.problem import ProblemService


@pytest.mark.asyncio
async def test_get_problem_returns_full_details():
    api_client = AsyncMock()
    page_parser = AsyncMock()

    problem = Problem(
        contest_id="1000",
        id="A",
        statement="Test Problem",
        rating=800,
        tags=["math", "implementation"],
    )
    api_client.get_problem.return_value = problem

    problem_data = MagicMock()
    problem_data.description = "Problem description"
    problem_data.time_limit = "1 second"
    problem_data.memory_limit = "256 megabytes"
    page_parser.parse_problem_page.return_value = problem_data

    service = ProblemService(api_client=api_client, page_parser=page_parser)
    identifier = ProblemIdentifier(contest_id="1000", problem_id="A")

    result = await service.get_problem(identifier)

    assert result.contest_id == "1000"
    assert result.id == "A"
    assert result.statement == "Test Problem"
    assert result.rating == 800
    assert result.tags == ["math", "implementation"]
    assert result.description == "Problem description"
    assert result.time_limit == "1 second"
    assert result.memory_limit == "256 megabytes"
    api_client.get_problem.assert_called_once_with(identifier)
    page_parser.parse_problem_page.assert_called_once_with(identifier)


@pytest.mark.asyncio
async def test_get_problem_handles_page_parse_failure():
    api_client = AsyncMock()
    page_parser = AsyncMock()

    problem = Problem(
        contest_id="1000",
        id="B",
        statement="Test Problem B",
        rating=1200,
        tags=["dp"],
    )
    api_client.get_problem.return_value = problem
    page_parser.parse_problem_page.side_effect = Exception("Page not found")

    service = ProblemService(api_client=api_client, page_parser=page_parser)
    identifier = ProblemIdentifier(contest_id="1000", problem_id="B")

    result = await service.get_problem(identifier)

    assert result.contest_id == "1000"
    assert result.id == "B"
    assert result.statement == "Test Problem B"
    assert result.rating == 1200
    assert result.tags == ["dp"]
    assert result.description is None
    assert result.time_limit is None
    assert result.memory_limit is None


@pytest.mark.asyncio
async def test_get_problem_by_url():
    api_client = AsyncMock()
    page_parser = AsyncMock()
    url_parser = MagicMock()

    identifier = ProblemIdentifier(contest_id="1500", problem_id="C")
    url_parser.parse.return_value = identifier

    problem = Problem(
        contest_id="1500",
        id="C",
        statement="Problem C",
        rating=1600,
        tags=["graphs"],
    )
    api_client.get_problem.return_value = problem

    problem_data = MagicMock()
    problem_data.description = "Graph problem"
    problem_data.time_limit = "2 seconds"
    problem_data.memory_limit = "512 megabytes"
    page_parser.parse_problem_page.return_value = problem_data

    service = ProblemService(api_client=api_client, page_parser=page_parser, url_parser=url_parser)  # type: ignore[arg-type]

    result = await service.get_problem_by_url("https://codeforces.com/problemset/problem/1500/C")

    assert result.contest_id == "1500"
    assert result.id == "C"
    assert result.statement == "Problem C"
    assert result.description == "Graph problem"
    url_parser.parse.assert_called_once_with("https://codeforces.com/problemset/problem/1500/C")
