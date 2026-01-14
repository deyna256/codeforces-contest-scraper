import pytest




@pytest.mark.asyncio
async def test_strips_front_matter_when_protocol_matches(
    extractor_factory, tutorial, identifier, fake_ai
):
    text = "---\nmeta\n---\n\nsolution"
    ai = fake_ai({"raw_response": text})
    extractor = extractor_factory(ai)

    editorial = await extractor.extract(tutorial=tutorial, identifier=identifier)

    assert editorial.solution_text == "solution"


@pytest.mark.asyncio
async def test_preserves_text_when_front_matter_is_incomplete(
    extractor_factory, tutorial, identifier, fake_ai
):
    text = "---\nmeta\n---\nsolution"
    ai = fake_ai({"raw_response": text})
    extractor = extractor_factory(ai)

    editorial = await extractor.extract(tutorial=tutorial, identifier=identifier)

    assert editorial.solution_text == text.strip()
