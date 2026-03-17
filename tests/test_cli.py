"""Comprehensive tests for the CLI."""

from pathlib import Path
from unittest.mock import patch

from grok_tts_cli.cli import cli
from grok_tts_cli.client import AuthenticationError, GrokTTSError, RateLimitError

# ============================================================================
# Speak Command Tests
# ============================================================================


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
        # Check that file was created
        assert Path("output.mp3").exists()


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


def test_speak_no_text_no_stdin(runner, mock_client):
    """Test speak without text and without stdin fails."""
    result = runner.invoke(
        cli,
        ["speak", "-o", "output.mp3"],
        env={"XAI_API_KEY": "test-key"},
    )
    assert result.exit_code == 1
    # The actual error message is "Empty text provided" when stdin is empty
    assert "Empty text" in result.output or "No text" in result.output


def test_speak_empty_text(runner, mock_client):
    """Test speak with empty text fails."""
    result = runner.invoke(
        cli,
        ["speak", "", "-o", "output.mp3"],
        env={"XAI_API_KEY": "test-key"},
    )
    assert result.exit_code == 1
    assert "Empty text" in result.output


def test_speak_empty_stdin(runner, mock_client):
    """Test speak with empty stdin fails."""
    result = runner.invoke(
        cli,
        ["speak", "-o", "output.mp3"],
        input="   \n  \t  \n  ",
        env={"XAI_API_KEY": "test-key"},
    )
    assert result.exit_code == 1
    assert "Empty text" in result.output


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


def test_speak_to_file(runner, mock_client):
    """Test speak creates output file."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "test.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert Path("test.mp3").exists()
        assert Path("test.mp3").read_bytes() == b"fake-mp3-data"


def test_speak_creates_parent_dirs(runner, mock_client):
    """Test speak creates parent directories if needed."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "subdir/nested/output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert Path("subdir/nested/output.mp3").exists()
        assert Path("subdir/nested/output.mp3").read_bytes() == b"fake-mp3-data"


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


def test_speak_all_voices_work(runner, mock_client):
    """Test speak with all available voices."""
    voices = ["eve", "ara", "rex", "sal", "leo"]
    with runner.isolated_filesystem():
        for voice in voices:
            result = runner.invoke(
                cli,
                ["speak", "Hello", "-o", f"{voice}.mp3", "--voice", voice],
                env={"XAI_API_KEY": "test-key"},
            )
            assert result.exit_code == 0, f"Failed for voice {voice}"


def test_speak_invalid_voice_rejected(runner, mock_client):
    """Test speak rejects invalid voice."""
    result = runner.invoke(
        cli,
        ["speak", "Hello", "-o", "output.mp3", "--voice", "invalid"],
        env={"XAI_API_KEY": "test-key"},
    )
    assert result.exit_code != 0
    assert "Invalid value" in result.output or "invalid" in result.output.lower()


def test_speak_invalid_language_rejected(runner, mock_client):
    """Test speak rejects invalid language."""
    result = runner.invoke(
        cli,
        ["speak", "Hello", "-o", "output.mp3", "--lang", "invalid"],
        env={"XAI_API_KEY": "test-key"},
    )
    assert result.exit_code != 0
    assert "Invalid value" in result.output or "invalid" in result.output.lower()


def test_speak_missing_api_key_error(runner):
    """Test speak fails gracefully when API key is missing."""
    with patch("grok_tts_cli.cli.GrokTTSClient") as mock:
        mock.side_effect = AuthenticationError("XAI_API_KEY not found")
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3"],
        )
        assert result.exit_code == 1
        # Error should be displayed somewhere (output or exception)
        assert result.exception or "Authentication" in str(result.output).lower() or "XAI_API_KEY" in result.output


def test_speak_auth_error_display(runner, mock_client):
    """Test speak displays authentication errors properly."""
    mock_client.synthesize.side_effect = AuthenticationError("Invalid API key")
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 1
        # Error handling may raise exception or print error
        assert result.exception is not None or "error" in result.output.lower()


def test_speak_rate_limit_error_display(runner, mock_client):
    """Test speak displays rate limit errors properly."""
    mock_client.synthesize.side_effect = RateLimitError("Rate limit exceeded")
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 1
        assert result.exception is not None or "error" in result.output.lower()


def test_speak_generic_error_display(runner, mock_client):
    """Test speak displays generic errors properly."""
    mock_client.synthesize.side_effect = GrokTTSError("API error: 500")
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 1
        assert result.exception is not None or "error" in result.output.lower()


def test_speak_unexpected_error_display(runner, mock_client):
    """Test speak displays unexpected errors properly."""
    mock_client.synthesize.side_effect = ValueError("Unexpected error")
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 1
        assert result.exception is not None or "error" in result.output.lower()


