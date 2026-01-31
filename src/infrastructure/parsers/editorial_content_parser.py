"""LLM-powered parser for editorial blog entries to extract problem-specific solutions."""

import json
import re
from typing import Dict, List, Optional

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
        llm_client: Optional[OpenRouterClient] = None,
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
        editorial_urls: List[str],
        expected_problems: List[tuple[str, str]] | None = None,
    ) -> ContestEditorial:
        """
        Parse editorial content and segment into individual problem solutions.

        Args:
            contest_id: Contest identifier
            editorial_urls: List of editorial blog entry URLs
            expected_problems: Optional list of (contest_id, problem_letter) tuples for context

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
                f"All editorial URLs failed to load: {failed_urls}", contest_id
            )

        # Combine all editorial content
        combined_content = await self._combine_editorial_content(all_content)

        # Use LLM to segment into problem-specific solutions
        problem_solutions = await self._segment_by_problems(
            combined_content, contest_id, expected_problems
        )

        # Convert to domain objects
        editorials = [
            Editorial(contest_id=cid, problem_id=pid, analysis_text=text)
            for (cid, pid), text in problem_solutions.items()
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
        Extract main content from Codeforces blog entry with smart HTML cleanup.

        This removes all unnecessary elements (comments, UI, navigation) before
        extracting text, ensuring LLM gets only editorial content.

        Args:
            soup: Parsed HTML content

        Returns:
            Cleaned editorial text content with preserved structure
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
                # Clean HTML before extracting text
                cleaned_element = self._clean_html_content(content_element)
                text = self._extract_text_with_structure(cleaned_element)

                if len(text.strip()) > 200:  # Minimum viable content length
                    return text

        # Fallback: search for any large text block
        body = soup.find("body")
        if body:
            cleaned_body = self._clean_html_content(body)
            text = self._extract_text_with_structure(cleaned_body)
            return text

        return ""

    def _clean_html_content(self, element) -> BeautifulSoup:
        """
        Remove unnecessary HTML elements from parsed content.

        Removes:
        - Comments section
        - User avatars and profiles
        - Vote buttons and controls
        - Navigation elements
        - Advertisements
        - Scripts and styles

        Args:
            element: BeautifulSoup element to clean

        Returns:
            Cleaned BeautifulSoup element
        """
        # Make a copy to avoid modifying original
        from copy import deepcopy

        cleaned = deepcopy(element)

        # Remove comment sections and user-generated content
        unwanted_selectors = [
            ".comments",  # Comments section
            ".comment",  # Individual comments
            "#comments",
            ".comment-table",
            ".userbox",  # User profile boxes
            ".avatar",  # User avatars
            ".roundbox.menu-box",  # Navigation menus
            ".menu",
            ".sidebar",
            ".footer",
            ".header",
            ".voted-count",  # Vote buttons
            ".vote-controls",
            ".community-menu",
            ".lang-chooser",
            "script",  # Scripts
            "style",  # Inline styles
            "noscript",
            ".signature",  # User signatures
            "form",  # Forms (login, search, etc.)
            "input",
            "button",
            ".share-buttons",  # Social media buttons
            ".advertisement",
            ".ad",
            "[id^='google_ads']",  # Google ads
            "iframe",  # Embedded content
        ]

        for selector in unwanted_selectors:
            for elem in cleaned.select(selector):
                elem.decompose()

        return cleaned

    def _extract_text_with_structure(self, element) -> str:
        """
        Extract text while preserving document structure using markdown-like format.

        This helps LLM understand the document hierarchy:
        - Preserves headings (H1, H2, H3)
        - Separates paragraphs
        - Keeps code blocks identifiable

        Args:
            element: Cleaned BeautifulSoup element

        Returns:
            Structured text content
        """
        lines = []

        # Process all child elements to preserve structure
        for child in element.descendants:
            # Skip navigable strings that are only whitespace
            if isinstance(child, str):
                text = child.strip()
                if text and not text.isspace():
                    # Only add if not already added (avoid duplicates)
                    if not lines or lines[-1] != text:
                        lines.append(text)
                continue

            # Handle headings
            if child.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                level = int(child.name[1])
                heading_text = child.get_text(strip=True)
                if heading_text:
                    # Add markdown-style heading
                    lines.append("\n" + "#" * level + " " + heading_text + "\n")

            # Handle code blocks
            elif child.name == "pre":
                code_text = child.get_text(strip=True)
                if code_text:
                    lines.append("\n```\n" + code_text + "\n```\n")

            # Handle paragraphs
            elif child.name == "p":
                para_text = child.get_text(strip=True)
                if para_text:
                    lines.append("\n" + para_text + "\n")

        # Join and clean
        text = "\n".join(lines)
        return self._clean_extracted_text(text)

    def _clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted text content.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

        # Remove common UI elements and garbage text
        remove_patterns = [
            r"Material\s+You\s+Should\s+Know.*?(?=\n|\Z)",  # Common header
            r"Problem\s+tags\s*:.*?(?=\n|\Z)",  # Tags section
            r"Download\s+as\s+.*?(?=\n|\Z)",  # Download links
            r"Submit\s+a\s+ticket.*?(?=\n|\Z)",  # Support links
            r"Related\s+topics.*?(?=\n|\Z)",  # Related topics
        ]

        for pattern in remove_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)

        # Normalize spacing
        text = re.sub(r"[ \t]+", " ", text)  # Multiple spaces to single space
        text = re.sub(r"\n\s+", "\n", text)  # Space after newline to just newline

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
        self, full_text: str, contest_id: str, expected_problems: List[tuple[str, str]] | None
    ) -> Dict[tuple[str, str], str]:
        """
        Use LLM to segment editorial text into problem-specific solutions.

        Args:
            full_text: Combined editorial text content
            contest_id: Contest identifier for context
            expected_problems: Optional list of (contest_id, problem_letter) tuples

        Returns:
            Dictionary mapping (contest_id, problem_letter) tuples to solution text

        Raises:
            LLMSegmentationError: If LLM fails to segment properly
        """
        if not self.llm_client:
            raise LLMSegmentationError(contest_id, "No LLM client available")

        if not full_text or len(full_text.strip()) < 50:
            raise LLMSegmentationError(contest_id, "Content too short for segmentation")

        try:
            result = await self._ask_llm_for_segmentation(full_text, contest_id, expected_problems)

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
        self, editorial_text: str, contest_id: str, expected_problems: List[tuple[str, str]] | None
    ) -> Dict[tuple[str, str], str]:
        """
        Ask LLM to segment editorial text into problem solutions.

        Args:
            editorial_text: Full editorial text content
            contest_id: Contest ID for context
            expected_problems: Optional list of (contest_id, problem_letter) tuples

        Returns:
            Dictionary mapping (contest_id, problem_letter) tuples to solution texts
        """
        assert self.llm_client is not None, "LLM client must be initialized"

        # Truncate text if too long (LLM token limits)
        # Claude 3.5 Haiku has 200k token context (~600k-800k chars)
        # We only ask for markers (not full text), so we can handle large editorials
        max_chars = 300000  # ~75k tokens - safe for most editorials
        if len(editorial_text) > max_chars:
            editorial_text = editorial_text[:max_chars] + "\n\n[CONTENT TRUNCATED DUE TO LENGTH]"
            logger.warning(
                f"Truncated editorial text for contest {contest_id} to {max_chars} chars"
            )

        system_prompt = r"""You are an expert at analyzing Codeforces contest editorials.
