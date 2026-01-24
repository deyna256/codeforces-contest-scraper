"""LLM-powered parser for editorial blog entries to extract problem-specific solutions."""

import json
import re
from typing import Dict, List, Optional, Any

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from domain.models.editorial import Editorial, ContestEditorial
from infrastructure.http_client import AsyncHTTPClient
from infrastructure.llm_client import LLMError, OpenRouterClient
from infrastructure.parsers.errors import (
    EditorialContentFetchError,
    EditorialContentParseError,
    LLMSegmentationError,
    EditorialNotFoundError,
)


class EditorialContentParser:
    """Parses editorial blog entries into individual problem solutions using LLM."""

    def __init__(
        self,
        http_client: Optional[AsyncHTTPClient] = None,
        llm_client: Optional[OpenRouterClient] = None
    ):
        """
        Initialize editorial content parser.

        Args:
            http_client: HTTP client for fetching content
            llm_client: LLM client for content segmentation
        """
        self.http_client = http_client or AsyncHTTPClient()
        self.llm_client = llm_client

    async def parse_editorial_content(
        self,
        contest_id: str,
        editorial_urls: List[str]
    ) -> ContestEditorial:
        """
        Parse editorial content and segment into individual problem solutions.

        Args:
            contest_id: Contest identifier
            editorial_urls: List of editorial blog entry URLs

        Returns:
            ContestEditorial with segmented problem analyses

        Raises:
            EditorialNotFoundError: If no editorial URLs provided
            EditorialContentFetchError: If all URLs fail to fetch
            LLMSegmentationError: If LLM fails to segment content
        """
        if not editorial_urls:
            raise EditorialNotFoundError(contest_id)

        # Collect content from all URLs
        all_content = []
        failed_urls = []

        for url in editorial_urls:
            try:
                content = await self._fetch_editorial_content(url)
                all_content.append(content)
                logger.debug(f"Successfully fetched content from {url}")
            except Exception as e:
                logger.warning(f"Failed to fetch content from {url}: {e}")
                failed_urls.append(url)
                continue

        if not all_content:
            raise EditorialContentFetchError(
                f"All editorial URLs failed to load: {failed_urls}",
                contest_id
            )

        # Combine all editorial content
        combined_content = await self._combine_editorial_content(all_content)

        # Use LLM to segment into problem-specific solutions
        problem_solutions = await self._segment_by_problems(
            combined_content, contest_id
        )

        # Convert to domain objects
        editorials = [
            Editorial(problem_id=pid, analysis_text=text)
            for pid, text in problem_solutions.items()
        ]

        return ContestEditorial(contest_id=contest_id, editorials=editorials)

    async def _fetch_editorial_content(self, url: str) -> str:
        """
        Fetch and extract text content from editorial URL.

        Args:
            url: Editorial blog entry URL

        Returns:
            Extracted text content

        Raises:
            EditorialContentFetchError: If URL fetch fails
            EditorialContentParseError: If HTML parsing fails
        """
        try:
            response = await self.http_client.get(url)
            html_content = response.text

        except Exception as e:
            logger.error(f"Failed to fetch editorial content from {url}: {e}")
            raise EditorialContentFetchError(url) from e

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            text_content = self._extract_blog_content(soup)

            if not text_content or len(text_content.strip()) < 100:
                raise EditorialContentParseError(url)

            return text_content

        except Exception as e:
            logger.error(f"Failed to parse HTML content from {url}: {e}")
            raise EditorialContentParseError(url) from e

    def _extract_blog_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content from Codeforces blog entry.

        Args:
            soup: Parsed HTML content

        Returns:
            Extracted blog text content
        """
        # Try to find the main blog content
        content_selectors = [
            ".ttypography",  # Current Codeforces blog content
            ".entry-content",
            ".blog-entry-content",
            "#blog-entry-text",
            ".problem-statement",  # Alternative content selectors
        ]

        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                text = content_element.get_text(separator="\n", strip=True)

                # Clean up the text
                text = self._clean_extracted_text(text)

                if len(text.strip()) > 200:  # Minimum viable content length
                    return text

        # Fallback: search for any large text block
        body = soup.find("body")
        if body:
            text = body.get_text(separator="\n", strip=True)
            return self._clean_extracted_text(text)

        return ""

    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text content.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Remove common UI elements and garbage text
        remove_patterns = [
            r'Material\s+You\s+Should\s+Know.*?(?=\n|\Z)',  # Common header
            r'Problem\s+tags\s*:.*?(?=\n|\Z)',  # Tags section
            r'Download\s+as\s+.*?(?=\n|\Z)',  # Download links
            r'Submit\s+a\s+ticket.*?(?=\n|\Z)',  # Support links
            r'Related\s+topics.*?(?=\n|\Z)',  # Related topics
        ]

        for pattern in remove_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)

        # Normalize spacing
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n\s+', '\n', text)  # Space after newline to just newline

        return text.strip()

    async def _combine_editorial_content(self, content_list: List[str]) -> str:
        """
        Combine content from multiple editorial URLs.

        Args:
            content_list: List of text content from different URLs

        Returns:
            Combined content with section headers
        """
        if len(content_list) == 1:
            return content_list[0]

        # Add separators between different editorial sources
        combined_parts = []
        for i, content in enumerate(content_list, 1):
            combined_parts.append(f"=== EDITORIAL SOURCE {i} ===\n\n{content}")

        return "\n\n".join(combined_parts)

    async def _segment_by_problems(
        self,
        full_text: str,
        contest_id: str
    ) -> Dict[str, str]:
        """
        Use LLM to segment editorial text into problem-specific solutions.

        Args:
            full_text: Combined editorial text content
            contest_id: Contest identifier for context

        Returns:
            Dictionary mapping problem IDs (A, B, C, etc.) to solution text

        Raises:
            LLMSegmentationError: If LLM fails to segment properly
        """
        if not self.llm_client:
            raise LLMSegmentationError(contest_id, "No LLM client available")

        if not full_text or len(full_text.strip()) < 50:
            raise LLMSegmentationError(contest_id, "Content too short for segmentation")

        try:
            result = await self._ask_llm_for_segmentation(full_text, contest_id)

            if not result or not isinstance(result, dict):
                raise LLMSegmentationError(contest_id, f"Invalid LLM response format: {result}")

            return result

        except LLMError as e:
            logger.error(f"LLM error during editorial segmentation: {e}")
            raise LLMSegmentationError(contest_id) from e
        except Exception as e:
            logger.error(f"Unexpected error during editorial segmentation: {e}")
            raise LLMSegmentationError(contest_id) from e

    async def _ask_llm_for_segmentation(
        self,
        editorial_text: str,
        contest_id: str
    ) -> Dict[str, str]:
        """
        Ask LLM to segment editorial text into problem solutions.

        Args:
            editorial_text: Full editorial text content
            contest_id: Contest ID for context

        Returns:
            Dictionary mapping problem letters to solution texts
        """
        # Truncate text if too long (LLM token limits)
        max_chars = 40000  # Conservative limit
        if len(editorial_text) > max_chars:
            editorial_text = editorial_text[:max_chars] + "\n\n[CONTENT TRUNCATED DUE TO LENGTH]"
            logger.warning(f"Truncated editorial text for contest {contest_id} to {max_chars} chars")

        system_prompt = """You are an expert at analyzing Codeforces contest editorials.
