"""Codeforces API client for fetching problem data."""

from loguru import logger

from domain.exceptions import NetworkError, ProblemNotFoundError
from domain.models import ProblemIdentifier, Problem
from infrastructure.http_client import AsyncHTTPClient


class CodeforcesApiClient:
    """Client for accessing Codeforces API to fetch problem information."""

    BASE_URL = "https://codeforces.com/api"

    def __init__(self, http_client: AsyncHTTPClient | None = None):
        """Initialize with optional HTTP client."""
        self.http_client = http_client or AsyncHTTPClient()

    async def fetch_problemset_problems(self) -> dict:
        """Fetch all problems from Codeforces problemset."""
        url = f"{self.BASE_URL}/problemset.problems"

        logger.debug(f"Fetching problemset from: {url}")

        response = await self.http_client.get(url)

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse Codeforces API response: {e}")
            raise NetworkError(f"Invalid response from Codeforces API: {e}")

        if data.get("status") != "OK":
            logger.error(f"Codeforces API returned status: {data.get('status')}")
            raise NetworkError(f"Codeforces API error: {data.get('status')}")

        return data

    async def get_problem_details(self, contest_id: str, problem_id: str) -> dict:
        """Get detailed information about a specific problem."""
        logger.debug(f"Fetching problem details for {contest_id}/{problem_id}")

        # Fetch all problems and find the specific one
        problems_data = await self.fetch_problemset_problems()
        problems = problems_data.get("result", {}).get("problems", [])

        # Find the specific problem
        for problem in problems:
            if str(problem.get("contestId")) == contest_id and problem.get("index") == problem_id:
                return problem

        # If not found, try to get contest information for additional context
        logger.warning(f"Problem {contest_id}/{problem_id} not found in problemset")
        raise ProblemNotFoundError(f"Problem {contest_id}/{problem_id} not found")

    async def get_problem(self, identifier: ProblemIdentifier) -> Problem:
        """Get Problem domain model for given identifier."""
        logger.info(f"Getting problem: {identifier}")

        problem_data = await self.get_problem_details(identifier.contest_id, identifier.problem_id)

        # Map Codeforces API response to our Problem model
        problem = Problem(
            statement=problem_data.get("name", ""),
            tags=problem_data.get("tags", []),
            rating=problem_data.get("rating"),
            contest_id=str(problem_data.get("contestId")),
            id=problem_data.get("index", ""),
        )

        return problem
