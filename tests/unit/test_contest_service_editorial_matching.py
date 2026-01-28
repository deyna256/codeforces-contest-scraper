"""Unit tests for contest service editorial matching logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.domain.models.editorial import Editorial, ContestEditorial
from src.services.contest import ContestService


@pytest.mark.asyncio
async def test_service_filters_editorials_by_contest_id():
    """Test that service filters editorials to match only requested contest."""
    # Setup mocks
    api_client = AsyncMock()
    page_parser = AsyncMock()
    editorial_parser = AsyncMock()

    # Mock API responses
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 1900", "type": "CF"},
            "problems": [
                {"index": "A", "name": "Problem A"},
                {"index": "B", "name": "Problem B"},
            ],
        }
    }
    api_client.fetch_problemset_problems.return_value = {
        "result": {
            "problems": [
                {"contestId": 1900, "index": "A", "rating": 1200, "tags": []},
                {"contestId": 1900, "index": "B", "rating": 1400, "tags": []},
            ]
        }
    }

    # Mock page parser to return editorials
    page_parser.parse_contest_page.return_value = MagicMock(
        editorial_urls=["http://example.com/editorial"]
    )
    page_parser.parse_problem_in_contest.return_value = MagicMock(
        description="Test description", time_limit="1 second", memory_limit="256 MB"
    )

    # Mock editorial_parser to return editorials from multiple contests
    editorial_parser.parse_editorial_content.return_value = ContestEditorial(
        contest_id="1900",
        editorials=[
            Editorial(contest_id="1900", problem_id="A", analysis_text="Div1 A solution"),
            Editorial(contest_id="1901", problem_id="A", analysis_text="Div2 A solution"),
            Editorial(contest_id="1900", problem_id="B", analysis_text="Div1 B solution"),
        ],
    )

    service = ContestService(
        api_client=api_client, page_parser=page_parser, editorial_parser=editorial_parser
    )

    # Execute
    contest = await service.get_contest("1900")

    # Verify that expected_problems was passed correctly
    editorial_parser.parse_editorial_content.assert_called_once()
    call_args = editorial_parser.parse_editorial_content.call_args
    assert call_args[0][0] == "1900"  # contest_id
    expected_problems = call_args[1]["expected_problems"]
    assert expected_problems == [("1900", "A"), ("1900", "B")]

    # Verify that only Div1 problems got explanations
    assert len(contest.problems) == 2
    problem_a = next(p for p in contest.problems if p.id == "A")
    problem_b = next(p for p in contest.problems if p.id == "B")

    assert problem_a.explanation == "Div1 A solution"  # NOT "Div2 A solution"
    assert problem_b.explanation == "Div1 B solution"


@pytest.mark.asyncio
async def test_service_handles_editorials_without_contest_id():
    """Test that service handles editorials without contest_id (fallback)."""
    # Setup mocks
    api_client = AsyncMock()
    page_parser = AsyncMock()
    editorial_parser = AsyncMock()

    # Mock API responses
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 1900", "type": "CF"},
            "problems": [
                {"index": "A", "name": "Problem A"},
            ],
        }
    }
    api_client.fetch_problemset_problems.return_value = {
        "result": {
            "problems": [
                {"contestId": 1900, "index": "A", "rating": 1200, "tags": []},
            ]
        }
    }

    # Mock page parser
    page_parser.parse_contest_page.return_value = MagicMock(
        editorial_urls=["http://example.com/editorial"]
    )
    page_parser.parse_problem_in_contest.return_value = MagicMock(
        description="Test description", time_limit="1 second", memory_limit="256 MB"
    )

    # Mock editorial_parser to return editorial without contest_id (old format)
    editorial_parser.parse_editorial_content.return_value = ContestEditorial(
        contest_id="1900",
        editorials=[
            Editorial(
                contest_id=None, problem_id="A", analysis_text="Problem A solution (no contest_id)"
            ),
        ],
    )

    service = ContestService(
        api_client=api_client, page_parser=page_parser, editorial_parser=editorial_parser
    )

    # Execute
    contest = await service.get_contest("1900")

    # Verify that problem got explanation using fallback
    assert len(contest.problems) == 1
    problem_a = contest.problems[0]
    assert problem_a.explanation == "Problem A solution (no contest_id)"


@pytest.mark.asyncio
async def test_service_skips_editorials_from_other_contests():
    """Test that service skips editorials from other contests entirely."""
    # Setup mocks
    api_client = AsyncMock()
    page_parser = AsyncMock()
    editorial_parser = AsyncMock()

    # Mock API responses
    api_client.fetch_contest_standings.return_value = {
        "result": {
            "contest": {"name": "Contest 1900", "type": "CF"},
            "problems": [
                {"index": "A", "name": "Problem A"},
            ],
        }
    }
    api_client.fetch_problemset_problems.return_value = {
        "result": {
            "problems": [
                {"contestId": 1900, "index": "A", "rating": 1200, "tags": []},
            ]
        }
    }

    # Mock page parser
    page_parser.parse_contest_page.return_value = MagicMock(
        editorial_urls=["http://example.com/editorial"]
    )
    page_parser.parse_problem_in_contest.return_value = MagicMock(
        description="Test description", time_limit="1 second", memory_limit="256 MB"
    )

    # Mock editorial_parser to return only editorials from other contests
    editorial_parser.parse_editorial_content.return_value = ContestEditorial(
        contest_id="1900",
        editorials=[
            Editorial(contest_id="1901", problem_id="A", analysis_text="Div2 A solution"),
            Editorial(
                contest_id="1902", problem_id="A", analysis_text="Another contest A solution"
            ),
        ],
    )

    service = ContestService(
        api_client=api_client, page_parser=page_parser, editorial_parser=editorial_parser
    )

    # Execute
    contest = await service.get_contest("1900")

    # Verify that problem did NOT get any explanation
    assert len(contest.problems) == 1
    problem_a = contest.problems[0]
    assert problem_a.explanation is None
