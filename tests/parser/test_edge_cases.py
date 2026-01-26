import pytest
from domain.models import TutorialFormat
from domain.exceptions import ParsingError

@pytest.mark.asyncio
async def test_parsing_error_propagated(parser, mock_http_client):
    """Test that exceptions during parsing are re-raised as ParsingError"""
    url = "https://codeforces.com/broken"
    mock_http_client.get_content_type.side_effect = Exception("Network Error")

    with pytest.raises(ParsingError) as exc_info:
        await parser.parse(url)

    assert "Failed to parse tutorial" in str(exc_info.value)


@pytest.mark.asyncio
async def test_empty_content_handling(parser, mock_http_client):
    """Test handling of empty content"""
    url = "https://codeforces.com/empty"
    mock_http_client.get_content_type.return_value = "text/html"
    mock_http_client.get_text.return_value = ""

    result = await parser.parse(url)
    assert result.content == ""


@pytest.mark.asyncio
async def test_large_html_content_handling(parser, mock_http_client):
    """Test handling of large HTML documents"""
    url = "https://codeforces.com/large"
    large_div = "<div>" + "x" * 10000 + "</div>"
    html_content = (
        f"<html><body><div class='ttypography'>{large_div}</div></body></html>"
    )

    mock_http_client.get_content_type.return_value = "text/html"
    mock_http_client.get_text.return_value = html_content

    result = await parser.parse(url)

    assert result.format == TutorialFormat.HTML
    assert len(result.content) >= 10000
