"""Async orchestrator for coordinating the editorial extraction process."""
from loguru import logger

from domain.models import Editorial, ProblemData
from domain.parsers.url_parser import URLParser
from domain.parsers.problem_page import ProblemPageParser
from domain.parsers.tutorial_parser import TutorialParser
from domain.fetchers.tutorial_finder import TutorialFinder
from domain.extractors.editorial_extractor import EditorialExtractor
from domain.exceptions import CodeforcesEditorialError


class AsyncEditorialOrchestrator:
    """Async orchestrator for editorial extraction process."""

    def __init__(
        self,
        http_client,
        ai_client,
        cache_client=None,
        use_cache: bool = True,
    ):
        self.http_client = http_client
        self.ai_client = ai_client
        self.cache_client = cache_client
        self.use_cache = False  # 🔴 disable cache for now (important)

        self.problem_parser = ProblemPageParser(self.http_client)
        self.tutorial_parser = TutorialParser(self.http_client)
        self.tutorial_finder = TutorialFinder(self.ai_client, self.http_client)
        self.editorial_extractor = EditorialExtractor(self.ai_client)

    async def get_editorial(self, url: str) -> tuple[Editorial, ProblemData]:
        logger.info(f"Getting editorial for URL: {url}")

        try:
            logger.info("Step 1: Parsing URL")
            identifier = URLParser.parse(url)

            logger.info("Step 2: Parsing problem page")
            problem_data = await self.problem_parser.parse_problem_page(identifier)

            logger.info("Step 3: Finding tutorial URL")
            tutorial_url = await self.tutorial_finder.find_tutorial(identifier)

            logger.info("Step 4: Parsing tutorial content")
            tutorial_data = await self.tutorial_parser.parse(tutorial_url)

            logger.info("Step 5: Extracting editorial")
            editorial = await self.editorial_extractor.extract(
                tutorial_data,
                identifier,
                problem_data.title,
            )

            logger.info("Editorial extraction completed successfully")
            return editorial, problem_data

        except CodeforcesEditorialError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in orchestrator: {e}")
            raise CodeforcesEditorialError(
                f"Failed to get editorial: {e}"
            ) from e