Your task is to identify where each problem's solution starts and ends in the editorial text.

CRITICAL INSTRUCTIONS:
1. Editorials often cover MULTIPLE contests (e.g., Div1 + Div2) in ONE blog post.
   You MUST identify the contest ID for each problem to avoid confusion.

2. DO NOT extract or copy the full text - only identify boundaries!
   For each problem, find:
   - A unique text marker that indicates where the problem's solution STARTS
   - A unique text marker that indicates where the problem's solution ENDS

   These markers should be actual text from the editorial (e.g., "Problem A", "2189A", "Solution for A", etc.)

3. Return ONLY metadata about problem locations, not the full text content.

Return this JSON format:
{
  "problems": [
    {
      "contest_id": "1900",
      "problem_id": "A",
      "start_marker": "Problem A",
      "end_marker": "Problem B"
    },
    {
      "contest_id": "1900",
      "problem_id": "B",
      "start_marker": "Problem B",
      "end_marker": "Problem C"
    }
  ]
}

Guidelines:
- Look for contest IDs in: problem headers (e.g., "1900A"), section titles, blog text
- Use uppercase letters for problem_id (A, B, C, etc.)
- contest_id should be numeric string (e.g., "1900", "1901")
- start_marker and end_marker should be unique text snippets (10-50 characters) that appear in the editorial
- For the last problem, end_marker can be empty string "" if no clear ending
- If contest ID is ambiguous, infer from context or use the primary contest ID
- Return valid JSON only, no extra text"""

        user_prompt = f"""Contest ID: {contest_id}

