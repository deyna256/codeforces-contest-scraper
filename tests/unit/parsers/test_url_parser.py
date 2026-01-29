import pytest

from domain.models.identifiers import ContestIdentifier, ProblemIdentifier
from infrastructure.parsers import URLParser, URLParsingError


@pytest.mark.parametrize(
    "url, expected_contest, expected_problem",
    [
        ("https://codeforces.com/problemset/problem/500/A", "500", "A"),
        ("https://codeforces.ru/problemset/problem/1234/C", "1234", "C"),
        ("https://codeforces.com/problemset/problem/1350/B1", "1350", "B1"),
    ],
)
def test_parse_problem_url(url, expected_contest, expected_problem):
    identifier = URLParser.parse(url=url)

    assert identifier.contest_id == expected_contest
    assert identifier.problem_id == expected_problem


def test_parse_problem_url_rejects_invalid():
    invalid_urls = [
        "not_a_url",
        "https://google.com",
        "https://codeforces.com/blog/entry/123",
        "https://codeforces.com/contest/abc/problem/A",
        "https://codeforces.com/contest/1234/problem/C",
    ]

    for url in invalid_urls:
        with pytest.raises(URLParsingError):
            URLParser.parse(url=url)


def test_build_problem_url():
    identifier = ProblemIdentifier(contest_id="1234", problem_id="A")

    url = URLParser.build_problem_url(identifier=identifier)

    assert url == "https://codeforces.com/problemset/problem/1234/A"


@pytest.mark.parametrize(
    "url, expected_contest_id",
    [
        ("https://codeforces.com/contest/1500", "1500"),
        ("https://codeforces.ru/contest/2000", "2000"),
    ],
)
def test_parse_contest_url(url, expected_contest_id):
    identifier = URLParser.parse_contest_url(url)

    assert identifier.contest_id == expected_contest_id


def test_parse_contest_url_rejects_invalid():
    invalid_urls = [
        "not_a_url",
        "https://google.com",
        "https://codeforces.com/blog/entry/123",
        "https://codeforces.com/contest/abc",
        "https://codeforces.com/problemset/problem/1234/A",
    ]

    for url in invalid_urls:
        with pytest.raises(URLParsingError):
            URLParser.parse_contest_url(url)


def test_parse_contest_url_rejects_gym():
    gym_urls = [
        "https://codeforces.com/gym/102942",
        "https://codeforces.ru/gym/500000",
    ]

    for url in gym_urls:
        with pytest.raises(URLParsingError) as exc_info:
            URLParser.parse_contest_url(url)
        assert "gym contests not supported" in str(exc_info.value).lower()


def test_build_contest_url():
    identifier = ContestIdentifier(contest_id="1500")

    url = URLParser.build_contest_url(identifier)

    assert url == "https://codeforces.com/contest/1500"
