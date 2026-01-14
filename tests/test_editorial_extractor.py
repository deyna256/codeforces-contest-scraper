import pytest


from domain.models import ProblemIdentifier, TutorialData
from domain.exceptions import ExtractionError
from domain.extractors.editorial_extractor import EditorialExtractor


# ============================================================
# Fake AI Client
# ============================================================

class FakeAI:
    def __init__(self, response=None, raise_exc=False, model="test-model"):
        self._response = response
        self._raise = raise_exc
        self.model = model

    async def extract_solution(self, *args, **kwargs):
        if self._raise:
            raise RuntimeError("AI failure")
        return self._response


class FakeAIMissingModel(FakeAI):
    pass


# ============================================================
# Layer 1 — AI Boundary
# ============================================================

@pytest.mark.asyncio
async def test_l1_valid_response():
    ai = FakeAI({"raw_response": "solution"})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))
    assert editorial.solution_text == "solution"


@pytest.mark.asyncio
async def test_l1_exception():
    ai = FakeAI(raise_exc=True)
    extractor = EditorialExtractor(ai)

    with pytest.raises(ExtractionError):
        await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))

@pytest.mark.asyncio
async def test_l1_empty_dict():
    ai = FakeAI({})
    extractor = EditorialExtractor(ai)

    with pytest.raises(ExtractionError):
        await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))


@pytest.mark.asyncio
async def test_l1_missing_raw_response():
    ai = FakeAI({"msg": "hi"})
    extractor = EditorialExtractor(ai)

    with pytest.raises(ExtractionError):
        await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))


@pytest.mark.asyncio
async def test_l1_raw_response_none():
    ai = FakeAI({"raw_response": None})
    extractor = EditorialExtractor(ai)

    with pytest.raises(ExtractionError):
        await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))


@pytest.mark.asyncio
async def test_l1_raw_response_number():
    ai = FakeAI({"raw_response": 10})
    extractor = EditorialExtractor(ai)

    with pytest.raises(ExtractionError):
        await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))


@pytest.mark.asyncio
async def test_l1_raw_response_list():
    ai = FakeAI({"raw_response": []})
    extractor = EditorialExtractor(ai)

    with pytest.raises(ExtractionError):
        await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))


@pytest.mark.asyncio
async def test_l1_raw_response_dict():
    ai = FakeAI({"raw_response": {}})
    extractor = EditorialExtractor(ai)

    with pytest.raises(ExtractionError):
        await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))


@pytest.mark.asyncio
async def test_l1_empty_string_allowed():
    ai = FakeAI({"raw_response": ""})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))
    assert editorial.solution_text == ""


# ============================================================
# Layer 2 — NOT_FOUND protocol
# ============================================================

@pytest.mark.asyncio
@pytest.mark.parametrize("text", [
    "NOT_FOUND",
    "NOT_FOUND: missing",
    "   NOT_FOUND",
    "\n\nNOT_FOUND",
    "NOT_FOUND\nproblem missing",
])
async def test_l2_not_found_blocks(text):
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    with pytest.raises(ExtractionError):
        await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))


@pytest.mark.asyncio
@pytest.mark.parametrize("text", [
    "not_found",
    "Not_Found",
    "The result is NOT_FOUND",
    "```text\nNOT_FOUND\n```",
    "Here\nNOT_FOUND\nlater",
])
async def test_l2_not_found_not_blocked(text):
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))
    assert editorial.solution_text == text.strip()

# ============================================================
# Layer 3 — Metadata & code parsing
# ============================================================

@pytest.mark.asyncio
async def test_metadata_stripped_only_when_protocol_matches():
    """
    Metadata is stripped only when the exact front-matter protocol matches:
        ---
        meta
        ---

        solution
    """
    text = "---\nmeta\n---\n\nsolution"
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))
    assert editorial.solution_text == "solution"


@pytest.mark.asyncio
async def test_metadata_not_stripped_when_blank_line_missing():
    """
    If the blank line after --- is missing, the regex must not match
    and the full response must be preserved.
    """
    text = "---\nmeta\n---\nsolution"
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))
    assert editorial.solution_text == text.strip()


