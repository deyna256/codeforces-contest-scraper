import pytest
from unittest.mock import AsyncMock, MagicMock

from services.contest import ContestService
from infrastructure.parsers.errors import EditorialNotFoundError


@pytest.mark.asyncio
async def test_continues_when_page_parser_fails():
    api_client = AsyncMock()
    page_parser = AsyncMock()

    # Mock API responses
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 1000", "type": "CF"},
            "problems": [
                {"index": "A", "name": "Problem A", "rating": 800, "tags": ["math"]},
            ],
        }
    }
    api_client.fetch_problemset_problems.return_value = {"result": {"problems": []}}

    # Mock page parser to fail
    page_parser.parse_contest_page.side_effect = Exception("Network error")
    page_parser.parse_problem_in_contest.return_value = MagicMock(
        description="Description", time_limit="1s", memory_limit="256MB"
    )

    service = ContestService(api_client=api_client, page_parser=page_parser)

    # Execute
    contest = await service.get_contest("1000")

    # Verify - should succeed without editorial URLs
    assert contest.contest_id == "1000"
    assert contest.title == "Contest 1000"
    assert len(contest.problems) == 1
    assert contest.editorials == []  # No editorials due to parser failure


@pytest.mark.asyncio
async def test_continues_when_problem_parsing_fails():
    api_client = AsyncMock()
    page_parser = AsyncMock()

    # Mock API responses
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 2000", "type": "CF"},
            "problems": [
                {"index": "A", "name": "Problem A", "rating": 800, "tags": ["math"]},
                {"index": "B", "name": "Problem B", "rating": 1200, "tags": ["dp"]},
                {"index": "C", "name": "Problem C", "rating": 1600, "tags": ["graphs"]},
            ],
        }
    }
    api_client.fetch_problemset_problems.return_value = {"result": {"problems": []}}

    # Mock page parser
    page_parser.parse_contest_page.return_value = MagicMock(editorial_urls=[])

    # Make problem B fail to parse
    def parse_problem_side_effect(contest_id, problem_id):
        if problem_id == "B":
            raise Exception("Failed to parse B")
        return MagicMock(
            description=f"Description {problem_id}", time_limit="1s", memory_limit="256MB"
        )

    page_parser.parse_problem_in_contest.side_effect = parse_problem_side_effect

    service = ContestService(api_client=api_client, page_parser=page_parser)

    # Execute
    contest = await service.get_contest("2000")

    # Verify - should have 3 problems (B has no description but is still included)
    assert len(contest.problems) == 3
    problem_b = next(p for p in contest.problems if p.id == "B")
    # Problem B should exist but without description (parsing failed)
    assert problem_b.statement is None


@pytest.mark.asyncio
async def test_get_contest_by_url_success():
    api_client = AsyncMock()
    page_parser = AsyncMock()
    url_parser = MagicMock()

    # Mock URL parser
    identifier = MagicMock()
    identifier.contest_id = "1500"
    url_parser.parse_contest_url.return_value = identifier

    # Mock API responses
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 1500", "type": "CF"},
            "problems": [{"index": "A", "name": "Problem A", "rating": 800, "tags": ["math"]}],
        }
    }
    api_client.fetch_problemset_problems.return_value = {"result": {"problems": []}}

    # Mock page parser
    page_parser.parse_contest_page.return_value = MagicMock(editorial_urls=[])
    page_parser.parse_problem_in_contest.return_value = MagicMock(
        description="Description", time_limit="1s", memory_limit="256MB"
    )

    service = ContestService(api_client=api_client, page_parser=page_parser, url_parser=url_parser)  # type: ignore[arg-type]

    # Execute
    contest = await service.get_contest_by_url("https://codeforces.com/contest/1500")

    # Verify
    assert contest.contest_id == "1500"
    assert contest.title == "Contest 1500"
    url_parser.parse_contest_url.assert_called_once_with("https://codeforces.com/contest/1500")


@pytest.mark.asyncio
async def test_get_editorial_content_no_parser():
    api_client = AsyncMock()
    page_parser = AsyncMock()

    # Create service without editorial parser
    service = ContestService(api_client=api_client, page_parser=page_parser, editorial_parser=None)

    with pytest.raises(EditorialNotFoundError):
        await service.get_editorial_content("1000")


