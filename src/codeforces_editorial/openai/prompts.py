"""Prompts for OpenAI API interactions."""

from codeforces_editorial.models import ProblemIdentifier


def get_find_editorial_prompt(contest_html: str, problem_id: str) -> str:
    """
    Get prompt for finding editorial link in contest page HTML.

    Args:
        contest_html: HTML content of contest page
        problem_id: Problem ID to find editorial for

    Returns:
        Prompt string
    """
    return f"""Find the editorial/tutorial/разбор link for this Codeforces contest.

Look for: Tutorial, Editorial, Разбор, Solutions, Analysis (usually in blog post or "Contest materials").

Return ONLY the full URL (http:// or https://), or "NOT_FOUND".

HTML:
{contest_html[:50000]}
"""


def get_extract_solution_prompt(
    tutorial_content: str,
    identifier: ProblemIdentifier,
    problem_title: str = "",
) -> str:
    """
    Get prompt for extracting solution for specific problem from tutorial.

    Args:
        tutorial_content: Tutorial content (HTML or text)
        identifier: Problem identifier
        problem_title: Optional problem title for better matching

    Returns:
        Prompt string
    """
    problem_ref = f"Problem {identifier.problem_id}"
    if problem_title:
        problem_ref += f" ({problem_title})"

    return f"""Extract editorial for Problem {identifier.problem_id} from this Codeforces tutorial.

Find section marked as: {identifier.problem_id}. / {identifier.problem_id}) / Problem {identifier.problem_id} / {identifier.full_id} / Задача {identifier.problem_id}{f' / "{problem_title}"' if problem_title else ""}

Look for: headings, separators (---, ##), case-insensitive.

Format:
---
Problem: {identifier.problem_id}
Contest: {identifier.contest_id}
{f"Title: {problem_title}" if problem_title else ""}
---

[Complete solution - preserve formatting, code blocks, formulas]

If not found: start with "NOT_FOUND" and list what problems you see.

Tutorial:
{tutorial_content[:150000]}"""


def get_parse_pdf_editorial_prompt(problem_id: str) -> str:
    """
    Get prompt for analyzing PDF editorial.

    Args:
        problem_id: Problem ID

    Returns:
        Prompt string
    """
    return f"""Extract editorial for Problem {problem_id} from this Codeforces PDF.

Find section for Problem {problem_id}. Preserve formatting, code, formulas. Include full solution."""


def get_alternative_search_prompt(page_html: str) -> str:
    """
    Get prompt for alternative editorial search strategies.

    Args:
        page_html: HTML to search

    Returns:
        Prompt string
    """
    return f"""Find tutorial/editorial/solution links on this Codeforces page.

Return JSON list of URLs: ["url1", "url2", ...] or []

HTML:
{page_html[:50000]}
"""


def get_validate_editorial_prompt(content: str, problem_id: str) -> str:
    """
    Get prompt to validate if content contains editorial for specific problem.

    Args:
        content: Content to validate
        problem_id: Problem ID

    Returns:
        Prompt string
    """
    return f"""Does this contain editorial for Problem {problem_id}?

Answer: YES / NO / PARTIAL

Content:
{content[:20000]}
"""
