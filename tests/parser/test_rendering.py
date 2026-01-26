import pytest

@pytest.mark.asyncio
async def test_uses_js_rendering_for_blogs_and_contests(parser, mock_http_client):
    """Test that JS rendering is triggered for blog and contest URLs"""
    # Scenario 1: Blog URL
    url_blog = "https://codeforces.com/blog/entry/12345"
    mock_http_client.get_content_type.return_value = "text/html"
    mock_http_client.get_text_with_js.return_value = (
        "<html><body>JS Loaded Content</body></html>"
    )

    await parser.parse(url_blog)

    # Check for hardcoded wait_time as seen in implementation
    mock_http_client.get_text_with_js.assert_called_with(url_blog, wait_time=5000)

    # Scenario 2: Contest URL
    url_contest = "https://codeforces.com/contest/1234/problem/A"

    await parser.parse(url_contest)
    mock_http_client.get_text_with_js.assert_called_with(
        url_contest, wait_time=5000
    )


@pytest.mark.asyncio
async def test_uses_static_rendering_for_other_pages(parser, mock_http_client):
    """Test that static rendering is used for non-blog/contest codeforces pages"""
    url = "https://codeforces.com/problemset/problem/1234/A"
    mock_http_client.get_content_type.return_value = "text/html"
    mock_http_client.get_text.return_value = (
        "<html><body>Static Content</body></html>"
    )

    await parser.parse(url)

    mock_http_client.get_text.assert_called_once_with(url)
    mock_http_client.get_text_with_js.assert_not_called()
