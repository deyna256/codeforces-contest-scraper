"""LLM-based editorial URL finder for contest pages."""

import json
from typing import Optional

from bs4 import BeautifulSoup
from loguru import logger

from infrastructure.llm_client import LLMError, OpenRouterClient


class LLMEditorialFinder:
    """Uses LLM to intelligently find editorial URLs from contest pages."""

    def __init__(self, llm_client: Optional[OpenRouterClient] = None):
        """
        Initialize LLM editorial finder.

        Args:
            llm_client: OpenRouter client instance (None to disable LLM)
        """
        self.llm_client = llm_client

    async def find_editorial_url(self, soup: BeautifulSoup, contest_id: str) -> list[str]:
        """
        Find editorial URL using LLM.

        Args:
            soup: Parsed HTML of contest page
            contest_id: Contest ID

        Returns:
            List of editorial URLs if found, empty list otherwise
        """
        if not self.llm_client:
            logger.debug("LLM client not available, skipping LLM editorial detection")
            return []

        try:
            # Extract all links from the page
            links = self._extract_links(soup)

            if not links:
                logger.debug("No links found on contest page")
                return []

            # Use LLM to identify editorial link
            editorial_urls = await self._ask_llm_for_editorial(links, contest_id)
            return editorial_urls

        except LLMError as e:
            logger.debug(f"LLM editorial detection failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in LLM editorial detection: {e}")
            return []

    def _extract_links(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        """
        Extract all relevant links from the page.

        Returns:
            List of dicts with 'url' and 'text' keys
        """
        links = []
        seen_urls = set()

        # Focus on main content and sidebar areas
        search_areas = [
            soup.find("div", id="sidebar"),
            soup.find("div", class_="roundbox"),
            soup.find("div", class_="datatable"),
            soup,  # Fallback to entire page
        ]

        all_extracted_links = []

        for area in search_areas:
            if area is None:
                continue

            for link in area.find_all("a", href=True):
                href = link["href"]
                if not isinstance(href, str):
                    continue

                text = link.get_text(strip=True)
                all_extracted_links.append(
                    {
                        "href": href,
                        "text": text,
                        "potential": self._is_potentially_editorial_link(href),
                    }
                )

                # Skip non-blog links and common UI elements
                if not self._is_potentially_editorial_link(href):
                    continue

                # Deduplicate
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                if not text:
                    continue

                # Convert relative URLs to absolute
                if href.startswith("/"):
                    href = f"https://codeforces.com{href}"

                links.append({"url": href, "text": text})

        # Limit to first 20 most relevant links
        result = links[:20]
        return result

    def _is_potentially_editorial_link(self, href: str) -> bool:
        """Check if link could potentially be an editorial."""
        # Must contain blog/entry or certain keywords
        if "/blog/entry/" in href:
            return True

        # Skip common UI elements
        skip_patterns = [
            "/profile/",
            "/problemset/",
            "/contest/",
            "/gym/",
            "/standings/",
            "/submission/",
            "/register",
            "/settings",
            "javascript:",
            "#",
        ]

        return not any(pattern in href for pattern in skip_patterns)

    async def _ask_llm_for_editorial(
        self, links: list[dict[str, str]], contest_id: str
    ) -> list[str]:
        """
        Ask LLM to identify all editorial URLs from list of links.

        Args:
            links: List of link dicts with 'url' and 'text'
            contest_id: Contest ID for context

        Returns:
            List of all editorial URLs found (may be empty, or contain multiple URLs)
        """
        if not links or not self.llm_client:
            return []

        # Format links for LLM
        links_text = "\n".join(
            [f"{i + 1}. [{link['text']}] - {link['url']}" for i, link in enumerate(links)]
        )

        system_prompt = """You are an expert at analyzing Codeforces contest pages.
Your task is to identify ALL links that lead to editorials/tutorials for the contest.

IMPORTANT: Some contests may have multiple editorial links (e.g., different divisions, multiple parts, alternative solutions). You must return ALL editorial links found.

Editorial/Solution links typically:
- Have text like "Tutorial", "Editorial", "Analysis", "Solutions", "Разбор задач", "Разбор" (Russian for "analysis", "solutions")
- Do NOT have text like "Announcement", "Registration", "Rules", "Timetable", or other meta-contest information
- Point to /blog/entry/ URLs
- Are posted by contest authors or coordinators
- Are typically posted AFTER the contest ends (not as announcements before)

Common editorial patterns:
- "Tutorial", "Editorial", "Analysis", "Solutions"
- "Разбор задач", "Разбор", "Решения" (Russian)
- Task-specific editorials: "Tutorial for A+B+C" etc.

Common non-editorial patterns to AVOID:
- "Announcement", "Registration", "Rules", "Problems", "Results"
- "Цуцсивцив", "Объявление", "Регистрация" (Russian)

Respond ONLY with a JSON object in this format:
{"urls": ["url1", "url2", ...]} if found, or {"urls": []} if no editorial links exist.

Examples:
- Single editorial: {"urls": ["https://codeforces.com/blog/entry/12345"]}
- Multiple editorials: {"urls": ["https://codeforces.com/blog/entry/12345", "https://codeforces.com/blog/entry/12346"]}
- No editorial: {"urls": []}

Do not include any explanation or additional text."""

        user_prompt = f"""Contest ID: {contest_id}

Available links:
{links_text}

Which links are editorials/tutorials? Return ALL editorial links if multiple exist. Respond with JSON only."""

        logger.debug(
            f"Sending LLM request for contest {contest_id} with {len(links)} candidate links"
        )

        try:
            response = await self.llm_client.complete(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.0,  # Deterministic
                max_tokens=100,  # Short response expected
            )

            # Parse JSON response
            result = json.loads(response)

            # Support both new format {"urls": [...]} and old format {"url": "..."}
            editorial_urls = result.get("urls")
            if editorial_urls is None:
                # Fall back to old format for backward compatibility
                single_url = result.get("url")
                editorial_urls = [single_url] if single_url else []

            if editorial_urls:
                logger.info(
                    f"LLM identified {len(editorial_urls)} editorial URL(s) for contest {contest_id}: {editorial_urls}"
                )
                return editorial_urls
            else:
                logger.debug(f"LLM did not find editorial URLs for contest {contest_id}")
                return []

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse LLM response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error asking LLM for editorial: {e}")
            return []
