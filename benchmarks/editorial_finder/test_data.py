"""Test data for benchmarking editorial finder.

This file contains ground truth data for contests where we know the correct editorial URL.
You should manually verify and expand this list with real contest data.
"""

from typing import TypedDict


class TestCase(TypedDict):
    """Test case with ground truth."""

    contest_id: str
    expected_editorial: list[str]  # Empty list if no editorial exists
    description: str
    difficulty: str  # "easy", "medium", "hard"


# Ground truth test cases
# TODO: Expand this list with manually verified contest data
FINDER_TEST_CASES: list[TestCase] = [
    # Example cases - replace with real verified data
    {
        "contest_id": "2185",
        "expected_editorial": ["https://codeforces.com/blog/entry/150288"],
        "description": "Codeforces Round 1074 (Div. 4)",
        "difficulty": "easy",
    },
    {
        "contest_id": "2190",
        "expected_editorial": ["https://codeforces.com/blog/entry/150256"],
        "description": "Codeforces Round 1073 (Div. 1)",
        "difficulty": "easy",
    },
    {
        "contest_id": "2191",
        "expected_editorial": ["https://codeforces.com/blog/entry/150256"],
        "description": "Codeforces Round 1073 (Div. 2)",
        "difficulty": "medium",
    },
    {
        "contest_id": "2184",
        "expected_editorial": ["https://codeforces.com/blog/entry/150033"],
        "description": "Codeforces Round 1072 (Div. 3)",
        "difficulty": "easy",
    },
    {
        "contest_id": "2183",
        "expected_editorial": ["https://codeforces.com/blog/entry/149944"],
        "description": "Hello 2026",
        "difficulty": "easy",
    },
    {
        "contest_id": "2182",
        "expected_editorial": ["https://codeforces.com/blog/entry/149733"],
        "description": "Educational Codeforces Round 186 (Rated for Div. 2)",
        "difficulty": "easy",
    },
    {
        "contest_id": "2178",
        "expected_editorial": ["https://codeforces.com/blog/entry/149548"],
        "description": "Good Bye 2025",
        "difficulty": "easy",
    },
    {
        "contest_id": "2177",
        "expected_editorial": [],
        "description": "ICPC 2025 Online Winter Challenge powered by Huawei",
        "difficulty": "easy",
    },
    {
        "contest_id": "36",
        "expected_editorial": [
            "https://codeforces.com/blog/entry/773",
            "https://codeforces.com/blog/entry/774",
            "https://codeforces.com/blog/entry/768",
            "https://codeforces.com/blog/entry/769",
            "https://codeforces.com/blog/entry/770",
            "https://codeforces.com/blog/entry/771",
        ],
        "description": "Codeforces Beta Round 36",
        "difficulty": "easy",
    },
    {
        "contest_id": "2102",
        "expected_editorial": ["https://codeforces.com/blog/entry/142788"],
        "description": "Codeforces Round 1024 (Div. 2)",
        "difficulty": "easy",
    },
    {
        "contest_id": "2124",
        "expected_editorial": ["https://codeforces.com/blog/entry/144382"],
        "description": "EPIC Institute of Technology Round Summer 2025 (Codeforces Round 1036, Div. 1 + Div. 2)",
        "difficulty": "easy",
    },
    {
        "contest_id": "1975",
        "expected_editorial": ["https://codeforces.com/blog/entry/129801"],
        "description": "Codeforces Round 947 (Div. 1 + Div. 2)",
        "difficulty": "easy",
    },
    {
        "contest_id": "1970",
        "expected_editorial": ["https://codeforces.com/blog/entry/129149"],
        "description": "Helvetic Coding Contest 2024",
        "difficulty": "easy",
    },
    {
        "contest_id": "1992",
        "expected_editorial": ["https://codeforces.com/blog/entry/131461"],
        "description": "Codeforces Round 957 (Div. 3)",
        "difficulty": "easy",
    },
    {
        "contest_id": "1991",
        "expected_editorial": ["https://codeforces.com/blog/entry/132021"],
        "description": "Pinely Round 4 (Div. 1 + Div. 2)",
        "difficulty": "easy",
    },
    {
        "contest_id": "2010",
        "expected_editorial": [],
        "description": "Testing Round 19 (Div. 3)",
        "difficulty": "easy",
    },
    {
        "contest_id": "1866",
        "expected_editorial": ["https://codeforces.com/blog/entry/120025"],
        "description": "COMPFEST 15 - Preliminary Online Mirror (Unrated, ICPC Rules, Teams Preferred)",
        "difficulty": "easy",
    },
    {
        "contest_id": "1860",
        "expected_editorial": ["https://codeforces.com/blog/entry/119504"],
        "description": "Educational Codeforces Round 153 (Rated for Div. 2)",
        "difficulty": "easy",
    },
    {
        "contest_id": "1856",
        "expected_editorial": ["https://codeforces.com/blog/entry/119058"],
        "description": "Codeforces Round 890 (Div. 2) supported by Constructor Institute",
        "difficulty": "easy",
    },
    {
        "contest_id": "1826",
        "expected_editorial": ["https://codeforces.com/blog/entry/115892"],
        "description": "Codeforces Round 870 (Div. 2)",
        "difficulty": "easy",
    },
    {
        "contest_id": "1774",
        "expected_editorial": ["https://codeforces.com/blog/entry/110184"],
        "description": "Polynomial Round 2022 (Div. 1 + Div. 2, Rated, Prizes!)",
        "difficulty": "easy",
    },
    {
        "contest_id": "1770",
        "expected_editorial": ["https://codeforces.com/blog/entry/110754"],
        "description": "Good Bye 2022: 2023 is NEAR",
        "difficulty": "easy",
    },
    # Add more test cases here
    # To find contest IDs and editorial URLs:
    # 1. Go to https://codeforces.com/contests
    # 2. Click on a contest
    # 3. Look for "Tutorial" or "Editorial" link in sidebar
    # 4. Copy contest ID and editorial URL
]
