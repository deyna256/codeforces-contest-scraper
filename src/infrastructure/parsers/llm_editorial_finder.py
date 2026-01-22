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

        logger.debug(f"Sending {len(links)} links to LLM for contest {contest_id}")

        system_prompt = """You are an expert at analyzing Codeforces contest pages.
Your task is to identify which link leads to the editorial/tutorial for the contest.

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
{"url": "the_editorial_url"} if found, or {"url": null} if no editorial link exists.

Do not include any explanation or additional text."""

        user_prompt = f"""Contest ID: {contest_id}

Available links:
{links_text}

Which link is the editorial/tutorial? Respond with JSON only."""

        logger.debug(f"LLM prompt for contest {contest_id}: {user_prompt}")

        try:
            response = await self.llm_client.complete(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.0,  # Deterministic
                max_tokens=100,  # Short response expected
            )

            logger.debug(f"LLM raw response for contest {contest_id}: {response}")

            # Parse JSON response
            result = json.loads(response)
            editorial_url = result.get("url")

            if editorial_url:
                logger.debug(f"LLM identified editorial URL: {editorial_url}")
                return [editorial_url]
            else:
                logger.debug("LLM did not find editorial URL")
                return []

        except json.JSONDecodeError as e:
            logger.debug(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error asking LLM for editorial: {e}")
            return None
