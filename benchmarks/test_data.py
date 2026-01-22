"""Test data for benchmarking editorial finder.

This file contains ground truth data for contests where we know the correct editorial URL.
You should manually verify and expand this list with real contest data.
"""

from typing import TypedDict


class TestCase(TypedDict):
    """Test case with ground truth."""

    contest_id: str
    expected_editorial: str | None  # None if no editorial exists
    description: str
    difficulty: str  # "easy", "medium", "hard"


# Ground truth test cases
# TODO: Expand this list with manually verified contest data
BENCHMARK_TEST_CASES: list[TestCase] = [
    # Example cases - replace with real verified data
    {
        "contest_id": "2185",
        "expected_editorial": "https://codeforces.com/blog/entry/150288",
        "description": "Codeforces Round 1074 (Div. 4)",
        "difficulty": "easy",
    },
    {
        "contest_id": "2190",
        "expected_editorial": "https://codeforces.com/blog/entry/150256",
        "description": "Codeforces Round 1073 (Div. 1)",
        "difficulty": "easy",
    },
    {
        "contest_id": "2191",
        "expected_editorial": "https://codeforces.com/blog/entry/150256",
        "description": "Codeforces Round 1073 (Div. 2)",
        "difficulty": "medium",
    },
    {
        "contest_id": "2184",
        "expected_editorial": "https://codeforces.com/blog/entry/150033",
        "description": "Codeforces Round 1072 (Div. 3)",
        "difficulty": "easy",
    },
    # Add more test cases here
    # To find contest IDs and editorial URLs:
    # 1. Go to https://codeforces.com/contests
    # 2. Click on a contest
    # 3. Look for "Tutorial" or "Editorial" link in sidebar
    # 4. Copy contest ID and editorial URL
]


def get_test_cases(difficulty: str | None = None) -> list[TestCase]:
    """
    Get test cases, optionally filtered by difficulty.

    Args:
        difficulty: Filter by difficulty level ("easy", "medium", "hard") or None for all

    Returns:
        List of test cases
    """
    if difficulty is None:
        return BENCHMARK_TEST_CASES
    return [tc for tc in BENCHMARK_TEST_CASES if tc["difficulty"] == difficulty]


def get_test_case_by_id(contest_id: str) -> TestCase | None:
    """
    Get a specific test case by contest ID.

    Args:
        contest_id: Contest ID to look up

    Returns:
        Test case or None if not found
    """
    for tc in BENCHMARK_TEST_CASES:
        if tc["contest_id"] == contest_id:
            return tc
    return None
