import pytest


from domain.exceptions import ExtractionError


@pytest.mark.asyncio
async def test_returns_solution_text_when_ai_returns_raw_response(
    extractor_factory, tutorial, identifier, fake_ai
):
    ai = fake_ai({"raw_response": "solution"})
    extractor = extractor_factory(ai)

    editorial = await extractor.extract(tutorial=tutorial, identifier=identifier)

    assert editorial.solution_text == "solution"


@pytest.mark.asyncio
async def test_raises_extraction_error_when_ai_throws(
    extractor_factory, tutorial, identifier, fake_ai
):
    ai = fake_ai(raise_exc=True)
    extractor = extractor_factory(ai)

    with pytest.raises(ExtractionError):
        await extractor.extract(tutorial=tutorial, identifier=identifier)


@pytest.mark.asyncio
async def test_allows_empty_string_as_valid_solution(
    extractor_factory, tutorial, identifier, fake_ai
):
    ai = fake_ai({"raw_response": ""})
    extractor = extractor_factory(ai)

    editorial = await extractor.extract(tutorial=tutorial, identifier=identifier)

    assert editorial.solution_text == ""
