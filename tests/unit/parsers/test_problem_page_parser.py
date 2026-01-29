import pytest

from unittest.mock import AsyncMock

from infrastructure.parsers import ProblemPageParser
from domain.models.identifiers import ProblemIdentifier
from infrastructure.parsers import ParsingError


REALISTIC_HTML = """
<html>
    <div class="problem-statement">
        <div class="header">
            <div class="title">A. Real Problem Title</div>
            <div class="time-limit">time limit per test 2 seconds</div>
            <div class="memory-limit">memory limit per test 256 megabytes</div>
        </div>
        <div class="">
            <p>You are given a problem to solve.</p>
            <p>This is the description of the problem.</p>
        </div>
    </div>
</html>
"""

SAMPLE_HTML_NO_EDITORIAL = """
<html>
    <div class="problem-statement">
        <div class="header">
            <div class="time-limit">time limit per test 1 second</div>
            <div class="memory-limit">memory limit per test 512 megabytes</div>
        </div>
        <div class="">
            <p>Another problem description.</p>
        </div>
    </div>
</html>
"""


@pytest.fixture
def mock_http_client() -> AsyncMock:
    client = AsyncMock()
    client.get_text.return_value = REALISTIC_HTML
    return client


@pytest.mark.asyncio
async def test_parse_successful(mock_http_client) -> None:
    identifier = ProblemIdentifier(
        contest_id="2183",
        problem_id="A",
    )

    parser = ProblemPageParser(mock_http_client)
    data = await parser.parse_problem_page(identifier=identifier)

    assert data.identifier == identifier
    assert data.time_limit == "2 seconds"
    assert data.memory_limit == "256 megabytes"
    assert "You are given a problem to solve" in (data.description or "")
    assert "This is the description of the problem" in (data.description or "")


@pytest.mark.asyncio
async def test_parse_no_editorial() -> None:
    client = AsyncMock()
    client.get_text.return_value = SAMPLE_HTML_NO_EDITORIAL
    identifier = ProblemIdentifier(
        contest_id="9999",
        problem_id="B",
    )

    parser = ProblemPageParser(client)
    data = await parser.parse_problem_page(identifier=identifier)

    assert data.identifier == identifier
    assert data.time_limit == "1 second"
    assert data.memory_limit == "512 megabytes"
    assert "Another problem description" in (data.description or "")


@pytest.mark.asyncio
async def test_http_error_handling() -> None:
    client = AsyncMock()
    client.get_text.side_effect = Exception("Network Error")
    identifier = ProblemIdentifier(contest_id="1234", problem_id="A")

    with pytest.raises(ParsingError):
        parser = ProblemPageParser(client)
        await parser.parse_problem_page(identifier=identifier)
