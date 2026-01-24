from litestar import Controller, post
from litestar.status_codes import HTTP_200_OK
from loguru import logger

from api.schemas.contest import ContestProblemResponse, ContestRequest, ContestResponse
from services import create_contest_service


class ContestController(Controller):
    path = "/contest"

    @post("/", status_code=HTTP_200_OK)
    async def get_contest(
        self,
        data: ContestRequest,
    ) -> ContestResponse:
        """
        Get contest information from Codeforces API.

        Request body:
        - url: Codeforces contest URL (e.g., "https://codeforces.com/contest/2191")
        """
        logger.debug(f"API request for contest URL: {data.url}")

        service = create_contest_service()
        contest = await service.get_contest_by_url(data.url)

        # Map ContestProblem to ContestProblemResponse
        problem_responses = [
            ContestProblemResponse(
                contest_id=problem.contest_id,
                id=problem.id,
                title=problem.title,
                statement=problem.statement,
                rating=problem.rating,
                tags=problem.tags,
                time_limit=problem.time_limit,
                memory_limit=problem.memory_limit,
                explanation=problem.explanation,
            )
            for problem in contest.problems
        ]

        return ContestResponse(
            contest_id=contest.contest_id,
            title=contest.title,
            problems=problem_responses,
            editorials=contest.editorials,
        )
