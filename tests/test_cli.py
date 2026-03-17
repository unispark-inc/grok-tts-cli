"""Tests for the CLI."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from grok_tts_cli.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_client():
    """Create a mock TTS client."""
    with patch("grok_tts_cli.cli.GrokTTSClient") as mock:
        instance = MagicMock()
        instance.synthesize = AsyncMock(return_value=b"fake-mp3-data")
        instance.synthesize_batch = AsyncMock()
        mock.return_value = instance
        yield instance


def test_speak_with_text_argument(runner, mock_client):
    """Test speak command with text argument."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello world", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert "Saved to output.mp3" in result.output
        mock_client.synthesize.assert_called_once()


def test_speak_with_stdin(runner, mock_client):
    """Test speak command with stdin input."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "-o", "output.mp3"],
            input="Hello from stdin",
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        mock_client.synthesize.assert_called_once()


def test_speak_with_custom_voice(runner, mock_client):
    """Test speak with custom voice."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3", "--voice", "rex"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        # Check that synthesize was called with rex voice
        call_args = mock_client.synthesize.call_args
        assert call_args[0][1] == "rex"


def test_speak_with_custom_language(runner, mock_client):
    """Test speak with custom language."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hola", "-o", "output.mp3", "--lang", "es"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        call_args = mock_client.synthesize.call_args
        assert call_args[0][2] == "es"


def test_speak_to_stdout(runner, mock_client):
    """Test speak with stdout output."""
    result = runner.invoke(
        cli,
        ["speak", "Hello", "-o", "-"],
        env={"XAI_API_KEY": "test-key"},
    )
    assert result.exit_code == 0
    # stdout should contain the audio data
    assert b"fake-mp3-data" in result.stdout_bytes


def test_speak_no_text_no_stdin(runner, mock_client):
    """Test speak without text and without stdin fails."""
    result = runner.invoke(
        cli,
        ["speak", "-o", "output.mp3"],
        env={"XAI_API_KEY": "test-key"},
    )
    assert result.exit_code == 1
    assert "No text provided" in result.output


def test_batch_command(runner, mock_client):
    """Test batch command."""
    with runner.isolated_filesystem():
        # Create input file
        with open("input.txt", "w") as f:
            f.write("Line 1\nLine 2\nLine 3\n")

        # Mock async generator
        async def mock_batch_gen():
            for i in range(3):
                yield i, b"fake-mp3-data"

        mock_client.synthesize_batch.return_value = mock_batch_gen()

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert "Processed 3 files" in result.output


def test_voices_command(runner):
    """Test voices command."""
    result = runner.invoke(cli, ["voices"])
    assert result.exit_code == 0
    assert "Available Voices" in result.output
    assert "eve" in result.output
    assert "rex" in result.output
    assert "ara" in result.output


def test_version_option(runner):
    """Test --version option."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
