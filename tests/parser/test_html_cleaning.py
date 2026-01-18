import pytest

@pytest.mark.asyncio
async def test_html_removes_unwanted_tags(parser, mock_http_client):
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

    assert "alert" not in result.content
    assert "css" not in result.content
    assert "Menu" not in result.content
    assert "Copyright" not in result.content
    assert "Actual Content" in result.content
    assert "Description" in result.content


@pytest.mark.asyncio
async def test_html_extracts_title_correctly(parser, mock_http_client):
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


@pytest.mark.asyncio
async def test_html_fallback_title(parser, mock_http_client):
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


@pytest.mark.asyncio
async def test_html_extracts_from_ttypography_div(parser, mock_http_client):
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


@pytest.mark.asyncio
async def test_html_fallback_to_full_body(parser, mock_http_client):
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


@pytest.mark.asyncio
async def test_unicode_handling_in_html(parser, mock_http_client):
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
