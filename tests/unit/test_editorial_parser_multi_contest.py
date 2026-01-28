"""Unit tests for multi-contest editorial matching."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.infrastructure.parsers.editorial_content_parser import EditorialContentParser


class TestMultiContestMatching:
    """Test editorial parsing with multiple contests in one blog post."""

    @pytest.fixture
    def parser(self):
        """Create parser with mocked dependencies."""
        http_client = MagicMock()
        llm_client = AsyncMock()
        return EditorialContentParser(http_client, llm_client)

    def test_parse_new_format_with_contest_ids(self, parser):
        """Test parsing LLM response with new format including contest_ids."""
        llm_response = """{
            "problems": [
                {"contest_id": "1900", "problem_id": "A", "analysis": "Div1 A solution"},
                {"contest_id": "1901", "problem_id": "A", "analysis": "Div2 A solution"},
                {"contest_id": "1900", "problem_id": "B", "analysis": "Div1 B solution"}
            ]
        }"""

        result = parser._parse_llm_response(llm_response, "1900", None)

        assert len(result) == 3
        assert result[("1900", "A")] == "Div1 A solution"
        assert result[("1901", "A")] == "Div2 A solution"
        assert result[("1900", "B")] == "Div1 B solution"

    def test_parse_old_format_fallback(self, parser):
        """Test fallback to old format when LLM doesn't include contest_ids."""
        llm_response = """{
            "A": "Problem A solution",
            "B": "Problem B solution"
        }"""

        result = parser._parse_llm_response(llm_response, "1900", None)

        assert len(result) == 2
        assert result[(None, "A")] == "Problem A solution"
        assert result[(None, "B")] == "Problem B solution"

    def test_format_expected_problems(self, parser):
        """Test formatting of expected problems for LLM prompt."""
        expected = [("1900", "A"), ("1900", "B"), ("1900", "C")]
        formatted = parser._format_expected_problems(expected)

        assert "1900/A" in formatted
        assert "1900/B" in formatted
        assert "1900/C" in formatted

    def test_format_expected_problems_none(self, parser):
        """Test formatting when expected problems is None."""
        formatted = parser._format_expected_problems(None)
        assert "Unknown" in formatted

    def test_parse_new_format_with_invalid_entries(self, parser):
        """Test parsing new format with some invalid entries."""
        llm_response = """{
            "problems": [
                {"contest_id": "1900", "problem_id": "A", "analysis": "Valid entry"},
                {"contest_id": "", "problem_id": "B", "analysis": "Missing contest_id"},
                {"contest_id": "1900", "problem_id": "", "analysis": "Missing problem_id"},
                {"contest_id": "1900", "problem_id": "C", "analysis": ""}
            ]
        }"""

        result = parser._parse_llm_response(llm_response, "1900", None)

        # Only the valid entry should be included
        assert len(result) == 1
        assert result[("1900", "A")] == "Valid entry"

    def test_parse_old_format_normalizes_problem_ids(self, parser):
        """Test that old format parsing normalizes problem IDs."""
        llm_response = """{
            "a": "Problem a solution",
            "Problem B": "Problem B solution",
            "C.": "Problem C solution"
        }"""

        result = parser._parse_llm_response(llm_response, "1900", None)

        assert len(result) == 3
        assert result[(None, "A")] == "Problem a solution"
        assert result[(None, "B")] == "Problem B solution"
        assert result[(None, "C")] == "Problem C solution"
