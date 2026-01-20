"""Parsers for extracting data from external sources."""

from .problem_page_parser import ProblemPageParser
from .url_parser import URLParser, URLParsingError
from .interfaces import (
    URLParserProtocol,
    ProblemPageParserProtocol,
    APIClientProtocol,
    HTTPClientProtocol,
    ParsingError,
)

__all__ = [
    "ProblemPageParser",
    "URLParser",
    "URLParsingError",
    "ParsingError",
    "URLParserProtocol",
    "ProblemPageParserProtocol",
    "APIClientProtocol",
    "HTTPClientProtocol",
]

__all__ = [
    "ProblemPageParser",
    "URLParser",
    "URLParserProtocol",
    "ProblemPageParserProtocol",
    "APIClientProtocol",
    "HTTPClientProtocol",
]
