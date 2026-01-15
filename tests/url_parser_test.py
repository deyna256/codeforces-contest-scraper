import pytest

from domain.parsers.url_parser import URLParser, parse_problem_url
from domain.models import ProblemIdentifier
from domain.exceptions import URLParsingError


@pytest.mark.parametrize(
    "url, expected_contest, expected_problem",
    [
        # 1. Problemset URL
        ("https://codeforces.com/problemset/problem/500/A", "500", "A"),
        # 2. Russian Domain
        ("https://codeforces.ru/problemset/problem/1234/C", "1234", "C"),
        # 3. Complex Problem Index
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
        "not_a_url",  # wrong url
        "https://google.com",  # wrong site
        "https://codeforces.com/blog/entry/123",  # Valid site, wrong page
        "https://codeforces.com/contest/abc/problem/A",  # Non-numeric contest ID
        "https://codeforces.com/gym/102942/problem/F",  # Gym (rejected)
        "https://codeforces.com/contest/1234/problem/C",  # Contest (rejected)
    ]

    for url in invalid_urls:
        with pytest.raises((URLParsingError)):
            URLParser.parse(url=url)


def test_build_problem_url() -> None:
    contest_id = ProblemIdentifier(contest_id="1234", problem_id="A")
    assert (
        URLParser.build_problem_url(identifier=contest_id)
        == "https://codeforces.com/problemset/problem/1234/A"
    )


def test_build_contest_url() -> None:
    contest_id = ProblemIdentifier(contest_id="1234", problem_id="A")
    assert (
        URLParser.build_contest_url(identifier=contest_id) == "https://codeforces.com/contest/1234"
    )


def test_parse_convenience_function() -> None:
    url = "https://codeforces.com/problemset/problem/777/A"
    identifier = parse_problem_url(url)
    assert identifier.contest_id == "777"
    assert identifier.problem_id == "A"