Expected problems: {self._format_expected_problems(expected_problems)}

Full editorial text:
{editorial_text}

IMPORTANT: Identify the START and END markers for each problem's solution.
Find unique text snippets that mark where each problem begins and ends.
Do NOT copy the full text - only return the boundary markers.

Return JSON with contest_id, problem_id, start_marker, and end_marker for each problem."""

        logger.debug(f"Sending LLM segmentation request for contest {contest_id}")

        response = await self.llm_client.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.0,  # Deterministic segmentation
            max_tokens=4000,  # Reduced - we only need markers, not full text
        )

        # Parse response with fallback, passing original text for extraction
        return self._parse_llm_response(response, contest_id, expected_problems, editorial_text)

    def _normalize_problem_id(self, problem_id: str) -> Optional[str]:
        """
        Normalize problem ID to standard format (A, B, C, C1, C2, D1, D2, etc.).

        Args:
            problem_id: Raw problem identifier

        Returns:
            Normalized problem ID or None if invalid
        """
        if not problem_id or not isinstance(problem_id, str):
            return None

        # Extract and convert to uppercase
        problem_id = problem_id.strip().upper()

        # Handle single letter (A, B, C, etc.)
        if len(problem_id) == 1 and problem_id.isalpha():
            return problem_id

        # Handle patterns like "Problem A", "Задача A" - extract the last part
        if problem_id.startswith("PROBLEM ") or problem_id.startswith("ЗАДАЧА "):
            parts = problem_id.split()
            if len(parts) >= 2:
                last_part = parts[-1]
                # Check if it's letter + optional digit (A, C1, D2)
                if len(last_part) <= 2 and last_part[0].isalpha():
                    return last_part

        # Handle patterns like "C1", "C2", "D1", "D2" (letter + digit)
        if len(problem_id) == 2 and problem_id[0].isalpha() and problem_id[1].isdigit():
            return problem_id

        # Handle patterns like "1900A", "1900C1" - extract letter part from end
        # Find where letters start from the end
        if problem_id and problem_id[-1].isalpha():
            # Extract trailing letter (possibly with digit before it)
            for i in range(len(problem_id) - 1, -1, -1):
                if not (problem_id[i].isalpha() or problem_id[i].isdigit()):
                    # Found non-alphanumeric, take everything after it
                    result = problem_id[i + 1 :]
                    if result and result[0].isalpha():
                        return result
                    break
            else:
                # All alphanumeric, find first letter
                for i, char in enumerate(problem_id):
                    if char.isalpha():
                        return problem_id[i:]

        # Handle patterns where first character is the letter (fallback)
        if problem_id[0].isalpha():
            # Extract letter and following digits if any
            result = problem_id[0]
            if len(problem_id) > 1 and problem_id[1].isdigit():
                result += problem_id[1]
            return result

        return None

    def _format_expected_problems(self, expected_problems: List[tuple[str, str]] | None) -> str:
        """Format expected problems list for LLM prompt."""
        if not expected_problems:
            return "Unknown (parse all problems found)"

        formatted = ", ".join([f"{cid}/{pid}" for cid, pid in expected_problems])
        return f"{formatted}"

    def _attempt_json_repair(self, json_str: str) -> str | None:
        """
        Attempt to repair common JSON structural issues.

        Args:
            json_str: Potentially broken JSON string

        Returns:
            Repaired JSON string if successful, None otherwise
        """
        try:
            # Common repair: truncated response - try to close unclosed structures
            repaired = json_str.strip()

            # Count braces and brackets to detect truncation
            open_braces = repaired.count("{") - repaired.count("}")
            open_brackets = repaired.count("[") - repaired.count("]")

            # Check if we're inside a string by counting quotes
            quote_count = 0
            escaped = False
            for char in repaired:
                if char == "\\" and not escaped:
                    escaped = True
                    continue
                if char == '"' and not escaped:
                    quote_count += 1
                escaped = False

            # If odd number of quotes, we have an unclosed string
            if quote_count % 2 == 1:
                # Try to close the string
                repaired += '"'

            # Remove trailing comma before closing brace/bracket (common LLM error)
            repaired = repaired.rstrip()
            if repaired.endswith(","):
                repaired = repaired[:-1].rstrip()

            # Close any unclosed arrays
            repaired += "]" * open_brackets

            # Close any unclosed objects
            repaired += "}" * open_braces

            # Try to parse the repaired JSON
            json.loads(repaired)
            return repaired

        except (json.JSONDecodeError, Exception):
            return None

    def _sanitize_json_string(self, json_str: str) -> str:
        r"""
        Sanitize JSON string by fixing common issues with escape sequences.

        This specifically handles LaTeX formulas and other backslashes that aren't
        properly escaped by the LLM. The strategy is to escape all single backslashes
        inside string values (converting \ to \\), while preserving already-escaped
        backslashes (\\).

        Args:
            json_str: Raw JSON string from LLM

        Returns:
            Sanitized JSON string ready for parsing
        """
        # First, try to parse as-is - if it works, no sanitization needed
        try:
            json.loads(json_str)
            return json_str  # Already valid JSON
        except json.JSONDecodeError:
            pass  # Need to sanitize

        result = []
        i = 0
        in_string = False

        while i < len(json_str):
            char = json_str[i]

            # Track when we're inside a string value (simple heuristic)
            if char == '"':
                # Check if this quote is escaped by looking at preceding backslashes
                num_backslashes = 0
                j = i - 1
                while j >= 0 and json_str[j] == "\\":
                    num_backslashes += 1
                    j -= 1

                # If even number of backslashes (including 0), quote is not escaped
                if num_backslashes % 2 == 0:
                    in_string = not in_string

                result.append(char)
                i += 1
                continue

            # Inside string values, handle special characters
            if in_string:
                if char == "\\":
                    # Check if this backslash is already escaped (preceded by another backslash)
                    # We need to check if we just added a backslash to result
                    if i + 1 < len(json_str) and json_str[i + 1] == "\\":
                        # This is \\, keep both backslashes as-is (already escaped)
                        result.append("\\")
                        result.append("\\")
                        i += 2  # Skip both backslashes
                    elif i + 1 < len(json_str) and json_str[i + 1] in (
                        '"',
                        "n",
                        "t",
                        "r",
                        "b",
                        "f",
                        "/",
                    ):
                        # Valid escape sequence - keep as is
                        result.append("\\")
                        result.append(json_str[i + 1])
                        i += 2
                    else:
                        # Single backslash - escape it
                        result.append("\\\\")
                        i += 1
                # Handle control characters that should be escaped
                elif char == "\n":
                    result.append("\\n")
                    i += 1
                elif char == "\t":
                    result.append("\\t")
                    i += 1
                elif char == "\r":
                    result.append("\\r")
                    i += 1
                elif char == "\b":
                    result.append("\\b")
                    i += 1
                elif char == "\f":
                    result.append("\\f")
                    i += 1
                else:
                    result.append(char)
                    i += 1
            else:
                result.append(char)
                i += 1

        return "".join(result)

    def _parse_llm_response(
        self,
        response: str,
        primary_contest_id: str,
        expected_problems: List[tuple[str, str]] | None,
        editorial_text: str | None = None,
    ) -> Dict[tuple[str, str], str]:
        """
        Parse LLM response with format detection and fallback.

        Args:
            response: LLM response containing problem boundaries
            primary_contest_id: Primary contest ID
            expected_problems: Expected problems list
            editorial_text: Original editorial text for extraction

        Returns:
            Dict mapping (contest_id, problem_letter) -> analysis_text
        """
        try:
            # Try to extract JSON from markdown code blocks first
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                if json_end != -1:
                    json_content = response[json_start:json_end].strip()
                    # Sanitize before parsing
                    json_content = self._sanitize_json_string(json_content)
                    result = json.loads(json_content)
                    logger.debug("Extracted JSON from markdown code block")
                    return self._process_parsed_json(result, primary_contest_id, editorial_text)

            # Try to find JSON object boundaries
            json_start = response.find("{")
            if json_start == -1:
                raise ValueError("No JSON found in response")

            # Find matching closing brace
            json_end = self._find_matching_brace(response, json_start)
            if json_end == -1:
                # Fallback to taking everything after {
                json_content = response[json_start:].strip()
            else:
                json_content = response[json_start : json_end + 1].strip()

            # Sanitize before parsing
            json_content = self._sanitize_json_string(json_content)

            # Try to parse
            try:
                result = json.loads(json_content)
                return self._process_parsed_json(result, primary_contest_id, editorial_text)
            except json.JSONDecodeError as parse_error:
                # Attempt to repair truncated JSON (missing closing braces)
                logger.debug(f"Initial parse failed: {parse_error}, attempting repair...")
                repaired = self._attempt_json_repair(json_content)
                if repaired:
                    result = json.loads(repaired)
                    logger.warning(
                        f"Successfully parsed repaired JSON for contest {primary_contest_id}"
                    )
                    return self._process_parsed_json(result, primary_contest_id, editorial_text)
                raise  # Re-raise if repair didn't work

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.debug(f"Response preview (first 500 chars): {response[:500]}")

            # Save the problematic response for debugging
            try:
                import re
                from pathlib import Path

                # Sanitize contest_id to prevent path traversal
                safe_contest_id = re.sub(r"[^a-zA-Z0-9_-]", "_", primary_contest_id)

                debug_dir = Path.home() / ".cache" / "codeforces-editorial"
                debug_dir.mkdir(parents=True, exist_ok=True)
                debug_file = debug_dir / f"failed_llm_response_{safe_contest_id}.txt"

                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write("=== Original Response ===\n")
                    f.write(response)
                    f.write("\n\n=== Attempted JSON Content ===\n")
                    f.write(json_content if "json_content" in locals() else "N/A")

                logger.debug(f"Saved problematic LLM response to: {debug_file}")
            except Exception as debug_error:
                logger.debug(f"Could not save debug file: {debug_error}")

            raise LLMSegmentationError(primary_contest_id, response) from e

    def _find_matching_brace(self, text: str, start: int) -> int:
        """Find the matching closing brace for an opening brace at start position."""
        count = 0
        in_string = False
        escape = False

        for i in range(start, len(text)):
            char = text[i]

            # Handle string escaping
            if escape:
                escape = False
                continue
            if char == "\\":
                escape = True
                continue

            # Handle string delimiters
            if char == '"' and not escape:
                in_string = not in_string
                continue

            # Count braces outside strings
            if not in_string:
                if char == "{":
                    count += 1
                elif char == "}":
                    count -= 1
                    if count == 0:
                        return i

        return -1

    def _process_parsed_json(
        self, result: dict, primary_contest_id: str, editorial_text: str | None = None
    ) -> Dict[tuple[str, str], str]:
        """Process parsed JSON result and return formatted dict."""
        # Try new format first
        if "problems" in result and isinstance(result["problems"], list):
            return self._parse_new_format(result["problems"], editorial_text)

        # Fallback to old format
        logger.warning("LLM returned old format (no contest_id), using fallback")
        return self._parse_old_format(result, primary_contest_id)

    def _extract_text_between_markers(self, text: str, start_marker: str, end_marker: str) -> str:
        """
        Extract text between start and end markers.

        Args:
            text: Full editorial text
            start_marker: Text marker indicating start of section
            end_marker: Text marker indicating end of section (empty string = until end)

        Returns:
            Extracted text between markers, or empty string if markers not found
        """
        # Find start position
        start_pos = text.find(start_marker)
        if start_pos == -1:
            logger.warning(f"Start marker not found: {start_marker[:50]}...")
            return ""

        # Start after the marker
        start_pos += len(start_marker)

        # Find end position
        if end_marker:
            end_pos = text.find(end_marker, start_pos)
            if end_pos == -1:
                # End marker not found - take until end of text
                logger.debug(f"End marker not found, taking text until end: {end_marker[:50]}...")
                extracted = text[start_pos:].strip()
            else:
                extracted = text[start_pos:end_pos].strip()
        else:
            # No end marker - take until end of text
            extracted = text[start_pos:].strip()

        return extracted

    def _parse_new_format(
        self, problems: list, editorial_text: str | None = None
    ) -> Dict[tuple[str, str], str]:
        """
        Parse new format with markers and extract text.

        New format: [{"contest_id": "1900", "problem_id": "A", "start_marker": "...", "end_marker": "..."}]
        Old format (fallback): [{"contest_id": "1900", "problem_id": "A", "analysis": "..."}]
        """
        clean_result = {}
        for item in problems:
            if not isinstance(item, dict):
                continue

            contest_id = str(item.get("contest_id", "")).strip()
            problem_id = self._normalize_problem_id(item.get("problem_id", ""))

            # Check if this is new marker-based format
            if "start_marker" in item and editorial_text:
                start_marker = item.get("start_marker", "").strip()
                end_marker = item.get("end_marker", "").strip()

                if contest_id and problem_id and start_marker:
                    # Extract text between markers
                    analysis = self._extract_text_between_markers(
                        editorial_text, start_marker, end_marker
                    )
                    if analysis:
                        key = (contest_id, problem_id)
                        clean_result[key] = analysis
            else:
                # Old format fallback - analysis text is directly in JSON
                analysis = item.get("analysis", "").strip()
                if contest_id and problem_id and analysis:
                    key = (contest_id, problem_id)
                    clean_result[key] = analysis

        logger.info(f"Parsed {len(clean_result)} editorials with contest IDs")
        return clean_result

    def _parse_old_format(
        self, result: dict, primary_contest_id: str
    ) -> Dict[tuple[str, str], str]:
        """Parse old format: {"A": "...", "B": "..."}"""
        clean_result = {}
        for key, value in result.items():
            if isinstance(value, str) and value.strip():
                problem_id = self._normalize_problem_id(key)
                if problem_id:
                    # Use None for contest_id to signal fallback matching
                    clean_result[(None, problem_id)] = value.strip()

        logger.warning(f"Parsed {len(clean_result)} editorials without contest IDs (old format)")
        return clean_result
