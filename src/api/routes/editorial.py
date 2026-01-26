"""API routes for editorial content."""

from litestar import Controller, get
from litestar.status_codes import HTTP_200_OK
from loguru import logger

from api.schemas.editorial import ContestEditorialResponse, EditorialResponse
from services import create_contest_service


class EditorialController(Controller):
    """Controller for editorial-related endpoints."""

    path = "/editorial"

    @get("/{contest_id:str}", status_code=HTTP_200_OK)
    async def get_editorial(
        self,
        contest_id: str,
    ) -> ContestEditorialResponse:
        """
        Get editorial content for a contest, segmented by individual problems.

        Path parameters:
        - contest_id: Codeforces contest ID (e.g., "2191")

        Returns editorial analyses for all problems in the contest.
        Each response includes problem_id and analysis_text.
        """
        logger.debug(f"API request for editorial content: contest_id={contest_id}")

        service = create_contest_service()
        editorial_data = await service.get_editorial_content(contest_id)

        # Map ContestEditorial to ContestEditorialResponse
        editorial_responses = [
            EditorialResponse(
                problem_id=editorial.problem_id,
                analysis_text=editorial.analysis_text,
            )
            for editorial in editorial_data.editorials
        ]

        return ContestEditorialResponse(
            contest_id=editorial_data.contest_id,
            editorials=editorial_responses,
        )
