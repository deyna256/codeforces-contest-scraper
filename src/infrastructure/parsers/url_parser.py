"""Parser for Codeforces problem URLs."""

import re
from urllib.parse import urlparse

from loguru import logger

from domain.models.identifiers import ContestIdentifier, ProblemIdentifier
from .interfaces import URLParserProtocol


class URLParsingError(ValueError):
    """Invalid URL format or unable to parse URL."""

    pass


class URLParser(URLParserProtocol):
    """Parser for various Codeforces URL formats."""

    # Unified pattern matches: problemset/problem/1234/A
    PATTERN = r"codeforces\.(?:com|ru)/problemset/problem/(\d+)/([A-Z]\d*)"
    # Contest pattern matches: contest/1234 or gym/1234
    CONTEST_PATTERN = r"codeforces\.(?:com|ru)/(contest|gym)/(\d+)"

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

    @classmethod
    def parse_contest_url(cls, url: str) -> ContestIdentifier:
        """
        Parse Codeforces contest URL and extract contest identifier.
        """
        logger.debug(f"Parsing contest URL: {url}")

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise URLParsingError(f"Invalid URL format: {url}")
        except Exception as e:
            raise URLParsingError(f"Failed to parse URL: {url}") from e

        match = re.search(cls.CONTEST_PATTERN, url)
        if match:
            contest_type, contest_id = match.groups()
            is_gym = contest_type.lower() == "gym"

            identifier = ContestIdentifier(
                contest_id=contest_id,
                is_gym=is_gym,
            )

            logger.info(f"Parsed URL to contest: {identifier}")
            return identifier

        # No pattern matched
        raise URLParsingError(
            f"Unrecognized Codeforces contest URL format: {url}. "
            "Expected format: https://codeforces.com/contest/<contest_id>"
        )

    @classmethod
    def build_contest_url(cls, identifier: ContestIdentifier) -> str:
        """
        Build contest URL from identifier.
        """
        path_type = "gym" if identifier.is_gym else "contest"
        url = f"https://codeforces.com/{path_type}/{identifier.contest_id}"

        logger.debug(f"Built contest URL: {url}")
        return url
