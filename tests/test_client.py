"""Comprehensive tests for the Grok TTS client."""

import asyncio

import httpx
import pytest

from grok_tts_cli.client import (
    AuthenticationError,
    GrokTTSClient,
    GrokTTSError,
    RateLimitError,
)

# ============================================================================
# Initialization Tests
# ============================================================================


def test_client_requires_api_key(clear_env_api_key):
    """Test that client raises error if no API key provided."""
    with pytest.raises(AuthenticationError) as exc_info:
        GrokTTSClient()
    assert "XAI_API_KEY not found" in str(exc_info.value)


def test_client_accepts_explicit_api_key():
    """Test client accepts API key via constructor."""
    client = GrokTTSClient(api_key="explicit-key")
    assert client.api_key == "explicit-key"


def test_client_uses_env_var(mock_env_api_key):
    """Test client uses XAI_API_KEY environment variable."""
    client = GrokTTSClient()
    assert client.api_key == mock_env_api_key


def test_client_explicit_key_overrides_env(monkeypatch):
    """Test explicit API key overrides environment variable."""
    monkeypatch.setenv("XAI_API_KEY", "env-key")
    client = GrokTTSClient(api_key="explicit-key")
    assert client.api_key == "explicit-key"


def test_client_rejects_empty_string_key(clear_env_api_key):
    """Test client rejects empty string as API key."""
    with pytest.raises(AuthenticationError):
        GrokTTSClient(api_key="")


def test_client_rejects_none_key_without_env(clear_env_api_key):
    """Test client rejects None API key when env var not set."""
    with pytest.raises(AuthenticationError):
        GrokTTSClient(api_key=None)


# ============================================================================
# Synthesize Success Tests
# ============================================================================


async def test_synthesize_success(client, monkeypatch):
    """Test successful synthesis."""
    mock_audio = b"fake-mp3-data"

    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, content=mock_audio)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    result = await client.synthesize("Hello world")
    assert result == mock_audio


async def test_synthesize_correct_url(client, monkeypatch):
    """Test that synthesize uses correct API URL."""
    captured_url = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_url
        captured_url = url
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await client.synthesize("Hello")
    assert captured_url == "https://api.x.ai/v1/tts"


async def test_synthesize_correct_headers(client, monkeypatch):
    """Test that synthesize sends correct headers."""
    captured_headers = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_headers
        captured_headers = kwargs.get("headers", {})
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await client.synthesize("Hello")
    assert "Authorization" in captured_headers
    assert captured_headers["Authorization"] == f"Bearer {client.api_key}"
    assert captured_headers["Content-Type"] == "application/json"


async def test_synthesize_correct_payload(client, monkeypatch):
    """Test that synthesize sends correct payload."""
    captured_payload = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_payload
        captured_payload = kwargs.get("json", {})
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await client.synthesize("Hello world", "rex", "es")
    assert captured_payload["text"] == "Hello world"
    assert captured_payload["voice_id"] == "rex"
    assert captured_payload["language"] == "es"


async def test_synthesize_returns_bytes(client, monkeypatch):
    """Test that synthesize returns bytes."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, content=b"\x00\x01\x02\x03")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    result = await client.synthesize("Hello")
    assert isinstance(result, bytes)
    assert result == b"\x00\x01\x02\x03"


# ============================================================================
# Synthesize Error Handling Tests
# ============================================================================


async def test_synthesize_401_raises_auth_error(client, monkeypatch):
    """Test that 401 status raises AuthenticationError."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(401, text="Unauthorized")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(AuthenticationError) as exc_info:
        await client.synthesize("Hello")
    assert "Invalid API key" in str(exc_info.value)


async def test_synthesize_429_raises_rate_limit(client, monkeypatch):
    """Test that 429 status raises RateLimitError."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(429, text="Rate limit exceeded")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(RateLimitError) as exc_info:
        await client.synthesize("Hello")
    assert "Rate limit exceeded" in str(exc_info.value)


async def test_synthesize_500_raises_grok_error(client, monkeypatch):
    """Test that 500 status raises GrokTTSError."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(500, text="Internal server error")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(GrokTTSError) as exc_info:
        await client.synthesize("Hello")
    assert "500" in str(exc_info.value)


async def test_synthesize_400_raises_grok_error(client, monkeypatch):
    """Test that 400 status raises GrokTTSError."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(400, text="Bad request")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(GrokTTSError) as exc_info:
        await client.synthesize("Hello")
    assert "400" in str(exc_info.value)


async def test_synthesize_404_raises_grok_error(client, monkeypatch):
    """Test that 404 status raises GrokTTSError."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(404, text="Not found")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(GrokTTSError) as exc_info:
        await client.synthesize("Hello")
    assert "404" in str(exc_info.value)


