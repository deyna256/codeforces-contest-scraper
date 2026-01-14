import pytest

from domain.models import ProblemIdentifier, TutorialData, TutorialFormat
from domain.extractors.editorial_extractor import EditorialExtractor


class FakeAI:
    def __init__(self, response=None, raise_exc=False, model="test-model"):
        self._response = response
        self._raise = raise_exc
        self.model = model

    async def extract_solution(self, *args, **kwargs):
        if self._raise:
            raise RuntimeError("AI failure")
        return self._response


@pytest.fixture
def tutorial():
    return TutorialData(
        url="https://cf.com/contest/123",
        content="tutorial",
        format=TutorialFormat.HTML,
    )


@pytest.fixture
def identifier():
    return ProblemIdentifier(problem_id="1", contest_id="123")


@pytest.fixture
def extractor_factory():
    def _make(ai):
        return EditorialExtractor(ai)
    return _make

@pytest.fixture
def fake_ai():
    def _make(response=None, raise_exc=False, model="test-model"):
        return FakeAI(response=response, raise_exc=raise_exc, model=model)
    return _make

