"""Tests for the Grok TTS client."""

import pytest
from httpx import AsyncClient, Response

from grok_tts_cli.client import (
    AuthenticationError,
    GrokTTSClient,
    GrokTTSError,
    RateLimitError,
)


@pytest.fixture
def client():
    """Create a test client."""
    return GrokTTSClient(api_key="test-api-key")


def test_client_requires_api_key(monkeypatch):
    """Test that client raises error if no API key provided."""
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with pytest.raises(AuthenticationError):
        GrokTTSClient()


async def test_synthesize_success(client, monkeypatch):
    """Test successful synthesis."""
    mock_audio = b"fake-mp3-data"

    async def mock_post(*args, **kwargs):
        return Response(200, content=mock_audio)

    monkeypatch.setattr(AsyncClient, "post", mock_post)

    result = await client.synthesize("Hello world")
    assert result == mock_audio


async def test_synthesize_auth_error(client, monkeypatch):
    """Test authentication error handling."""

    async def mock_post(*args, **kwargs):
        return Response(401, text="Unauthorized")

    monkeypatch.setattr(AsyncClient, "post", mock_post)

    with pytest.raises(AuthenticationError):
        await client.synthesize("Hello")


async def test_synthesize_rate_limit(client, monkeypatch):
    """Test rate limit error handling."""

    async def mock_post(*args, **kwargs):
        return Response(429, text="Rate limit exceeded")

    monkeypatch.setattr(AsyncClient, "post", mock_post)

    with pytest.raises(RateLimitError):
        await client.synthesize("Hello")


async def test_synthesize_with_voice_and_lang(client, monkeypatch):
    """Test synthesis with custom voice and language."""
    mock_audio = b"fake-mp3-data"
    captured_payload = {}

    async def mock_post(*args, **kwargs):
        nonlocal captured_payload
        captured_payload = kwargs.get("json", {})
        return Response(200, content=mock_audio)

    monkeypatch.setattr(AsyncClient, "post", mock_post)

    result = await client.synthesize("Hello", voice_id="rex", language="es")
    assert result == mock_audio
    assert captured_payload["voice_id"] == "rex"
    assert captured_payload["language"] == "es"


async def test_synthesize_batch(client, monkeypatch):
    """Test batch synthesis."""
    mock_audio = b"fake-mp3-data"

    async def mock_post(*args, **kwargs):
        return Response(200, content=mock_audio)

    monkeypatch.setattr(AsyncClient, "post", mock_post)

    texts = ["Hello", "World", "Test"]
    results = []
    async for i, audio in client.synthesize_batch(texts):
        results.append((i, audio))

    assert len(results) == 3
    assert results[0] == (0, mock_audio)
    assert results[1] == (1, mock_audio)
    assert results[2] == (2, mock_audio)