async def test_synthesize_503_raises_grok_error(client, monkeypatch):
    """Test that 503 status raises GrokTTSError."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(503, text="Service unavailable")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(GrokTTSError) as exc_info:
        await client.synthesize("Hello")
    assert "503" in str(exc_info.value)


# ============================================================================
# Retry Logic Tests
# ============================================================================


async def test_timeout_retries(client, monkeypatch):
    """Test that timeouts are retried MAX_RETRIES times."""
    attempt_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        raise httpx.TimeoutException("Request timeout")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(GrokTTSError) as exc_info:
        await client.synthesize("Hello")

    assert attempt_count == client.MAX_RETRIES
    assert "timed out" in str(exc_info.value).lower()


async def test_network_error_retries(client, monkeypatch):
    """Test that network errors are retried MAX_RETRIES times."""
    attempt_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        raise httpx.NetworkError("Connection failed")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(GrokTTSError) as exc_info:
        await client.synthesize("Hello")

    assert attempt_count == client.MAX_RETRIES
    assert "Network error" in str(exc_info.value)


async def test_timeout_recovery_on_retry(client, monkeypatch):
    """Test that request succeeds after timeout if retry succeeds."""
    attempt_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise httpx.TimeoutException("Request timeout")
        return httpx.Response(200, content=b"success-data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    result = await client.synthesize("Hello")
    assert result == b"success-data"
    assert attempt_count == 2


async def test_network_recovery_on_retry(client, monkeypatch):
    """Test that request succeeds after network error if retry succeeds."""
    attempt_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise httpx.NetworkError("Connection failed")
        return httpx.Response(200, content=b"success-data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    result = await client.synthesize("Hello")
    assert result == b"success-data"
    assert attempt_count == 3


async def test_auth_error_not_retried(client, monkeypatch):
    """Test that authentication errors are not retried."""
    attempt_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(401, text="Unauthorized")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(AuthenticationError):
        await client.synthesize("Hello")

    # Should only attempt once, not retry
    assert attempt_count == 1


async def test_rate_limit_not_retried(client, monkeypatch):
    """Test that rate limit errors are not retried."""
    attempt_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        return httpx.Response(429, text="Rate limit")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(RateLimitError):
        await client.synthesize("Hello")

    # Should only attempt once, not retry
    assert attempt_count == 1


async def test_exponential_backoff_timing(client, monkeypatch):
    """Test that retry delays follow exponential backoff."""
    attempt_times = []

    async def mock_post(self, url, **kwargs):
        attempt_times.append(asyncio.get_event_loop().time())
        raise httpx.TimeoutException("Timeout")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(GrokTTSError):
        await client.synthesize("Hello")

    # Check we have 3 attempts
    assert len(attempt_times) == 3

    # Check delays between attempts (allowing some tolerance)
    delay1 = attempt_times[1] - attempt_times[0]
    delay2 = attempt_times[2] - attempt_times[1]

    # First retry: RETRY_DELAY * 1 = 1.0s
    # Second retry: RETRY_DELAY * 2 = 2.0s
    assert 0.9 < delay1 < 1.5  # ~1.0s with tolerance
    assert 1.9 < delay2 < 2.5  # ~2.0s with tolerance


# ============================================================================
# Synthesize with Parameters Tests
# ============================================================================


async def test_synthesize_all_voices(client, monkeypatch):
    """Test synthesize with all available voices."""
    voices = ["eve", "ara", "rex", "sal", "leo"]
    captured_voices = []

    async def mock_post(self, url, **kwargs):
        captured_voices.append(kwargs["json"]["voice_id"])
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    for voice in voices:
        await client.synthesize("Hello", voice_id=voice)

    assert captured_voices == voices


async def test_synthesize_all_languages(client, monkeypatch):
    """Test synthesize with all supported languages."""
    languages = [
        "en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "tr",
        "zh", "ja", "ko", "ar", "hi", "id", "ms", "th", "vi", "fil"
    ]
    captured_languages = []

    async def mock_post(self, url, **kwargs):
        captured_languages.append(kwargs["json"]["language"])
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    for lang in languages:
        await client.synthesize("Hello", language=lang)

    assert captured_languages == languages


async def test_synthesize_long_text(client, monkeypatch):
    """Test synthesize with long text."""
    long_text = "Hello world! " * 500  # ~6000 characters
    captured_text = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_text
        captured_text = kwargs["json"]["text"]
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await client.synthesize(long_text)
    assert captured_text == long_text
    assert len(captured_text) > 5000


async def test_synthesize_empty_text(client, monkeypatch):
    """Test synthesize with empty text edge case."""
    captured_text = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_text
        captured_text = kwargs["json"]["text"]
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await client.synthesize("")
    assert captured_text == ""


async def test_synthesize_unicode_text(client, monkeypatch):
    """Test synthesize with unicode text."""
    unicode_texts = [
        "Hello 世界",  # Chinese
        "Привет мир",  # Russian
        "مرحبا العالم",  # Arabic
        "שלום עולם",  # Hebrew
        "こんにちは世界",  # Japanese
        "안녕하세요 세계",  # Korean
        "Γεια σου κόσμε",  # Greek
        "🎉🎊✨",  # Emojis
    ]

    for unicode_text in unicode_texts:
        captured_text = None

        async def mock_post(self, url, **kwargs):
            nonlocal captured_text
            captured_text = kwargs["json"]["text"]
            return httpx.Response(200, content=b"data")

        monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

        await client.synthesize(unicode_text)
        assert captured_text == unicode_text


async def test_synthesize_speech_tags(client, monkeypatch):
    """Test synthesize with speech synthesis tags."""
    tagged_text = '<speak>Hello <break time="500ms"/> world!</speak>'
    captured_text = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_text
        captured_text = kwargs["json"]["text"]
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await client.synthesize(tagged_text)
    assert captured_text == tagged_text


async def test_synthesize_special_characters(client, monkeypatch):
    """Test synthesize with special characters."""
    special_text = 'Hello "world"!\n\tTab & newline\r\n$100 50%'
    captured_text = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_text
        captured_text = kwargs["json"]["text"]
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await client.synthesize(special_text)
    assert captured_text == special_text


async def test_synthesize_default_parameters(client, monkeypatch):
    """Test synthesize uses default parameters when not specified."""
    captured_payload = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_payload
        captured_payload = kwargs["json"]
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await client.synthesize("Hello")
    assert captured_payload["voice_id"] == "eve"
    assert captured_payload["language"] == "en"


# ============================================================================
# Batch Synthesis Tests
# ============================================================================


async def test_batch_empty_list(client, monkeypatch):
    """Test batch synthesis with empty list."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    results = []
    async for idx, audio in client.synthesize_batch([]):
        results.append((idx, audio))

    assert results == []