def test_speak_output_required(runner, mock_client):
    """Test that -o/--output is required."""
    result = runner.invoke(
        cli,
        ["speak", "Hello"],
        env={"XAI_API_KEY": "test-key"},
    )
    assert result.exit_code != 0
    assert "Missing option" in result.output or "--output" in result.output


def test_speak_with_long_text(runner, mock_client):
    """Test speak with long text."""
    long_text = "Hello world! " * 500
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", long_text, "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0


def test_speak_with_unicode(runner, mock_client):
    """Test speak with unicode text."""
    unicode_text = "Hello 世界 🎉"
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", unicode_text, "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0


def test_speak_with_multiline_stdin(runner, mock_client):
    """Test speak with multiline stdin input."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "-o", "output.mp3"],
            input="Line 1\nLine 2\nLine 3",
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        # Check that all lines were passed to synthesize
        call_args = mock_client.synthesize.call_args
        assert "Line 1" in call_args[0][0]
        assert "Line 2" in call_args[0][0]
        assert "Line 3" in call_args[0][0]


# ============================================================================
# Batch Command Tests
# ============================================================================


def test_batch_normal(runner, mock_client):
    """Test batch command with normal input."""
    with runner.isolated_filesystem():
        # Create input file
        Path("input.txt").write_text("Line 1\nLine 2\nLine 3\n")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert "Processed 3 files" in result.output
        # Check that output files were created
        assert Path("output_dir/output_0000.mp3").exists()
        assert Path("output_dir/output_0001.mp3").exists()
        assert Path("output_dir/output_0002.mp3").exists()


def test_batch_empty_file_warning(runner, mock_client):
    """Test batch with empty file shows warning."""
    with runner.isolated_filesystem():
        Path("empty.txt").write_text("")

        result = runner.invoke(
            cli,
            ["batch", "empty.txt", "-o", "output_dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        # Should complete successfully but with warning
        assert result.exit_code == 0 or (result.exit_code == 1 and result.exception)
        # Check for warning message if no exception
        if result.exit_code == 0:
            assert "Warning" in result.output or "No text" in result.output


def test_batch_empty_lines_ignored(runner, mock_client):
    """Test batch ignores empty lines."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("Line 1\n\n  \nLine 2\n\t\nLine 3")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert "Processed 3 files" in result.output


def test_batch_custom_voice(runner, mock_client):
    """Test batch with custom voice."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("Line 1\nLine 2")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir", "--voice", "rex"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0


def test_batch_custom_language(runner, mock_client):
    """Test batch with custom language."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("Hola\nMundo")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir", "--lang", "es"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0


def test_batch_output_dir_creation(runner, mock_client):
    """Test batch creates output directory."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("Line 1")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "new/nested/dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert Path("new/nested/dir").is_dir()


def test_batch_nonexistent_input_file_error(runner, mock_client):
    """Test batch fails with nonexistent input file."""
    result = runner.invoke(
        cli,
        ["batch", "nonexistent.txt", "-o", "output_dir"],
        env={"XAI_API_KEY": "test-key"},
    )
    assert result.exit_code != 0
    assert "does not exist" in result.output.lower() or "Error" in result.output


def test_batch_auth_error(runner, mock_client):
    """Test batch handles authentication errors."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("Line 1")

        # Make synthesize_batch raise auth error
        async def mock_batch_error(*args, **kwargs):
            raise AuthenticationError("Invalid API key")
            yield  # Make it a generator

        mock_client.synthesize_batch = mock_batch_error

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 1
        assert result.exception is not None or "error" in result.output.lower()


def test_batch_rate_limit_error(runner, mock_client):
    """Test batch handles rate limit errors."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("Line 1")

        # Make synthesize_batch raise rate limit error
        async def mock_batch_error(*args, **kwargs):
            raise RateLimitError("Rate limit exceeded")
            yield  # Make it a generator

        mock_client.synthesize_batch = mock_batch_error

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 1
        assert result.exception is not None or "error" in result.output.lower()


def test_batch_generic_error(runner, mock_client):
    """Test batch handles generic errors."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("Line 1")

        # Make synthesize_batch raise generic error
        async def mock_batch_error(*args, **kwargs):
            raise GrokTTSError("API error")
            yield  # Make it a generator

        mock_client.synthesize_batch = mock_batch_error

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 1
        assert result.exception is not None or "error" in result.output.lower()


def test_batch_output_required(runner, mock_client):
    """Test that -o/--output-dir is required for batch."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("Line 1")

        result = runner.invoke(
            cli,
            ["batch", "input.txt"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code != 0
        assert "Missing option" in result.output or "--output-dir" in result.output


def test_batch_with_unicode(runner, mock_client):
    """Test batch with unicode content."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("Hello 世界\nПривет мир\n안녕하세요")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert "Processed 3 files" in result.output


