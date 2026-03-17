"""End-to-end integration tests."""

from pathlib import Path

import httpx

from grok_tts_cli.cli import cli
from grok_tts_cli.client import GrokTTSClient

# ============================================================================
# End-to-End Speak Tests
# ============================================================================


def test_e2e_speak_text_to_file(runner, monkeypatch):
    """Test end-to-end speak with text to file."""
    # Mock HTTP response
    async def mock_post(self, url, **kwargs):
        assert url == "https://api.x.ai/v1/tts"
        assert kwargs["json"]["text"] == "Hello world"
        assert kwargs["json"]["voice_id"] == "eve"
        assert kwargs["json"]["language"] == "en"
        return httpx.Response(200, content=b"fake-audio-data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello world", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert Path("output.mp3").exists()
        assert Path("output.mp3").read_bytes() == b"fake-audio-data"


def test_e2e_speak_stdin_to_stdout(runner, monkeypatch):
    """Test end-to-end speak with stdin to stdout."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, content=b"audio-from-stdin")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    result = runner.invoke(
        cli,
        ["speak", "-o", "-"],
        input="Text from stdin",
        env={"XAI_API_KEY": "test-key"},
    )
    assert result.exit_code == 0
    assert b"audio-from-stdin" in result.stdout_bytes


def test_e2e_speak_with_voice_and_language(runner, monkeypatch):
    """Test end-to-end speak with custom voice and language."""
    captured_payload = {}

    async def mock_post(self, url, **kwargs):
        nonlocal captured_payload
        captured_payload = kwargs["json"]
        return httpx.Response(200, content=b"spanish-audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hola mundo", "-o", "output.mp3", "--voice", "rex", "--lang", "es"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert captured_payload["text"] == "Hola mundo"
        assert captured_payload["voice_id"] == "rex"
        assert captured_payload["language"] == "es"
        assert Path("output.mp3").read_bytes() == b"spanish-audio"


def test_e2e_speak_creates_nested_dirs(runner, monkeypatch):
    """Test end-to-end speak creates nested directories."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, content=b"audio-data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "a/b/c/output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert Path("a/b/c/output.mp3").exists()


# ============================================================================
# End-to-End Batch Tests
# ============================================================================


def test_e2e_batch_processing(runner, monkeypatch):
    """Test end-to-end batch processing."""
    call_count = 0
    captured_texts = []

    async def mock_post(self, url, **kwargs):
        nonlocal call_count
        call_count += 1
        captured_texts.append(kwargs["json"]["text"])
        return httpx.Response(200, content=f"audio-{call_count}".encode())

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        # Create input file
        Path("input.txt").write_text("Line 1\nLine 2\nLine 3")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert "Processed 3 files" in result.output

        # Check all files were created
        assert Path("output/output_0000.mp3").exists()
        assert Path("output/output_0001.mp3").exists()
        assert Path("output/output_0002.mp3").exists()

        # Check content
        assert Path("output/output_0000.mp3").read_bytes() == b"audio-1"
        assert Path("output/output_0001.mp3").read_bytes() == b"audio-2"
        assert Path("output/output_0002.mp3").read_bytes() == b"audio-3"

        # Verify texts were captured correctly
        assert captured_texts == ["Line 1", "Line 2", "Line 3"]


def test_e2e_batch_with_custom_voice(runner, monkeypatch):
    """Test end-to-end batch with custom voice."""
    captured_voices = []

    async def mock_post(self, url, **kwargs):
        captured_voices.append(kwargs["json"]["voice_id"])
        return httpx.Response(200, content=b"audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        Path("input.txt").write_text("Line 1\nLine 2")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output", "--voice", "leo"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert all(v == "leo" for v in captured_voices)


def test_e2e_batch_with_empty_lines(runner, monkeypatch):
    """Test end-to-end batch skips empty lines."""
    captured_texts = []

    async def mock_post(self, url, **kwargs):
        captured_texts.append(kwargs["json"]["text"])
        return httpx.Response(200, content=b"audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        Path("input.txt").write_text("Line 1\n\n  \nLine 2\n\t\n")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert captured_texts == ["Line 1", "Line 2"]


# ============================================================================
# Large Batch Processing Tests
# ============================================================================


def test_e2e_large_batch(runner, monkeypatch):
    """Test end-to-end processing of large batch (100 items)."""
    call_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, content=f"audio-{call_count}".encode())

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        # Create 100 lines
        lines = [f"Line {i}" for i in range(100)]
        Path("input.txt").write_text("\n".join(lines))

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert "Processed 100 files" in result.output
        assert call_count == 100

        # Spot check a few files
        assert Path("output/output_0000.mp3").exists()
        assert Path("output/output_0050.mp3").exists()
        assert Path("output/output_0099.mp3").exists()


# ============================================================================
# Unicode Text Pipeline Tests
# ============================================================================


def test_e2e_unicode_chinese(runner, monkeypatch):
    """Test end-to-end with Chinese unicode text."""
    captured_text = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_text
        captured_text = kwargs["json"]["text"]
        return httpx.Response(200, content=b"chinese-audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "你好世界", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert captured_text == "你好世界"
        assert Path("output.mp3").read_bytes() == b"chinese-audio"


def test_e2e_unicode_arabic(runner, monkeypatch):
    """Test end-to-end with Arabic unicode text."""
    captured_text = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_text
        captured_text = kwargs["json"]["text"]
        return httpx.Response(200, content=b"arabic-audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "مرحبا بالعالم", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert captured_text == "مرحبا بالعالم"


def test_e2e_unicode_emoji(runner, monkeypatch):
    """Test end-to-end with emoji."""
    captured_text = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_text
        captured_text = kwargs["json"]["text"]
        return httpx.Response(200, content=b"emoji-audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello 🌍 🎉", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert captured_text == "Hello 🌍 🎉"


def test_e2e_unicode_mixed_languages(runner, monkeypatch):
    """Test end-to-end with mixed language text."""
    captured_text = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_text
        captured_text = kwargs["json"]["text"]
        return httpx.Response(200, content=b"mixed-audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        mixed_text = "Hello 世界 مرحبا Привет"
        result = runner.invoke(
            cli,
            ["speak", mixed_text, "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert captured_text == mixed_text


def test_e2e_batch_unicode(runner, monkeypatch):
    """Test end-to-end batch with unicode content."""
    captured_texts = []

    async def mock_post(self, url, **kwargs):
        captured_texts.append(kwargs["json"]["text"])
        return httpx.Response(200, content=b"audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        Path("input.txt").write_text("Hello 世界\nПривет мир\n안녕하세요")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert captured_texts == ["Hello 世界", "Привет мир", "안녕하세요"]


# ============================================================================
# Speech Tags Pipeline Tests
# ============================================================================


def test_e2e_speech_tags(runner, monkeypatch):
    """Test end-to-end with speech synthesis tags."""
    captured_text = None

    async def mock_post(self, url, **kwargs):
        nonlocal captured_text
        captured_text = kwargs["json"]["text"]
        return httpx.Response(200, content=b"tagged-audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        tagged_text = '<speak>Hello <break time="500ms"/> world!</speak>'
        result = runner.invoke(
            cli,
            ["speak", tagged_text, "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert captured_text == tagged_text


def test_e2e_speech_tags_batch(runner, monkeypatch):
    """Test end-to-end batch with speech tags."""
    captured_texts = []

    async def mock_post(self, url, **kwargs):
        captured_texts.append(kwargs["json"]["text"])
        return httpx.Response(200, content=b"audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        content = '<speak>Line 1</speak>\n<speak>Line 2 <break/></speak>'
        Path("input.txt").write_text(content)

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert '<speak>Line 1</speak>' in captured_texts
        assert '<speak>Line 2 <break/></speak>' in captured_texts


# ============================================================================
# Client Integration Tests
# ============================================================================


async def test_client_integration_basic(monkeypatch):
    """Test basic client integration."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(200, content=b"audio-data")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    client = GrokTTSClient(api_key="test-key")
    result = await client.synthesize("Hello")
    assert result == b"audio-data"


async def test_client_integration_batch(monkeypatch):
    """Test client batch integration."""
    call_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal call_count
        call_count += 1
        return httpx.Response(200, content=f"audio-{call_count}".encode())

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    client = GrokTTSClient(api_key="test-key")
    results = []
    async for idx, audio in client.synthesize_batch(["A", "B", "C"]):
        results.append((idx, audio))

    assert len(results) == 3
    assert results[0] == (0, b"audio-1")
    assert results[1] == (1, b"audio-2")
    assert results[2] == (2, b"audio-3")


async def test_client_integration_all_voices(monkeypatch):
    """Test client with all voices."""
    captured_voices = []

    async def mock_post(self, url, **kwargs):
        captured_voices.append(kwargs["json"]["voice_id"])
        return httpx.Response(200, content=b"audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    client = GrokTTSClient(api_key="test-key")
    voices = ["eve", "ara", "rex", "sal", "leo"]

    for voice in voices:
        await client.synthesize("Test", voice_id=voice)

    assert captured_voices == voices


async def test_client_integration_all_languages(monkeypatch):
    """Test client with all languages."""
    captured_langs = []

    async def mock_post(self, url, **kwargs):
        captured_langs.append(kwargs["json"]["language"])
        return httpx.Response(200, content=b"audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    client = GrokTTSClient(api_key="test-key")
    languages = ["en", "es", "fr", "de", "it"]

    for lang in languages:
        await client.synthesize("Test", language=lang)

    assert captured_langs == languages


# ============================================================================
# Error Handling Integration Tests
# ============================================================================


def test_e2e_auth_error_handling(runner, monkeypatch):
    """Test end-to-end authentication error handling."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(401, text="Unauthorized")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3"],
            env={"XAI_API_KEY": "invalid-key"},
        )
        assert result.exit_code == 1
        # Error should be captured either as exception or in output
        assert result.exception is not None or "error" in result.output.lower()
        assert not Path("output.mp3").exists()


def test_e2e_rate_limit_handling(runner, monkeypatch):
    """Test end-to-end rate limit error handling."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(429, text="Rate limit exceeded")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 1
        assert result.exception is not None or "error" in result.output.lower()


def test_e2e_server_error_handling(runner, monkeypatch):
    """Test end-to-end server error handling."""
    async def mock_post(self, url, **kwargs):
        return httpx.Response(500, text="Internal server error")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 1
        assert result.exception is not None or "error" in result.output.lower()


# ============================================================================
# Retry Integration Tests
# ============================================================================


async def test_client_retry_integration(monkeypatch):
    """Test client retry integration."""
    attempt_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise httpx.TimeoutException("Timeout")
        return httpx.Response(200, content=b"success-after-retry")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    client = GrokTTSClient(api_key="test-key")
    result = await client.synthesize("Hello")
    assert result == b"success-after-retry"
    assert attempt_count == 2


def test_e2e_retry_recovery(runner, monkeypatch):
    """Test end-to-end retry and recovery."""
    attempt_count = 0

    async def mock_post(self, url, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise httpx.TimeoutException("Timeout")
        return httpx.Response(200, content=b"recovered-audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert Path("output.mp3").read_bytes() == b"recovered-audio"


# ============================================================================
# Complex Workflow Tests
# ============================================================================


def test_e2e_all_voices_batch(runner, monkeypatch):
    """Test batch processing with all voices."""
    captured_data = []

    async def mock_post(self, url, **kwargs):
        captured_data.append((kwargs["json"]["text"], kwargs["json"]["voice_id"]))
        return httpx.Response(200, content=b"audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    voices = ["eve", "ara", "rex", "sal", "leo"]

    with runner.isolated_filesystem():
        for voice in voices:
            Path("input.txt").write_text(f"Test with {voice}")
            result = runner.invoke(
                cli,
                ["batch", "input.txt", "-o", f"output_{voice}", "--voice", voice],
                env={"XAI_API_KEY": "test-key"},
            )
            assert result.exit_code == 0

    # Verify all voices were used
    used_voices = [v for _, v in captured_data]
    assert set(used_voices) == set(voices)


def test_e2e_multiple_languages(runner, monkeypatch):
    """Test processing text in multiple languages."""
    captured_data = []

    async def mock_post(self, url, **kwargs):
        captured_data.append((kwargs["json"]["text"], kwargs["json"]["language"]))
        return httpx.Response(200, content=b"audio")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    test_cases = [
        ("Hello world", "en"),
        ("Hola mundo", "es"),
        ("Bonjour le monde", "fr"),
        ("Hallo Welt", "de"),
        ("Ciao mondo", "it"),
    ]

    with runner.isolated_filesystem():
        for text, lang in test_cases:
            result = runner.invoke(
                cli,
                ["speak", text, "-o", f"{lang}.mp3", "--lang", lang],
                env={"XAI_API_KEY": "test-key"},
            )
            assert result.exit_code == 0

    # Verify all languages were used
    assert len(captured_data) == len(test_cases)
    for (text, lang), (cap_text, cap_lang) in zip(test_cases, captured_data, strict=False):
        assert cap_text == text
        assert cap_lang == lang
