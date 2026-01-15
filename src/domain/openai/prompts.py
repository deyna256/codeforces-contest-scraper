"""Prompts for OpenAI API interactions."""

from domain.models import ProblemIdentifier


def get_find_editorial_prompt(contest_html: str, problem: str) -> str:
    """
    Build a prompt that instructs OpenAI to locate an editorial link in contest HTML.
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
    Build a structured prompt that guides OpenAI to extract a specific problem’s
    editorial section from a tutorial.
    """
    problem_ref = f"Problem {identifier.problem}"
    if problem_title:
        problem_ref += f" ({problem_title})"

    return f"""Extract editorial for Problem {identifier.problem} from this Codeforces tutorial.

Find section marked as: {identifier.problem}. / {identifier.problem}) / Problem {identifier.problem} / {identifier.full_id} / Задача {identifier.problem}{f' / "{problem_title}"' if problem_title else ""}

Look for: headings, separators (---, ##), case-insensitive.

Format:
---
Problem: {identifier.problem}
Contest: {identifier.contest_id}
{f"title: {problem_title}" if problem_title else ""}
---

[Complete solution - preserve formatting, code blocks, formulas]

If not found: start with "NOT_FOUND" and list what problems you see.

Tutorial:
{tutorial_content[:150000]}"""


def get_parse_pdf_editorial_prompt(problem: str) -> str:
    """
    Build a prompt instructing OpenAI to extract a problem’s editorial from a PDF.
    """
    return f"""Extract editorial for Problem {problem} from this Codeforces PDF.

Find section for Problem {problem}. Preserve formatting, code, formulas. Include full solution."""


def get_alternative_search_prompt(page_html: str) -> str:
    """
    Build a prompt for finding possible editorial or solution links on a Codeforces page.
    """
    return f"""Find tutorial/editorial/solution links on this Codeforces page.

Return JSON list of URLs: ["url1", "url2", ...] or []

HTML:
{page_html[:50000]}
"""


def get_validate_editorial_prompt(content: str, problem: str) -> str:
    """
    Build a prompt that asks OpenAI to verify whether content contains an editorial
    for a specific problem.
    """
    return f"""Does this contain editorial for Problem {problem}?

Answer: YES / NO / PARTIAL

Content:
{content[:20000]}
"""
