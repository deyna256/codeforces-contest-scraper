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


# Ground truth test cases for segmentation
SEGMENTATION_TEST_CASES: list[SegmentationTestCase] = [
    # Simple case - single Div 4 contest
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
    # Complex - Div 1 + Div 2 combined
    {
        "contest_id": "2191",
        "editorial_urls": ["https://codeforces.com/blog/entry/150256"],
        "expected_problems": {
            ("2190", "A"): True,  # Div 1
            ("2190", "B"): True,
            ("2190", "C"): True,
            ("2190", "D"): True,
            ("2190", "E"): True,
            ("2191", "A"): True,  # Div 2
            ("2191", "B"): True,
            ("2191", "C"): True,
            ("2191", "D"): True,
            ("2191", "E"): True,
            ("2191", "F"): True,
        },
        "description": "Codeforces Round 1073 (Div. 1 + Div. 2)",
        "difficulty": "hard",
    },
    # Old contest with multiple editorial URLs
    {
        "contest_id": "36",
        "editorial_urls": [
            "https://codeforces.com/blog/entry/773",
            "https://codeforces.com/blog/entry/774",
            "https://codeforces.com/blog/entry/768",
        ],
        "expected_problems": {
            ("36", "A"): True,
            ("36", "B"): True,
            ("36", "C"): True,
            ("36", "D"): True,
            ("36", "E"): True,
        },
        "description": "Beta Round 36 - multiple editorial URLs",
        "difficulty": "medium",
    },
    # Contest with no editorial
    {
        "contest_id": "2177",
        "editorial_urls": [],
        "expected_problems": {},
        "description": "ICPC 2025 - no editorial",
        "difficulty": "easy",
    },
    # Recent Div 3 contest
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
    # Hello 2026
    {
        "contest_id": "2183",
        "editorial_urls": ["https://codeforces.com/blog/entry/149944"],
        "expected_problems": {
            ("2183", "A"): True,
            ("2183", "B"): True,
            ("2183", "C"): True,
            ("2183", "D"): True,
            ("2183", "E"): True,
            ("2183", "F"): True,
        },
        "description": "Hello 2026",
        "difficulty": "medium",
    },
    # Educational round
    {
        "contest_id": "2182",
        "editorial_urls": ["https://codeforces.com/blog/entry/149733"],
        "expected_problems": {
            ("2182", "A"): True,
            ("2182", "B"): True,
            ("2182", "C"): True,
            ("2182", "D"): True,
            ("2182", "E"): True,
            ("2182", "F"): True,
        },
        "description": "Educational Codeforces Round 186 (Rated for Div. 2)",
        "difficulty": "easy",
    },
]
