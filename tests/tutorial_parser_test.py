import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from bs4 import BeautifulSoup

from domain.parsers.tutorial_parser import TutorialParser
from domain.models import TutorialFormat, Language, TutorialData
from domain.exceptions import ParsingError


@pytest.mark.asyncio
class TestTutorialParser:
    """Test suite for TutorialParser class"""

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client"""
        client = Mock()
        # Setup async methods
        client.get_content_type = AsyncMock()
        client.get_text = AsyncMock()
        client.get_text_with_js = AsyncMock()
        client.get_bytes = AsyncMock()
        return client

    @pytest.fixture
    def parser(self, mock_http_client):
        """Create a TutorialParser instance with mock dependencies"""
        return TutorialParser(http_client=mock_http_client)

    # ==================== Format Routing Tests ====================

    async def test_parse_detects_html_content_type(self, parser, mock_http_client):
        """Test that HTML content-type routes to HTML parsing"""
        url = "https://codeforces.com/problemset/problem/1/A"
        mock_http_client.get_content_type.return_value = "text/html; charset=utf-8"
        mock_http_client.get_text.return_value = "<html><body>Tutorial</body></html>"

        result = await parser.parse(url)

        assert result.format == TutorialFormat.HTML
        mock_http_client.get_text.assert_called_once_with(url)
        mock_http_client.get_bytes.assert_not_called()

    async def test_parse_detects_pdf_content_type(self, parser, mock_http_client):
        """Test that PDF content-type routes to PDF parsing"""
        url = "https://codeforces.com/tutorials/123.pdf"
        mock_http_client.get_content_type.return_value = "application/pdf"
        mock_http_client.get_bytes.return_value = b"%PDF-1.4..."

        # We need to patch fitz.open since it's used in _parse_pdf
        with patch("fitz.open") as mock_fitz:
            # Mock the document iteration
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

    # ==================== HTML Cleaning Tests ====================

    async def test_html_removes_unwanted_tags(self, parser, mock_http_client):
        """Test that script, style, nav, and footer tags are removed"""
        url = "https://codeforces.com/problemset"
        html_content = """
        <html>
            <body>
                <script>alert('remove me')</script>
                <style>.css { display: none; }</style>
                <nav>Menu</nav>
                <div class="ttypography">
                    <h1>Actual Content</h1>
                    <p>Description</p>
                </div>
                <footer>Copyright</footer>
            </body>
        </html>
        """
        mock_http_client.get_content_type.return_value = "text/html"
        mock_http_client.get_text.return_value = html_content

        result = await parser.parse(url)

        # Check that unwanted content is gone
        assert "alert" not in result.content
        assert "css" not in result.content
        assert "Menu" not in result.content
        assert "Copyright" not in result.content

        # Check that wanted content is present
        assert "Actual Content" in result.content
        assert "Description" in result.content

    async def test_html_extracts_title_correctly(self, parser, mock_http_client):
        """Test title extraction from h1 or title tag"""
        url = "https://codeforces.com/test"
        html_content = """
        <html>
            <head><title>Page Title</title></head>
            <body>
                <h1>Content Title</h1>
                <div class="ttypography">Content</div>
            </body>
        </html>
        """
        mock_http_client.get_content_type.return_value = "text/html"
        mock_http_client.get_text.return_value = html_content

        result = await parser.parse(url)

        assert result.title == "Content Title"

    async def test_html_fallback_title(self, parser, mock_http_client):
        """Test fallback to <title> if <h1> is missing"""
        url = "https://codeforces.com/test"
        html_content = """
        <html>
            <head><title>Page Title</title></head>
            <body>
                <div class="ttypography">Content</div>
            </body>
        </html>
        """
        mock_http_client.get_content_type.return_value = "text/html"
        mock_http_client.get_text.return_value = html_content

        result = await parser.parse(url)

        assert result.title == "Page Title"

    async def test_html_extracts_from_ttypography_div(self, parser, mock_http_client):
        """Test that content is extracted from div if present"""
        url = "https://codeforces.com/problem/1"
        html_content = """
        <html>
            <body>
                <div>Sidebar content</div>
                <div class="ttypography">
                    Target Content
                </div>
                <div>More noise</div>
            </body>
        </html>
        """
        mock_http_client.get_content_type.return_value = "text/html"
        mock_http_client.get_text.return_value = html_content

        result = await parser.parse(url)

        assert "Target Content" in result.content
        assert "Sidebar content" not in result.content
        assert "More noise" not in result.content

    async def test_html_fallback_to_full_body(self, parser, mock_http_client):
        """Test fallback to body content if div is missing"""
        url = "https://codeforces.com/generic"
        html_content = """
        <html>
            <body>
                <div>Some Content</div>
                <p>More Content</p>
            </body>
        </html>
        """
        mock_http_client.get_content_type.return_value = "text/html"
        mock_http_client.get_text.return_value = html_content

        result = await parser.parse(url)

        assert "Some Content" in result.content
        assert "More Content" in result.content

    # ==================== PDF Extraction Tests ====================

    async def test_pdf_extraction_success(self, parser, mock_http_client):
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

    # ==================== Rendering Logic Tests ====================

    @patch("domain.parsers.tutorial_parser.get_settings")
    async def test_uses_js_rendering_for_blogs_and_contests(
        self, mock_settings, parser, mock_http_client
    ):
        """Test that JS rendering is triggered for blog and contest URLs"""
        # Scenario 1: Blog URL
        url_blog = "https://codeforces.com/blog/entry/12345"
        mock_http_client.get_content_type.return_value = "text/html"
        mock_http_client.get_text_with_js.return_value = (
            "<html><body>JS Loaded Content</body></html>"
        )

        mock_settings_obj = Mock()
        mock_settings_obj.http_js_wait = 2000
        mock_settings.return_value = mock_settings_obj

        await parser.parse(url_blog)

        mock_http_client.get_text_with_js.assert_called_with(url_blog, wait_time=2000)

        # Scenario 2: Contest URL
        url_contest = "https://codeforces.com/contest/1234/problem/A"

        await parser.parse(url_contest)
        mock_http_client.get_text_with_js.assert_called_with(
            url_contest, wait_time=2000
        )

    async def test_uses_static_rendering_for_other_pages(
        self, parser, mock_http_client
    ):
        """Test that static rendering is used for non-blog/contest codeforces pages"""
        url = "https://codeforces.com/problemset/problem/1234/A"
        mock_http_client.get_content_type.return_value = "text/html"
        mock_http_client.get_text.return_value = (
            "<html><body>Static Content</body></html>"
        )

        await parser.parse(url)

        mock_http_client.get_text.assert_called_once_with(url)
        mock_http_client.get_text_with_js.assert_not_called()

    # ==================== Error Handling Tests ====================

    async def test_parsing_error_propagated(self, parser, mock_http_client):
        """Test that exceptions during parsing are re-raised as ParsingError"""
        url = "https://codeforces.com/broken"
        mock_http_client.get_content_type.side_effect = Exception("Network Error")

        with pytest.raises(ParsingError) as exc_info:
            await parser.parse(url)

        assert "Failed to parse tutorial" in str(exc_info.value)

    # ==================== Edge Cases & Integration ====================

    async def test_empty_content_handling(self, parser, mock_http_client):
        """Test handling of empty content"""
        url = "https://codeforces.com/empty"
        mock_http_client.get_content_type.return_value = "text/html"
        mock_http_client.get_text.return_value = ""

        result = await parser.parse(url)
        assert result.content == ""

    async def test_unicode_handling_in_html(self, parser, mock_http_client):
        """Test proper Unicode handling in HTML content"""
        url = "https://codeforces.com/unicode"
        html_content = """
        <html>
            <body>
                <div class="ttypography">
                    <div>Тест на русском</div>
                    <div>中文测试</div>
                    <div>العربية</div>
                </div>
            </body>
        </html>
        """
        mock_http_client.get_content_type.return_value = "text/html; charset=utf-8"
        mock_http_client.get_text.return_value = html_content

        result = await parser.parse(url)

        assert "Тест на русском" in result.content
        assert "中文测试" in result.content

    async def test_large_html_content_handling(self, parser, mock_http_client):
        """Test handling of large HTML documents"""
        url = "https://codeforces.com/large"
        # Create large HTML (simulate large content)
        large_div = "<div>" + "x" * 10000 + "</div>"
        html_content = (
            f"<html><body><div class='ttypography'>{large_div}</div></body></html>"
        )

        mock_http_client.get_content_type.return_value = "text/html"
        mock_http_client.get_text.return_value = html_content

        result = await parser.parse(url)

        assert result.format == TutorialFormat.HTML
        assert len(result.content) >= 10000
