import pytest

from unittest.mock import MagicMock, patch
from domain.models import ProblemData, Editorial, CachedEditorial, ProblemIdentifier


@pytest.mark.asyncio
async def test_get_editorial_cache_miss_runs_pipeline(mock_clients) -> None:
    url = "https://codeforces.com/problemset/problem/1234/A"
    mock_clients["cache_client"].get.return_value = None

    mock_editorial = MagicMock(spec=Editorial)
    mock_identifier = MagicMock(spec=ProblemIdentifier)
    mock_identifier.cache_key = "test_key"
    mock_problem_data = ProblemData(
        title="Test Problem",
        url=url,
        identifier=mock_identifier,
    )
    mock_tutorial_data = MagicMock()
    mock_tutorial_data.format = "BLOG_POST"

    with (
        patch("services.editorial.URLParser.parse", return_value=mock_identifier),
        patch("services.editorial._parse_problem_page", return_value=mock_problem_data),
        patch(
            "services.editorial._find_tutorial",
            return_value="https://codeforces.com/blog/entry/123",
        ),
        patch("services.editorial._parse_tutorial", return_value=mock_tutorial_data),
        patch("services.editorial._extract_editorial", return_value=mock_editorial),
        patch("services.editorial._save_to_cache") as mock_save,
    ):
        from services.editorial import get_editorial

        editorial, problem_data = await get_editorial(
            url=url,
            http_client=mock_clients["http_client"],
            ai_client=mock_clients["ai_client"],
            cache_client=mock_clients["cache_client"],
            use_cache=True,
        )

        assert editorial == mock_editorial
        assert problem_data == mock_problem_data
        mock_clients["cache_client"].get.assert_called_once_with(mock_identifier.cache_key)
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_get_editorial_cache_hit_skip_pipeline(mock_clients) -> None:
    url = "https://codeforces.com/problemset/problem/1234/A"

    fake_editorial = MagicMock(spec=Editorial)
    fake_cached = MagicMock(spec=CachedEditorial)
    fake_cached.editorial = fake_editorial

    mock_identifier = MagicMock(spec=ProblemIdentifier)
    mock_identifier.cache_key = "test_key"

    mock_problem_data = ProblemData(
        title="Test Title",
        url=url,
        identifier=mock_identifier,
    )

    with (
        patch("services.editorial.URLParser.parse", return_value=mock_identifier),
        patch("services.editorial.CachedEditorial.from_dict", return_value=fake_cached),
        patch("services.editorial._parse_problem_page", return_value=mock_problem_data),
        patch("services.editorial._find_tutorial") as mock_find_tutorial,
        patch("services.editorial._parse_tutorial") as mock_parse_tutorial,
        patch("services.editorial._extract_editorial") as mock_extract,
    ):
        from services.editorial import get_editorial

        mock_clients["cache_client"].get.return_value = {"some": "json"}

        editorial, problem_data = await get_editorial(
            url=url,
            http_client=mock_clients["http_client"],
            ai_client=mock_clients["ai_client"],
            cache_client=mock_clients["cache_client"],
            use_cache=True,
        )

        assert editorial == fake_editorial
        assert problem_data == mock_problem_data
        mock_clients["cache_client"].get.assert_called_once_with(mock_identifier.cache_key)
        mock_find_tutorial.assert_not_called()
        mock_parse_tutorial.assert_not_called()
        mock_extract.assert_not_called()


@pytest.mark.asyncio
async def test_clear_cache(mock_clients) -> None:
    from services.editorial import clear_cache

    await clear_cache(mock_clients["cache_client"])

    mock_clients["cache_client"].flushdb.assert_called_once()


@pytest.mark.asyncio
async def test_clear_cache_no_client() -> None:
    from services.editorial import clear_cache

    await clear_cache(None)
