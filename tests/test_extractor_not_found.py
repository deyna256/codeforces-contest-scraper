import pytest


from domain.exceptions import ExtractionError


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text",
    [
        "NOT_FOUND",
        "NOT_FOUND: missing",
        "   NOT_FOUND",
        "\n\nNOT_FOUND",
        "NOT_FOUND\nproblem missing",
    ],
)
async def test_exact_not_found_prefix_blocks_extraction(
    extractor_factory, tutorial, identifier, text, fake_ai
):
    ai = fake_ai({"raw_response": text})
    extractor = extractor_factory(ai)

    with pytest.raises(ExtractionError):
        await extractor.extract(tutorial=tutorial, identifier=identifier)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text",
    [
        "not_found",
        "Not_Found",
        "The result is NOT_FOUND",
        "```text\nNOT_FOUND\n```",
        "Here\nNOT_FOUND\nlater",
    ],
)
async def test_embedded_or_mixed_case_not_found_does_not_block(
    extractor_factory, tutorial, identifier, text, fake_ai
):
    ai = fake_ai({"raw_response": text})
    extractor = extractor_factory(ai)

    editorial = await extractor.extract(tutorial=tutorial, identifier=identifier)

    assert editorial.solution_text == text.strip()
