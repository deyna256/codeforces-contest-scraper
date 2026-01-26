import pytest
from domain.parsers.tutorial_parser import TutorialParser

@pytest.fixture
def mock_http_client(mock_clients):
    """Get the mock HTTP client"""
    return mock_clients["http_client"]

@pytest.fixture
def parser(mock_http_client):
    return TutorialParser(http_client=mock_http_client)