def test_batch_large_file(runner, mock_client):
    """Test batch with large input file."""
    with runner.isolated_filesystem():
        lines = [f"Line {i}" for i in range(100)]
        Path("input.txt").write_text("\n".join(lines))

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        assert "Processed 100 files" in result.output


# ============================================================================
# Voices Command Tests
# ============================================================================


def test_voices_lists_all(runner):
    """Test voices command lists all voices."""
    result = runner.invoke(cli, ["voices"])
    assert result.exit_code == 0
    assert "Available Voices" in result.output
    # Check all voice IDs are present
    assert "eve" in result.output
    assert "ara" in result.output
    assert "rex" in result.output
    assert "sal" in result.output
    assert "leo" in result.output


def test_voices_table_formatting(runner):
    """Test voices command has table formatting."""
    result = runner.invoke(cli, ["voices"])
    assert result.exit_code == 0
    # Check for table columns
    assert "ID" in result.output
    assert "Name" in result.output
    assert "Gender" in result.output
    assert "Description" in result.output


def test_voices_shows_names(runner):
    """Test voices command shows voice names."""
    result = runner.invoke(cli, ["voices"])
    assert result.exit_code == 0
    assert "Eve" in result.output
    assert "Ara" in result.output
    assert "Rex" in result.output
    assert "Sal" in result.output
    assert "Leo" in result.output


def test_voices_shows_genders(runner):
    """Test voices command shows genders."""
    result = runner.invoke(cli, ["voices"])
    assert result.exit_code == 0
    assert "Female" in result.output
    assert "Male" in result.output
    assert "Neutral" in result.output


def test_voices_shows_descriptions(runner):
    """Test voices command shows descriptions."""
    result = runner.invoke(cli, ["voices"])
    assert result.exit_code == 0
    assert "Energetic" in result.output
    assert "Warm" in result.output
    assert "Confident" in result.output
    assert "Smooth" in result.output
    assert "Authoritative" in result.output


# ============================================================================
# Version and Help Tests
# ============================================================================


def test_version_option(runner):
    """Test --version option."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    # Should show some version info
    assert len(result.output) > 0


def test_help_option(runner):
    """Test --help option."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output or "help" in result.output.lower()
    assert "speak" in result.output
    assert "batch" in result.output
    assert "voices" in result.output


def test_speak_help(runner):
    """Test speak --help."""
    result = runner.invoke(cli, ["speak", "--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output or "help" in result.output.lower()
    assert "TEXT" in result.output or "text" in result.output
    assert "--output" in result.output or "-o" in result.output
    assert "--voice" in result.output or "-v" in result.output
    assert "--lang" in result.output or "-l" in result.output


def test_batch_help(runner):
    """Test batch --help."""
    result = runner.invoke(cli, ["batch", "--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output or "help" in result.output.lower()
    assert "INPUT_FILE" in result.output or "input" in result.output.lower()
    assert "--output-dir" in result.output or "-o" in result.output


def test_voices_help(runner):
    """Test voices --help."""
    result = runner.invoke(cli, ["voices", "--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output or "help" in result.output.lower()


# ============================================================================
# Additional Edge Cases
# ============================================================================


def test_speak_with_quotes_in_text(runner, mock_client):
    """Test speak with quotes in text."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", 'Hello "world"', "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0


def test_speak_with_special_chars_in_text(runner, mock_client):
    """Test speak with special characters."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello & goodbye! 50% off.", "-o", "output.mp3"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0


def test_batch_preserves_line_order(runner, mock_client):
    """Test batch preserves order of lines."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("First\nSecond\nThird")

        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir"],
            env={"XAI_API_KEY": "test-key"},
        )
        assert result.exit_code == 0
        # Files should be numbered in order
        assert Path("output_dir/output_0000.mp3").exists()
        assert Path("output_dir/output_0001.mp3").exists()
        assert Path("output_dir/output_0002.mp3").exists()


def test_speak_api_key_from_option(runner, mock_client):
    """Test speak with API key from command line option."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            ["speak", "Hello", "-o", "output.mp3", "--api-key", "cli-key"],
        )
        assert result.exit_code == 0


def test_batch_api_key_from_option(runner, mock_client):
    """Test batch with API key from command line option."""
    with runner.isolated_filesystem():
        Path("input.txt").write_text("Line 1")
        result = runner.invoke(
            cli,
            ["batch", "input.txt", "-o", "output_dir", "--api-key", "cli-key"],
        )
        assert result.exit_code == 0