@pytest.mark.asyncio
async def test_get_editorial_content_no_urls_provided():
    api_client = AsyncMock()
    page_parser = AsyncMock()
    editorial_parser = AsyncMock()

    # Mock contest with no editorials
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 3000", "type": "CF"},
            "problems": [],
        }
    }
    api_client.fetch_problemset_problems.return_value = {"result": {"problems": []}}
    page_parser.parse_contest_page.return_value = MagicMock(editorial_urls=[])

    service = ContestService(
        api_client=api_client, page_parser=page_parser, editorial_parser=editorial_parser
    )

    with pytest.raises(EditorialNotFoundError):
        await service.get_editorial_content("3000")


@pytest.mark.asyncio
async def test_get_editorial_content_with_urls():
    api_client = AsyncMock()
    page_parser = AsyncMock()
    editorial_parser = AsyncMock()

    # Mock editorial parser response
    editorial_data = MagicMock()
    editorial_data.editorials = [
        MagicMock(problem_id="A", analysis_text="Solution for A"),
        MagicMock(problem_id="B", analysis_text="Solution for B"),
    ]
    editorial_parser.parse_editorial_content.return_value = editorial_data

    service = ContestService(
        api_client=api_client, page_parser=page_parser, editorial_parser=editorial_parser
    )

    # Execute
    result = await service.get_editorial_content(
        "1000", ["https://codeforces.com/blog/entry/12345"]
    )

    # Verify
    assert result == editorial_data
    editorial_parser.parse_editorial_content.assert_called_once_with(
        "1000", ["https://codeforces.com/blog/entry/12345"]
    )


@pytest.mark.asyncio
async def test_get_editorial_content_fetches_urls():
    api_client = AsyncMock()
    page_parser = AsyncMock()
    editorial_parser = AsyncMock()

    # Mock API responses
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 4000", "type": "CF"},
            "problems": [],
        }
    }
    api_client.fetch_problemset_problems.return_value = {"result": {"problems": []}}

    # Mock page parser with editorial URLs
    page_parser.parse_contest_page.return_value = MagicMock(
        editorial_urls=["https://codeforces.com/blog/entry/99999"]
    )

    # Mock editorial parser
    editorial_data = MagicMock()
    editorial_data.editorials = []
    editorial_parser.parse_editorial_content.return_value = editorial_data

    service = ContestService(
        api_client=api_client, page_parser=page_parser, editorial_parser=editorial_parser
    )

    # Execute
    result = await service.get_editorial_content("4000")

    # Verify - should fetch URLs from contest and call parse_editorial_content twice:
    # once in get_contest (with expected_problems), once in get_editorial_content
    assert result == editorial_data
    assert editorial_parser.parse_editorial_content.call_count >= 1


@pytest.mark.asyncio
async def test_continues_when_editorial_parsing_fails():
    api_client = AsyncMock()
    page_parser = AsyncMock()
    editorial_parser = AsyncMock()

    # Mock API responses
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 5000", "type": "CF"},
            "problems": [{"index": "A", "name": "Problem A", "rating": 800, "tags": ["math"]}],
        }
    }
    api_client.fetch_problemset_problems.return_value = {"result": {"problems": []}}

    # Mock page parser
    page_parser.parse_contest_page.return_value = MagicMock(
        editorial_urls=["https://codeforces.com/blog/entry/12345"]
    )
    page_parser.parse_problem_in_contest.return_value = MagicMock(
        description="Description", time_limit="1s", memory_limit="256MB"
    )

    # Mock editorial parser to fail
    editorial_parser.parse_editorial_content.side_effect = Exception("Editorial parsing failed")

    service = ContestService(
        api_client=api_client, page_parser=page_parser, editorial_parser=editorial_parser
    )

    # Execute
    contest = await service.get_contest("5000")

    # Verify - should succeed without explanations
    assert contest.contest_id == "5000"
    assert len(contest.problems) == 1
    assert contest.problems[0].explanation is None  # No explanation due to parser failure