@pytest.mark.asyncio
async def test_metadata_not_stripped_when_extra_text_before_frontmatter():
    """
    Front-matter must be at the very beginning.
    If anything appears before '---', nothing is stripped.
    """
    text = "hello\n---\nmeta\n---\n\nsolution"
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))
    assert editorial.solution_text == text.strip()


@pytest.mark.asyncio
async def test_metadata_not_stripped_when_extra_blank_lines_exist():
    """
    The regex requires exactly one blank line after the closing ---.
    Extra blank lines should prevent matching.
    """
    text = "---\nmeta\n---\n\n\nsolution"
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))
    assert editorial.solution_text == text.strip()


# -------------------- Code block extraction --------------------

@pytest.mark.asyncio
async def test_single_code_block_extracted():
    """
    A single fenced code block should be detected and extracted.
    """
    text = "text\n```python\nprint(1)\n```"
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))

    assert len(editorial.code_snippets) == 1
    assert editorial.code_snippets[0].language == "python"
    assert "print(1)" in editorial.code_snippets[0].code


@pytest.mark.asyncio
async def test_multiple_code_blocks_extracted():
    """
    Multiple fenced code blocks must all be extracted.
    """
    text = "A\n```python\nx=1\n```\nB\n```cpp\ny=2\n```"
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))

    assert len(editorial.code_snippets) == 2
    assert editorial.code_snippets[0].language == "python"
    assert editorial.code_snippets[1].language == "cpp"


@pytest.mark.asyncio
async def test_code_block_without_language_defaults_to_text():
    """
    If no language is specified after the backticks,
    the extractor must default to 'text'.
    """
    text = "```\\nhello\\n```"
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))

    assert len(editorial.code_snippets) == 1
    assert editorial.code_snippets[0].language == "text"
    assert editorial.code_snippets[0].code == "hello"


@pytest.mark.asyncio
async def test_broken_code_block_is_ignored():
    """
    If a code fence is not closed, it should not be treated as a code block.
    """
    text = "```python\nprint(1)"
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))

    assert editorial.code_snippets == []


@pytest.mark.asyncio
async def test_code_block_with_empty_body_is_ignored():
    """
    Empty code blocks should not be added to code_snippets.
    """
    text = "```python\n\n```"
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))

    assert editorial.code_snippets == []


@pytest.mark.asyncio
async def test_text_around_code_is_preserved():
    """
    Code extraction must not remove or alter solution_text.
    """
    text = "Before\n```python\nx=1\n```\nAfter"
    ai = FakeAI({"raw_response": text})
    extractor = EditorialExtractor(ai)

    editorial = await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))

    assert editorial.solution_text == text.strip()



# ============================================================
# Layer 4 — Editorial Contract
# ============================================================

@pytest.mark.asyncio
async def test_editorial_contract_full():
    """
    This test locks the public Editorial API contract.
    Any future change that alters these fields must fail CI.
    """
    ai = FakeAI({"raw_response": "final solution"}, model="gpt-test")
    extractor = EditorialExtractor(ai)

    tutorial = TutorialData("https://cf.com/contest/123", "tutorial content")
    pid = ProblemIdentifier("1872C")

    editorial = await extractor.extract(tutorial, pid)

    # Identity & provenance
    assert editorial.problem_id == "1872C"
    assert editorial.source_url == "https://cf.com/contest/123"
    assert editorial.ai_model == "gpt-test"

    # Core content
    assert editorial.solution_text == "final solution"
    assert isinstance(editorial.code_snippets, list)

    # Stable defaults (must not change)
    assert editorial.approach is None
    assert editorial.algorithm is None
    assert editorial.time_complexity is None
    assert editorial.space_complexity is None
    assert editorial.hints == []
    assert editorial.notes is None

    # Timestamp must exist
    assert editorial.extracted_at is not None


@pytest.mark.asyncio
async def test_missing_model_attribute_fails():
    """
    If the AI client does not expose a `model` attribute,
    the extractor must fail instead of silently producing bad data.
    """
    class FakeAIMissingModel:
        async def extract_solution(self, *args, **kwargs):
            return {"raw_response": "x"}

    extractor = EditorialExtractor(FakeAIMissingModel())

    with pytest.raises(ExtractionError):
        await extractor.extract(TutorialData("u", "tutorial"), ProblemIdentifier("1"))

