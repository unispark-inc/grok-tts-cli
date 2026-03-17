"""Shared test fixtures and utilities."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner
from httpx import Response

from grok_tts_cli.client import GrokTTSClient


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def api_key():
    """Return a test API key."""
    return "test-api-key-12345"


@pytest.fixture
def client(api_key):
    """Create a test client with mocked API key."""
    return GrokTTSClient(api_key=api_key)


@pytest.fixture
def mock_api_response():
    """Create a mock API response."""
    def _create_response(status_code=200, content=b"fake-mp3-data", text=""):
        return Response(status_code, content=content, text=text)
    return _create_response


@pytest.fixture
def mock_client():
    """Create a mock TTS client for CLI tests."""
    with patch("grok_tts_cli.cli.GrokTTSClient") as mock:
        instance = MagicMock()
        instance.synthesize = AsyncMock(return_value=b"fake-mp3-data")

        # Mock batch synthesis
        async def mock_batch_gen(*args, **kwargs):
            texts = args[0] if args else []
            for i, _text in enumerate(texts):
                yield i, b"fake-mp3-data"

        instance.synthesize_batch = mock_batch_gen
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_env_api_key(monkeypatch, api_key):
    """Set XAI_API_KEY environment variable."""
    monkeypatch.setenv("XAI_API_KEY", api_key)
    yield api_key


@pytest.fixture
def clear_env_api_key(monkeypatch):
    """Clear XAI_API_KEY environment variable."""
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    yield


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
