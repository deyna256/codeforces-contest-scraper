import pytest

from unittest.mock import AsyncMock

from domain.parsers.problem_page import ProblemPageParser, parse_problem
from domain.models import ProblemIdentifier
from domain.exceptions import ParsingError


# Mock HTML content
REALISTIC_HTML = """
<html>
    <div class="breadcrumbs">
        <a href="/">Codeforces</a>
        <a href="/contest/2183">Hello 2026</a>
    </div>
    <div class="header">
        <div class="title">A. Real Problem Title</div>
    </div>

    <div class="roundbox sidebox sidebar-menu borderTopRound " style="">
        <div class="caption titled">→ Contest materials
            <div class="top-links"></div>
        </div>
        <ul>
            <li>
                <span>
                    <a href="/blog/entry/149809" title="Hello 2026" target="_blank">Hello 2026 <span class="resource-locale">(en)</span></a>
                </span>
            </li>
            <li>
                <span>
                    <a href="/contest/2183/attachments/download/35276/solution.pdf" title="Hello 2026 题解" target="_blank">Hello 2026 题解 <span class="resource-locale">(zh)</span></a>
                </span>
            </li>
            <li>
                <span>
                    <a href="/blog/entry/149944" title="Hello 2026 Editorial" target="_blank">Hello 2026 Editorial <span class="resource-locale">(en)</span></a>
                </span>
            </li>
        </ul>
    </div>
</html>
"""

SAMPLE_HTML_NO_EDITORIAL = """
<html>
    <div class="header"><div class="title">B. Hard Problem</div></div>
    <div class="sidebox">
        <div class="caption">Announcements</div>
        <a href="#">News</a>
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
    """Test standard parsing with editorial links present."""

    identifier = ProblemIdentifier(contest_id="2183", problem_id="A")

    parser = ProblemPageParser(mock_http_client)
    data = await parser.parse_problem_page(identifier=identifier)

    expected_links = [
        "https://codeforces.com/blog/entry/149809",
        "https://codeforces.com/contest/2183/attachments/download/35276/solution.pdf",
        "https://codeforces.com/blog/entry/149944",
    ]

    assert data.title == "Real Problem Title"
    assert data.contest_name == "Hello 2026"
    assert len(data.possible_editorial_links) == 3
    for link in expected_links:
        assert link in data.possible_editorial_links


@pytest.mark.asyncio
async def test_parse_no_editorial() -> None:
    """Test parsing with no 'Contest materials' box exists."""

    client = AsyncMock()
    client.get_text.return_value = SAMPLE_HTML_NO_EDITORIAL
    identifier = ProblemIdentifier(contest_id="9999", problem_id="B")

    parser = ProblemPageParser(client)
    data = await parser.parse_problem_page(identifier=identifier)

    assert data.title == "Hard Problem"
    assert data.possible_editorial_links == []


@pytest.mark.asyncio
async def test_http_error_handling() -> None:
    """Test that HTTPerrors raise ParsingError."""

    client = AsyncMock()
    client.get_text.side_effect = Exception("Network Error")
    identifier = ProblemIdentifier(contest_id="1234", problem_id="A")

    with pytest.raises(ParsingError):
        parser = ProblemPageParser(client)
        await parser.parse_problem_page(identifier=identifier)


@pytest.mark.asyncio
async def test_convenience_function(mock_http_client) -> None:
    url = "https://codeforces.com/problemset/problem/2183/A"
    data = await parse_problem(url=url, http_client=mock_http_client)

    assert data.identifier.contest_id == "2183"
    assert data.title == "Real Problem Title"
