import pytest
from unittest.mock import MagicMock, patch
from domain.models import TutorialFormat

@pytest.mark.asyncio
async def test_parse_detects_html_content_type(parser, mock_http_client):
    """Test that HTML content-type routes to HTML parsing"""
    url = "https://codeforces.com/problemset/problem/1/A"
    mock_http_client.get_content_type.return_value = "text/html; charset=utf-8"
    mock_http_client.get_text.return_value = "<html><body>Tutorial</body></html>"

    result = await parser.parse(url)

    assert result.format == TutorialFormat.HTML
    mock_http_client.get_text.assert_called_once_with(url)
    mock_http_client.get_bytes.assert_not_called()


@pytest.mark.asyncio
async def test_parse_detects_pdf_content_type(parser, mock_http_client):
    """Test that PDF content-type routes to PDF parsing"""
    url = "https://codeforces.com/tutorials/123.pdf"
    mock_http_client.get_content_type.return_value = "application/pdf"
    mock_http_client.get_bytes.return_value = b"%PDF-1.4..."

    with patch("fitz.open") as mock_fitz:
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "PDF Content"
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.return_value = mock_doc

        result = await parser.parse(url)

        assert result.format == TutorialFormat.PDF
        mock_http_client.get_bytes.assert_called_once_with(url)
