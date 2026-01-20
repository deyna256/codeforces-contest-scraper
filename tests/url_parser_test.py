import pytest

from infrastructure.parsers import URLParser
from domain.models.identifiers import ProblemIdentifier
from infrastructure.parsers import URLParsingError


@pytest.mark.parametrize(
    "url, expected_contest, expected_problem",
    [
        ("https://codeforces.com/problemset/problem/500/A", "500", "A"),
        ("https://codeforces.ru/problemset/problem/1234/C", "1234", "C"),
        ("https://codeforces.com/problemset/problem/1350/B1", "1350", "B1"),
    ],
)
def test_parse_valid_urls(url, expected_contest, expected_problem) -> None:
    identifier = URLParser.parse(url=url)

    assert identifier.contest_id == expected_contest
    assert identifier.problem_id == expected_problem
    assert not identifier.is_gym


def test_parse_invalid_urls() -> None:
    invalid_urls = [
        "not_a_url",
        "https://google.com",
        "https://codeforces.com/blog/entry/123",
        "https://codeforces.com/contest/abc/problem/A",
        "https://codeforces.com/gym/102942/problem/F",
        "https://codeforces.com/contest/1234/problem/C",
    ]

    for url in invalid_urls:
        with pytest.raises((URLParsingError)):
            URLParser.parse(url=url)


def test_build_problem_url() -> None:
    contest_id = ProblemIdentifier(contest_id="1234", problem_id="A", is_gym=False)
    assert (
        URLParser.build_problem_url(identifier=contest_id)
        == "https://codeforces.com/problemset/problem/1234/A"
    )
