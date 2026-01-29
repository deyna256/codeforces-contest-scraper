from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from infrastructure.codeforces_client import CodeforcesApiClient


@pytest.fixture
def mock_http_client() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def codeforces_client(mock_http_client: AsyncMock) -> CodeforcesApiClient:
    return CodeforcesApiClient(http_client=mock_http_client)


@pytest.fixture
def setup_mock_response(mock_http_client: AsyncMock):
    def _setup(data: Any) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = data
        mock_http_client.get.return_value = mock_response

    return _setup


@pytest.fixture
def sample_problemset_response() -> dict:
    return {
        "status": "OK",
        "result": {
            "problems": [
                {
                    "contestId": 1000,
                    "index": "A",
                    "name": "Problem A Title",
                    "type": "PROGRAMMING",
                    "rating": 800,
                    "tags": ["math", "implementation"],
                },
                {
                    "contestId": 1000,
                    "index": "B",
                    "name": "Problem B Title",
                    "type": "PROGRAMMING",
                    "rating": 1200,
                    "tags": ["dp", "greedy"],
                },
                {
                    "contestId": 2000,
                    "index": "A",
                    "name": "Another Problem",
                    "type": "PROGRAMMING",
                    "rating": 900,
                    "tags": ["strings"],
                },
            ],
            "problemStatistics": [],
        },
    }


@pytest.fixture
def sample_contest_standings_response() -> dict:
    return {
        "status": "OK",
        "result": {
            "contest": {
                "id": 1000,
                "name": "Test Contest",
                "type": "CF",
                "phase": "FINISHED",
                "frozen": False,
                "durationSeconds": 7200,
            },
            "problems": [
                {
                    "contestId": 1000,
                    "index": "A",
                    "name": "Problem A",
                    "type": "PROGRAMMING",
                    "rating": 800,
                    "tags": ["math"],
                },
                {
                    "contestId": 1000,
                    "index": "B",
                    "name": "Problem B",
                    "type": "PROGRAMMING",
                    "rating": 1200,
                    "tags": ["dp"],
                },
            ],
            "rows": [],
        },
    }


@pytest.fixture
def sample_problem_data() -> dict:
    return {
        "contestId": 1000,
        "index": "A",
        "name": "Test Problem",
        "type": "PROGRAMMING",
        "rating": 800,
        "tags": ["math", "implementation"],
    }
