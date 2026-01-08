"""Editorial extractor using OpenAI API."""

import re
from datetime import datetime
from typing import Optional

from loguru import logger

from codeforces_editorial.openai.client import OpenAIClient
from codeforces_editorial.models import (
    Editorial,
    CodeSnippet,
    ProblemIdentifier,
    TutorialData,
)
from codeforces_editorial.utils.exceptions import ExtractionError


class EditorialExtractor:
    """Extracts editorial/solution from tutorial content using OpenAI."""

    def __init__(self, ai_client: Optional[OpenAIClient] = None):
        """
        Initialize extractor.

        Args:
            ai_client: OpenAI API client
        """
        self.ai_client = ai_client or OpenAIClient()

    def extract(
        self,
        tutorial: TutorialData,
        identifier: ProblemIdentifier,
        problem_title: str = "",
    ) -> Editorial:
        """
        Extract editorial for specific problem from tutorial.

        Args:
            tutorial: Tutorial data
            identifier: Problem identifier
            problem_title: Optional problem title

        Returns:
            Editorial object

        Raises:
            ExtractionError: If extraction fails
        """
        logger.info(f"Extracting editorial for problem {identifier}")

        try:
            # Use OpenAI to extract solution
            result = self.ai_client.extract_solution(
                tutorial_content=tutorial.content,
                problem_id=identifier.problem_id,
                problem_title=problem_title,
            )

            raw_response = result["raw_response"]

            # Parse the response into structured Editorial
            editorial = self._parse_response(
                raw_response,
                identifier,
                tutorial.url,
            )

            logger.info(f"Successfully extracted editorial for {identifier.problem_id}")
            return editorial

        except Exception as e:
            logger.error(f"Failed to extract editorial: {e}")
            raise ExtractionError(f"Failed to extract editorial for {identifier}: {e}") from e

    def _parse_response(
        self,
        response: str,
        identifier: ProblemIdentifier,
        source_url: str,
    ) -> Editorial:
        """
        Parse AI response into Editorial object.

        Args:
            response: Raw response from OpenAI
            identifier: Problem identifier
            source_url: Tutorial URL

        Returns:
            Editorial object
        """
        # Extract different sections from response
        # This is a simple parser - in production you might want structured output

        approach = self._extract_section(response, ["Approach", "Solution Approach"])
        algorithm = self._extract_section(response, ["Algorithm", "Data Structure"])
        time_complexity = self._extract_complexity(response, "Time")
        space_complexity = self._extract_complexity(response, "Space")
        code_snippets = self._extract_code_snippets(response)
        hints = self._extract_hints(response)
        notes = self._extract_section(response, ["Notes", "Additional Notes"])

        return Editorial(
            problem_id=identifier.problem_id,
            solution_text=response,  # Full response as solution text
            approach=approach,
            algorithm=algorithm,
            time_complexity=time_complexity,
            space_complexity=space_complexity,
            code_snippets=code_snippets,
            hints=hints,
            notes=notes,
            source_url=source_url,
            extracted_at=datetime.now(),
            ai_model=self.ai_client.model,
        )

    def _extract_section(self, text: str, headers: list[str]) -> Optional[str]:
        """
        Extract content from a section with given headers.

        Args:
            text: Full text
            headers: Possible section headers

        Returns:
            Section content if found
        """
        for header in headers:
            # Try to find section with this header
            patterns = [
                rf"##?\s*{header}\s*:?\s*\n(.*?)(?=\n##|\Z)",  # Markdown header
                rf"\*\*{header}\*\*:?\s*\n(.*?)(?=\n\*\*|\Z)",  # Bold header
                rf"{header}:?\s*\n(.*?)(?=\n[A-Z][a-z]+:|\Z)",  # Plain header
            ]

            for pattern in patterns:
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match:
                    content = match.group(1).strip()
                    if content:
                        return content

        return None

    def _extract_complexity(self, text: str, complexity_type: str) -> Optional[str]:
        """
        Extract time or space complexity.

        Args:
            text: Full text
            complexity_type: "Time" or "Space"

        Returns:
            Complexity string if found
        """
        # Look for "Time Complexity: O(...)" patterns
        patterns = [
            rf"{complexity_type}\s+Complexity\s*:?\s*(O\([^)]+\))",
            rf"{complexity_type}\s*:?\s*(O\([^)]+\))",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_code_snippets(self, text: str) -> list[CodeSnippet]:
        """
        Extract code snippets from text.

        Args:
            text: Full text

        Returns:
            List of code snippets
        """
        snippets = []

        # Find code blocks (markdown style)
        code_block_pattern = r"```(\w+)?\n(.*?)```"
        matches = re.finditer(code_block_pattern, text, re.DOTALL)

        for match in matches:
            language = match.group(1) or "text"
            code = match.group(2).strip()

            if code:
                snippets.append(
                    CodeSnippet(
                        language=language,
                        code=code,
                    )
                )

        return snippets

    def _extract_hints(self, text: str) -> list[str]:
        """
        Extract hints from text.

        Args:
            text: Full text

        Returns:
            List of hints
        """
        hints = []

        # Look for hints section
        hints_section = self._extract_section(text, ["Hints", "Progressive Hints"])

        if hints_section:
            # Try to parse numbered or bulleted hints
            lines = hints_section.split("\n")
            for line in lines:
                line = line.strip()
                # Remove numbering/bullets
                hint = re.sub(r"^[\d\-\*\.]+\s*", "", line)
                if hint:
                    hints.append(hint)

        return hints


def extract_editorial(
    tutorial: TutorialData,
    identifier: ProblemIdentifier,
    problem_title: str = "",
    ai_client: Optional[OpenAIClient] = None,
) -> Editorial:
    """
    Convenience function to extract editorial.

    Args:
        tutorial: Tutorial data
        identifier: Problem identifier
        problem_title: Optional problem title
        ai_client: Optional OpenAI client

    Returns:
        Editorial

    Raises:
        ExtractionError: If extraction fails
    """
    extractor = EditorialExtractor(ai_client)
    return extractor.extract(tutorial, identifier, problem_title)
