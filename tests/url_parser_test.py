# src/domain/parsers/url_parser.py
from domain.models.problem import ProblemIdentifier


class URLParser:
    @staticmethod
    def parse(url: str) -> ProblemIdentifier:
        """
        Parse a Codeforces problem URL and return a ProblemIdentifier.

        Examples:
        https://codeforces.com/problemset/problem/1234/A
        https://codeforces.com/contest/567/problem/B
        """
        try:
            parts = url.rstrip("/").split("/")
            if "problemset" in url:
                contest_id = int(parts[-2])
                problem_index = parts[-1]
            elif "contest" in url:
                contest_id = int(parts[-2])
                problem_index = parts[-1]
            else:
                raise ValueError("URL not recognized as a Codeforces problem")
            return ProblemIdentifier(contest_id=contest_id, problem_index=problem_index)
        except Exception as e:
            raise ValueError(f"Invalid Codeforces URL: {url}") from e
