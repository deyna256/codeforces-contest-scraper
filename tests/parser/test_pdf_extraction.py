import pytest
from unittest.mock import MagicMock, patch
from domain.models import TutorialFormat

@pytest.mark.asyncio
async def test_pdf_extraction_success(parser, mock_http_client):
    """Test successful PDF text extraction via fitz"""
    url = "https://codeforces.com/editorial.pdf"
    mock_http_client.get_content_type.return_value = "application/pdf"
    mock_http_client.get_bytes.return_value = b"%PDF..."

    with patch("fitz.open") as mock_fitz:
        mock_doc = MagicMock()
        page1 = MagicMock()
        page1.get_text.return_value = "Page 1 Content"
        page2 = MagicMock()
        page2.get_text.return_value = "Page 2 Content"

        mock_doc.__iter__.return_value = [page1, page2]
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_fitz.return_value = mock_doc

        result = await parser.parse(url)

        assert result.format == TutorialFormat.PDF
        assert "Page 1 Content" in result.content
        assert "Page 2 Content" in result.content
        mock_fitz.assert_called_once_with(
            stream=mock_http_client.get_bytes.return_value, filetype="pdf"
        )
