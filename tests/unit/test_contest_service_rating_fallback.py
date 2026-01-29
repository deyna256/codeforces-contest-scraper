import pytest
from unittest.mock import AsyncMock, MagicMock

from services.contest import ContestService


@pytest.mark.asyncio
async def test_uses_rating_from_standings_when_available():
    api_client = AsyncMock()
    page_parser = AsyncMock()

    # Mock API responses - contest.standings includes rating
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 102", "type": "CF"},
            "problems": [
                {
                    "index": "A",
                    "name": "Problem A",
                    "rating": 1200,
                    "tags": ["brute force"],
                },
                {
                    "index": "D",
                    "name": "Problem D",
                    "rating": 1900,
                    "tags": ["dp", "graphs"],
                },
            ],
        }
    }

    # Mock problemset.problems - only has problem A (missing D)
    api_client.fetch_problemset_problems.return_value = {
        "result": {
            "problems": [
                {"contestId": 102, "index": "A", "rating": 1200, "tags": ["brute force"]},
            ]
        }
    }

    # Mock page parser
    page_parser.parse_contest_page.return_value = MagicMock(editorial_urls=[])
    page_parser.parse_problem_in_contest.return_value = MagicMock(
        description="Test description", time_limit="1 second", memory_limit="256 MB"
    )

    service = ContestService(api_client=api_client, page_parser=page_parser, editorial_parser=None)

    # Execute
    contest = await service.get_contest("102")

    # Verify that both problems got ratings (including D which is missing from problemset)
    assert len(contest.problems) == 2

    problem_a = next(p for p in contest.problems if p.id == "A")
    problem_d = next(p for p in contest.problems if p.id == "D")

    assert problem_a.rating == 1200
    assert problem_a.tags == ["brute force"]

    # Problem D should get rating from standings API (not from problemset)
    assert problem_d.rating == 1900
    assert problem_d.tags == ["dp", "graphs"]


@pytest.mark.asyncio
async def test_falls_back_to_problemset_when_rating_missing():
    api_client = AsyncMock()
    page_parser = AsyncMock()

    # Mock API responses - contest.standings WITHOUT rating
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 999", "type": "CF"},
            "problems": [
                {
                    "index": "A",
                    "name": "Problem A",
                    # No rating field
                },
            ],
        }
    }

    # Mock problemset.problems - has rating
    api_client.fetch_problemset_problems.return_value = {
        "result": {
            "problems": [
                {"contestId": 999, "index": "A", "rating": 1500, "tags": ["math"]},
            ]
        }
    }

    # Mock page parser
    page_parser.parse_contest_page.return_value = MagicMock(editorial_urls=[])
    page_parser.parse_problem_in_contest.return_value = MagicMock(
        description="Test description", time_limit="1 second", memory_limit="256 MB"
    )

    service = ContestService(api_client=api_client, page_parser=page_parser, editorial_parser=None)

    # Execute
    contest = await service.get_contest("999")

    # Verify that problem got rating from problemset.problems
    assert len(contest.problems) == 1
    problem_a = contest.problems[0]

    assert problem_a.rating == 1500
    assert problem_a.tags == ["math"]


@pytest.mark.asyncio
async def test_handles_missing_rating_in_both_sources():
    api_client = AsyncMock()
    page_parser = AsyncMock()

    # Mock API responses - no rating anywhere
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 888", "type": "CF"},
            "problems": [
                {
                    "index": "A",
                    "name": "Problem A",
                    # No rating
                },
            ],
        }
    }

    # Mock problemset.problems - also doesn't have this problem
    api_client.fetch_problemset_problems.return_value = {"result": {"problems": []}}

    # Mock page parser
    page_parser.parse_contest_page.return_value = MagicMock(editorial_urls=[])
    page_parser.parse_problem_in_contest.return_value = MagicMock(
        description="Test description", time_limit="1 second", memory_limit="256 MB"
    )

    service = ContestService(api_client=api_client, page_parser=page_parser, editorial_parser=None)

    # Execute
    contest = await service.get_contest("888")

    # Verify that problem has None rating (not an error)
    assert len(contest.problems) == 1
    problem_a = contest.problems[0]

    assert problem_a.rating is None
    assert problem_a.tags == []
