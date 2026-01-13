"""Editorial extractor using OpenAI API."""

import re
from datetime import datetime
from typing import Optional

from loguru import logger

from domain.models import (
    Editorial,
    CodeSnippet,
    ProblemIdentifier,
    TutorialData,
)
from domain.exceptions import ExtractionError
from infrastructure.openai_client import AsyncOpenAIClient


class EditorialExtractor:
    """Extracts editorial/solution from tutorial content using OpenAI."""

    def __init__(self, ai_client):
        """
        Initialize extractor.

        Args:
            ai_client: Async OpenAI API client
        """
        self.ai_client = ai_client

    async def extract(
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
            result = await self.ai_client.extract_solution(
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
        # Check if AI couldn't find the problem in the tutorial
        if response.strip().startswith("NOT_FOUND"):
            logger.warning(f"AI could not find problem {identifier.problem_id} in tutorial")
            raise ExtractionError(
                f"Could not find editorial for problem {identifier.problem_id} in the tutorial. "
                f"AI response: {response[:500]}"
            )

        # Extract metadata and original editorial text
        # The response should have metadata at the top, followed by the original text

        # Try to split metadata section from the actual editorial
        metadata_pattern = r"^---\n(.*?)\n---\n\n(.+)$"
        match = re.search(metadata_pattern, response, re.DOTALL)

        if match:
            # Metadata found, use the text after metadata
            solution_text = match.group(2).strip()
        else:
            # No metadata separator, use full response
            solution_text = response.strip()

        return Editorial(
            problem_id=identifier.problem_id,
            solution_text=solution_text,  # Original editorial text
            source_url=source_url,
            extracted_at=datetime.now(),
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
        
async def extract_editorial(
    tutorial: TutorialData,
    identifier: ProblemIdentifier,
    problem_title: str = "",
    ai_client: Optional[AsyncOpenAIClient] = None,
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
    return await extractor.extract(tutorial, identifier, problem_title)
