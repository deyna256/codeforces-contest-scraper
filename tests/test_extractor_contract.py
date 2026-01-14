import pytest




@pytest.mark.asyncio
async def test_editorial_contains_expected_fields(
    extractor_factory, tutorial, identifier, fake_ai
):
    ai = fake_ai({"raw_response": "final solution"}, model="gpt-test")
    extractor = extractor_factory(ai)

    editorial = await extractor.extract(tutorial=tutorial, identifier=identifier)

    assert editorial.problem_id == "1"
    assert editorial.source_url == "https://cf.com/contest/123"
    assert editorial.solution_text == "final solution"
    assert editorial.extracted_at is not None
