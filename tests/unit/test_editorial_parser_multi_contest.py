import pytest
from unittest.mock import AsyncMock, MagicMock

from infrastructure.parsers.editorial_content_parser import EditorialContentParser


class TestMultiContestMatching:
    """Test editorial parsing with multiple contests in one blog post."""

    @pytest.fixture
    def parser(self):
        """Create parser with mocked dependencies."""
        http_client = MagicMock()
        llm_client = AsyncMock()
        return EditorialContentParser(http_client, llm_client)

    def test_parse_new_format_with_contest_ids(self, parser):
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
        llm_response = """{
            "A": "Problem A solution",
            "B": "Problem B solution"
        }"""

        result = parser._parse_llm_response(llm_response, "1900", None)

        assert len(result) == 2
        assert result[(None, "A")] == "Problem A solution"
        assert result[(None, "B")] == "Problem B solution"

    def test_format_expected_problems(self, parser):
        expected = [("1900", "A"), ("1900", "B"), ("1900", "C")]
        formatted = parser._format_expected_problems(expected)

        assert "1900/A" in formatted
        assert "1900/B" in formatted
        assert "1900/C" in formatted

    def test_format_expected_problems_none(self, parser):
        formatted = parser._format_expected_problems(None)
        assert "Unknown" in formatted

    def test_parse_new_format_with_invalid_entries(self, parser):
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

    def test_sanitize_json_with_latex_formulas(self, parser):
        """Test that LaTeX formulas are preserved when using marker-based extraction."""
        # New approach: LLM returns markers, we extract text ourselves
        # Using raw string to preserve backslashes in LaTeX formulas
        editorial_text = r"""
        Problem 2189A - Test Problem

        For $$h \leq l$$, the solution is $$cnt_h \times cnt_l$$

        Problem 2189B - Next Problem
        """

        # LLM response with markers (no full text with LaTeX in JSON)
        llm_response = """{
            "problems": [
                {
                    "contest_id": "2189",
                    "problem_id": "A",
                    "start_marker": "Problem 2189A",
                    "end_marker": "Problem 2189B"
                }
            ]
        }"""

        result = parser._parse_llm_response(llm_response, "2189", None, editorial_text)

        assert len(result) == 1
        assert ("2189", "A") in result
        # The LaTeX should be preserved exactly as in original text
        assert r"\leq" in result[("2189", "A")]
        assert r"\times" in result[("2189", "A")]

    def test_sanitize_json_preserves_valid_escapes(self, parser):
        """Test that valid JSON escape sequences are preserved."""
        # This has properly escaped JSON - should work without sanitization
        raw_json = r"""{
            "problems": [
                {
                    "contest_id": "1900",
                    "problem_id": "A",
                    "analysis": "Line 1\nLine 2\tTabbed\\Backslash\"Quote"
                }
            ]
        }"""

        result = parser._parse_llm_response(raw_json, "1900", None)

        assert len(result) == 1
        analysis = result[("1900", "A")]
        # Valid escapes should work correctly
        assert "\n" in analysis  # newline
        assert "\t" in analysis  # tab
        assert "\\" in analysis  # backslash
        assert '"' in analysis   # quote

    def test_real_world_latex_error_from_logs(self, parser):
        """Test the exact error scenario from the production logs."""
        # This is based on the actual error from the logs:
        # "For any cell of the table $$(x, y)$$, $$1 \leq x \leq h$$"
        raw_json = r"""{
            "problems": [
                {
                    "contest_id": "2189",
                    "problem_id": "A",
                    "analysis": "Note that maximizing the sum is equivalent to maximizing the number of chosen pairs. Without loss of generality, we assume that $$h \leq l$$. For any cell of the table $$(x, y)$$, $$1 \leq x \leq h$$, $$1 \leq y \leq l$$. Let $$cnt_h$$ be the number of elements in the array not exceeding $$h$$, and $$cnt_l$$ be the number of elements not exceeding $$l$$."
                }
            ]
        }"""

        result = parser._parse_llm_response(raw_json, "2189", None)

        assert len(result) == 1
        assert ("2189", "A") in result
        analysis = result[("2189", "A")]
        # Verify LaTeX expressions are preserved
        assert r"\leq" in analysis
        assert "$$h" in analysis
        assert "$$cnt_h$$" in analysis
