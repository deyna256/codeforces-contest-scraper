"""Shared HTML parsing utilities for Codeforces pages."""

from typing import Optional

from bs4 import BeautifulSoup


def extract_time_limit(soup: BeautifulSoup) -> Optional[str]:
    """Extract time limit from problem page."""
    try:
        problem_statement = soup.find("div", class_="problem-statement")
        if not problem_statement:
            return None

        header = problem_statement.find("div", class_="header")
        if not header:
            return None

        time_limit = header.find("div", class_="time-limit")
        if time_limit:
            # Extract just the value, e.g., "2 seconds" from "time limit per test2 seconds"
            text = time_limit.get_text(strip=True)
            # Remove the label part
            if "time limit per test" in text.lower():
                text = text.lower().replace("time limit per test", "").strip()
            return text

        return None
    except Exception:
        return None


def extract_memory_limit(soup: BeautifulSoup) -> Optional[str]:
    """Extract memory limit from problem page."""
    try:
        problem_statement = soup.find("div", class_="problem-statement")
        if not problem_statement:
            return None

        header = problem_statement.find("div", class_="header")
        if not header:
            return None

        memory_limit = header.find("div", class_="memory-limit")
        if memory_limit:
            # Extract just the value, e.g., "256 megabytes" from "memory limit per test256 megabytes"
            text = memory_limit.get_text(strip=True)
            # Remove the label part
            if "memory limit per test" in text.lower():
                text = text.lower().replace("memory limit per test", "").strip()
            return text

        return None
    except Exception:
        return None


def extract_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract problem statement/description (without time/memory limits)."""
    try:
        # Find the problem statement block
        problem_statement = soup.find("div", class_="problem-statement")
        if not problem_statement:
            return None

        # Extract all text from the problem statement, preserving structure
        # We'll get text from all divs within problem-statement except header
        text_parts = []

        # Get main sections: input, output, etc. (excluding header)
        for section_class in [
            "",
            "input-specification",
            "output-specification",
            "sample-tests",
            "note",
        ]:
            if section_class:
                section = problem_statement.find("div", class_=section_class)
            else:
                # Find the first non-header div (usually the problem description)
                all_divs = problem_statement.find_all("div", recursive=False)
                for div in all_divs:
                    if not div.get("class") or div.get("class") == [""]:
                        section = div
                        break
                else:
                    section = None

            if section:
                section_text = section.get_text(separator="\n", strip=True)
                if section_text:
                    text_parts.append(section_text)

        if text_parts:
            return "\n\n".join(text_parts)

        # Fallback: get all text from problem-statement
        return problem_statement.get_text(separator="\n", strip=True)

    except Exception:
        return None
