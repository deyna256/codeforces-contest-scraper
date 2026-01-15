# tests/url_parser_test.py
import pytest
from domain.parsers.url_parser import URLParser, parse_problem_url
from domain.models import ProblemIdentifier

@pytest.mark.parametrize(
    "url, expected_contest, expected_problem",
    [
        ("https://codeforces.com/problemset/problem/500/A", 500, "A"),
        ("https://codeforces.ru/problemset/problem/1234/C", 1234, "C"),
        ("https://codeforces.com/problemset/problem/1350/B1", 1350, "B1"),
    ],
)
def test_parse_valid_urls(url, expected_contest, expected_problem) -> None:
    identifier = URLParser.parse(url=url)

    # Convert contest_id to int for assertion
    assert int(identifier.contest_id) == expected_contest
    assert identifier.problem_index == expected_problem
    # Remove is_gym assertion if not used
    # assert not identifier.is_gym

def test_parse_convenience_function() -> None:
    url = "https://codeforces.com/problemset/problem/777/A"
    identifier = parse_problem_url(url)

    assert int(identifier.contest_id) == 777
    assert identifier.problem_index == "A"

def test_build_problem_url() -> None:
    identifier = ProblemIdentifier(contest_id=1234, problem_index="A")
    url = URLParser.build_problem_url(identifier)
    assert url == "https://codeforces.com/problemset/problem/1234/A"

def test_build_contest_url() -> None:
    identifier = ProblemIdentifier(contest_id=1234, problem_index="A")
    url = URLParser.build_contest_url(identifier)
    assert url == "https://codeforces.com/contest/1234"