Your task is to identify each individual problem's solution section and extract the complete analysis text for each one.

IMPORTANT:
- Identify problems by their letters (A, B, C, D, E, F, G, H, I, J, K, L, M, etc.)
- Extract the COMPLETE solution/analysis text for each problem
- Include mathematical notation, code snippets, and all technical details
- Do NOT include contest announcements, rating changes, tournament results, or participant lists
- Skip meta-information that's not part of specific problem solutions

The editorial may contain:
- Multiple problems in one cohesive text block
- Section headers like "Problem A", "A.", "Задача A" (Russian), etc.
- Implicit problem boundaries
- Multiple editorials combined together (separated by === EDITORIAL SOURCE ===)

Return JSON format ONLY:
{
  "A": "Complete solution text for problem A...",
  "B": "Complete solution text for problem B...",
  "C": "Complete solution text for problem C..."
}

Notes:
- Use uppercase letters A, B, C, etc. as keys
- Preserve all technical content (equations, algorithms, code)
- If a problem has no clear solution section, omit it from the result
- Empty sections should not be included
- Return valid JSON with no extra text or explanation"""

        user_prompt = f"""Contest ID: {contest_id}

Full editorial text:
{editorial_text}

Extract and segment the solution for each individual problem. Return JSON with problem letters as keys."""

        logger.debug(f"Sending LLM segmentation request for contest {contest_id}")

        response = await self.llm_client.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.0,  # Deterministic segmentation
            max_tokens=8000,  # Allow for detailed solutions
        )

        # Parse JSON response
        try:
            # Extract JSON from response - LLM might prepend explanatory text
            json_start = response.find('{')
            if json_start == -1:
                raise ValueError("No JSON object found in response")

            json_content = response[json_start:].strip()
            result = json.loads(json_content)

            # Validate format
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")

            # Clean up results
            clean_result = {}
            for key, value in result.items():
                if isinstance(value, str) and value.strip():
                    # Normalize problem ID (ensure uppercase, etc.)
                    problem_id = self._normalize_problem_id(key)
                    if problem_id:
                        clean_result[problem_id] = value.strip()

            logger.info(
                f"LLM segmented editorial for contest {contest_id} into {len(clean_result)} problems: {list(clean_result.keys())}"
            )

            return clean_result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM segmentation response: {e}")
            logger.debug(f"LLM response was: {response}")
            raise LLMSegmentationError(contest_id, response) from e

    def _normalize_problem_id(self, problem_id: str) -> Optional[str]:
        """
        Normalize problem ID to standard format (A, B, C, etc.).

        Args:
            problem_id: Raw problem identifier

        Returns:
            Normalized problem ID or None if invalid
        """
        if not problem_id or not isinstance(problem_id, str):
            return None

        # Extract first letter and convert to uppercase
        problem_id = problem_id.strip().upper()

        # Handle common patterns
        if len(problem_id) == 1 and problem_id.isalpha():
            return problem_id

        # Handle patterns like "A.", "Problem A", "Задача A"
        first_char = problem_id[0]
        if first_char.isalpha():
            return first_char

        return None