"""Test data for benchmarking editorial segmentation.

This file contains ground truth data for contests where we verify correct segmentation
of editorial content by problem.
"""

from typing import TypedDict


class SegmentationTestCase(TypedDict):
    """Test case for editorial segmentation."""

    contest_id: str
    editorial_urls: list[str]
    expected_problems: dict[tuple[str, str], bool]  # {(contest_id, problem_id): should_exist}
    description: str
    difficulty: str  # "easy", "medium", "hard"


# Ground truth test cases for segmentation - reduced to 3 for faster benchmarking
SEGMENTATION_TEST_CASES: list[SegmentationTestCase] = [
    # Simple case - single Div 4 contest (fast)
    {
        "contest_id": "2185",
        "editorial_urls": ["https://codeforces.com/blog/entry/150288"],
        "expected_problems": {
            ("2185", "A"): True,
            ("2185", "B"): True,
            ("2185", "C"): True,
            ("2185", "D"): True,
            ("2185", "E"): True,
            ("2185", "F"): True,
        },
        "description": "Codeforces Round 1074 (Div. 4)",
        "difficulty": "easy",
    },
    # Contest with no editorial (instant, no LLM call needed)
    {
        "contest_id": "2177",
        "editorial_urls": [],
        "expected_problems": {},
        "description": "ICPC 2025 - no editorial",
        "difficulty": "easy",
    },
    # Recent Div 3 contest (medium size)
    {
        "contest_id": "2184",
        "editorial_urls": ["https://codeforces.com/blog/entry/150033"],
        "expected_problems": {
            ("2184", "A"): True,
            ("2184", "B"): True,
            ("2184", "C"): True,
            ("2184", "D"): True,
            ("2184", "E"): True,
            ("2184", "F"): True,
            ("2184", "G"): True,
        },
        "description": "Codeforces Round 1072 (Div. 3)",
        "difficulty": "easy",
    },
]
