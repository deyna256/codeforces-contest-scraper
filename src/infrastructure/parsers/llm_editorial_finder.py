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

    async def find_editorial_url(self, soup: BeautifulSoup, contest_id: str) -> Optional[str]:
        """
        Find editorial URL using LLM.

        Args:
            soup: Parsed HTML of contest page
            contest_id: Contest ID

        Returns:
            Editorial URL if found, None otherwise
        """
        if not self.llm_client:
            logger.debug("LLM client not available, skipping LLM editorial detection")
            return None

        try:
            # Extract all links from the page
            links = self._extract_links(soup)

            if not links:
                logger.debug("No links found on contest page")
                return None

            # Use LLM to identify editorial link
            editorial_url = await self._ask_llm_for_editorial(links, contest_id)
            return editorial_url

        except LLMError as e:
            logger.debug(f"LLM editorial detection failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in LLM editorial detection: {e}")
            return None

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

        for area in search_areas:
            if area is None:
                continue

            for link in area.find_all("a", href=True):
                href = link["href"]
                if not isinstance(href, str):
                    continue

                # Skip non-blog links and common UI elements
                if not self._is_potentially_editorial_link(href):
                    continue

                # Deduplicate
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                text = link.get_text(strip=True)
                if not text:
                    continue

                # Convert relative URLs to absolute
                if href.startswith("/"):
                    href = f"https://codeforces.com{href}"

                links.append({"url": href, "text": text})

        # Limit to first 20 most relevant links
        return links[:20]

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
    ) -> Optional[str]:
        """
        Ask LLM to identify editorial URL from list of links.

        Args:
            links: List of link dicts with 'url' and 'text'
            contest_id: Contest ID for context

        Returns:
            Editorial URL if found, None otherwise
        """
        if not links or not self.llm_client:
            return None

        # Format links for LLM
        links_text = "\n".join(
            [f"{i + 1}. [{link['text']}] - {link['url']}" for i, link in enumerate(links)]
        )

        system_prompt = """You are an expert at analyzing Codeforces contest pages.
Your task is to identify which link leads to the editorial/tutorial for the contest.

Editorial links typically:
- Have text like "Tutorial", "Editorial", "Analysis", "Разбор задач" (Russian for "Problem analysis")
- Point to /blog/entry/ URLs
- Are posted by contest authors or coordinators

Respond ONLY with a JSON object in this format:
{"url": "the_editorial_url"} if found, or {"url": null} if no editorial link exists.

Do not include any explanation or additional text."""

        user_prompt = f"""Contest ID: {contest_id}

Available links:
{links_text}

Which link is the editorial/tutorial? Respond with JSON only."""

        try:
            response = await self.llm_client.complete(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.0,  # Deterministic
                max_tokens=100,  # Short response expected
            )

            # Parse JSON response
            result = json.loads(response)
            editorial_url = result.get("url")

            if editorial_url:
                logger.debug(f"LLM identified editorial URL: {editorial_url}")
                return editorial_url
            else:
                logger.debug("LLM did not find editorial URL")
                return None

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error asking LLM for editorial: {e}")
            return None