async def test_batch_single_item(client, monkeypatch):
    """Test batch synthesis with single item."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    results = []
    async for idx, audio in client.synthesize_batch(["Hello"]):
        results.append((idx, audio))

    assert len(results) == 1
    assert results[0] == (0, b"data")


async def test_batch_multiple_items(client, monkeypatch):
    """Test batch synthesis with multiple items."""
    texts = ["Hello", "World", "Test", "Batch"]

    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    results = []
    async for idx, audio in client.synthesize_batch(texts):
        results.append((idx, audio))

    assert len(results) == 4
    assert results[0] == (0, b"data")
    assert results[1] == (1, b"data")
    assert results[2] == (2, b"data")
    assert results[3] == (3, b"data")


async def test_batch_yields_correct_indices(client, monkeypatch):
    """Test that batch synthesis yields correct indices."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    indices = []
    async for idx, _audio in client.synthesize_batch(["A", "B", "C", "D", "E"]):
        indices.append(idx)

    assert indices == [0, 1, 2, 3, 4]


async def test_batch_error_mid_batch_propagates(client, monkeypatch):
    """Test that errors during batch synthesis are propagated."""
    call_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 3:
            return httpx.Response(500, text="Server error")
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    results = []
    with pytest.raises(GrokTTSError):
        async for idx, audio in client.synthesize_batch(["A", "B", "C", "D"]):
            results.append((idx, audio))

    # Should have processed 2 items before error
    assert len(results) == 2


async def test_batch_with_custom_voice(client, monkeypatch):
    """Test batch synthesis with custom voice."""
    captured_voices = []

    async def mock_post(self, url, **kwargs):
        captured_voices.append(kwargs["json"]["voice_id"])
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    async for _idx, _audio in client.synthesize_batch(["A", "B"], voice_id="rex"):
        pass

    assert all(v == "rex" for v in captured_voices)


async def test_batch_with_custom_language(client, monkeypatch):
    """Test batch synthesis with custom language."""
    captured_langs = []

    async def mock_post(self, url, **kwargs):
        captured_langs.append(kwargs["json"]["language"])
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    async for _idx, _audio in client.synthesize_batch(["A", "B"], language="es"):
        pass

    assert all(lang == "es" for lang in captured_langs)


async def test_batch_preserves_text_content(client, monkeypatch):
    """Test that batch synthesis preserves text content."""
    texts = ["First line", "Second line", "Third line"]
    captured_texts = []

    async def mock_post(self, url, **kwargs):
        captured_texts.append(kwargs["json"]["text"])
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    async for _idx, _audio in client.synthesize_batch(texts):
        pass

    assert captured_texts == texts


async def test_batch_large_list(client, monkeypatch):
    """Test batch synthesis with large list."""
    texts = [f"Line {i}" for i in range(100)]

    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, content=b"data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    count = 0
    async for _idx, _audio in client.synthesize_batch(texts):
        count += 1

    assert count == 100
