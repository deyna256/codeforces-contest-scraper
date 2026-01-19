"""Parser for Codeforces problem URLs."""

import re
from urllib.parse import urlparse

from loguru import logger

from domain.models import ProblemIdentifier
from domain.exceptions import URLParsingError


class URLParser:
    """Parser for various Codeforces URL formats."""

    # Unified pattern matches: problemset/problem/1234/A
    PATTERN = r"codeforces\.(?:com|ru)/problemset/problem/(\d+)/([A-Z]\d*)"

    @classmethod
    def parse(cls, url: str) -> ProblemIdentifier:
        """
        Parse Codeforces problem URL and extract problem identifier.
        """
        logger.debug(f"Parsing URL: {url}")

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise URLParsingError(f"Invalid URL format: {url}")
        except Exception as e:
            raise URLParsingError(f"Failed to parse URL: {url}") from e

        match = re.search(cls.PATTERN, url)
        if match:
            contest_id, problem_id = match.groups()

            identifier = ProblemIdentifier(
                contest_id=contest_id,
                problem_id=problem_id,
                is_gym=False,
            )

            logger.info(f"Parsed URL to problem: {identifier}")
            return identifier

        # No pattern matched
        raise URLParsingError(
            f"Unrecognized Codeforces URL format: {url}. "
            "Expected format: https://codeforces.com/problemset/problem/<contest_id>/<problem_id>"
        )

    @classmethod
    def build_problem_url(cls, identifier: ProblemIdentifier) -> str:
        """
        Build problem URL from identifier.
        """

        url = f"https://codeforces.com/problemset/problem/{identifier.contest_id}/{identifier.problem_id}"

        logger.debug(f"Built problem URL: {url}")
        return url

