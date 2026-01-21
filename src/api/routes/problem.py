from litestar import Controller, post
from litestar.status_codes import HTTP_200_OK
from loguru import logger

from api.schemas import ProblemRequest, ProblemResponse
from services import create_problem_service


class ProblemController(Controller):
    path = "/problems"

    @post("/", status_code=HTTP_200_OK)
    async def get_problem(
        self,
        data: ProblemRequest,
    ) -> ProblemResponse:
        """
        Get problem information from Codeforces API.

        Request body:
        - url: Codeforces problem URL (e.g., "https://codeforces.com/problemset/problem/2190/B2")
        """
        logger.debug(f"API request for problem URL: {data.url}")

        service = create_problem_service()
        problem = await service.get_problem_by_url(data.url)

        return ProblemResponse(
            statement=problem.statement,
            tags=problem.tags,
            rating=problem.rating,
            contest_id=problem.contest_id,
            id=problem.id,
            url=data.url,
            description=problem.description,
            time_limit=problem.time_limit,
            memory_limit=problem.memory_limit,
        )
