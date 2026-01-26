"""Custom exceptions for editorial parsing operations."""


class EditorialParserError(Exception):
    """Base exception for editorial parsing failures."""

    def __init__(self, message: str, contest_id: str | None = None):
        self.contest_id = contest_id
        super().__init__(f"{message}" + (f" for contest {contest_id}" if contest_id else ""))


class EditorialContentFetchError(EditorialParserError):
    """Failed to fetch editorial content from URL."""

    def __init__(self, url: str, contest_id: str | None = None):
        self.url = url
        super().__init__(f"Failed to fetch editorial content from {url}", contest_id)


class EditorialContentParseError(EditorialParserError):
    """Failed to parse HTML content into text."""

    def __init__(self, url: str, contest_id: str | None = None):
        self.url = url
        super().__init__(f"Failed to extract text content from {url}", contest_id)


class LLMSegmentationError(EditorialParserError):
    """LLM failed to properly segment editorial content."""

    def __init__(self, contest_id: str | None = None, llm_response: str | None = None):
        self.llm_response = llm_response
        super().__init__("LLM failed to segment editorial into problem solutions", contest_id)


class EditorialNotFoundError(EditorialParserError):
    """No editorial found for the contest."""

    def __init__(self, contest_id: str):
        super().__init__(f"No editorial found for contest {contest_id}", contest_id)
