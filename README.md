# grok-tts-cli

[![PyPI version](https://badge.fury.io/py/grok-tts-cli.svg)](https://badge.fury.io/py/grok-tts-cli)
[![CI](https://github.com/unispark-inc/grok-tts-cli/workflows/CI/badge.svg)](https://github.com/unispark-inc/grok-tts-cli/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A command-line interface for [xAI's Grok TTS API](https://docs.x.ai/). Convert text to speech with multiple voices, languages, and advanced prosodic controls.

## Features

- Multiple high-quality voices (Eve, Ara, Rex, Sal, Leo)
- 20+ language support
- Batch processing for multiple texts
- Stdin/stdout piping for integration with other tools
- Rich CLI with progress bars and formatted output
- Async HTTP client with retry logic

## Installation

```bash
pip install grok-tts-cli
```

## Quick Start

First, set your xAI API key:

```bash
export XAI_API_KEY="your-api-key-here"
```

Generate speech from text:

```bash
grok-tts speak "Hello, world!" -o hello.mp3
```

## Usage

### Basic Speech Generation

```bash
# Simple text-to-speech
grok-tts speak "Welcome to Grok TTS" -o welcome.mp3

# Choose a voice
grok-tts speak --voice rex "I am Rex" -o rex.mp3

# Specify language
grok-tts speak --lang es "Hola mundo" -o hola.mp3
```

### Piping and Streaming

Pipe output to audio players:

```bash
# Play immediately with ffplay
grok-tts speak "Hello" -o - | ffplay -nodisp -autoexit -

# Or with mpv
grok-tts speak "Hello" -o - | mpv -
```

Read from stdin:

```bash
# From echo
echo "Hello from stdin" | grok-tts speak -o output.mp3

# From file
cat script.txt | grok-tts speak -o narration.mp3

# Chain commands
curl -s https://api.example.com/quote | jq -r '.text' | grok-tts speak -o quote.mp3
```

### Batch Processing

Process multiple lines of text:

```bash
# Create input file
cat > lines.txt << EOF
Welcome to the first chapter
This is the second line
And here's the third
EOF

# Generate audio for each line
grok-tts batch lines.txt -o audio_output/

# With custom voice
grok-tts batch lines.txt -o audio_output/ --voice ara --lang en
```

Output files will be named `output_0000.mp3`, `output_0001.mp3`, etc.

### List Available Voices

```bash
grok-tts voices
```

### Available Voices

| ID  | Name | Gender  | Description    |
|-----|------|---------|----------------|
| eve | Eve  | Female  | Energetic      |
| ara | Ara  | Female  | Warm           |
| rex | Rex  | Male    | Confident      |
| sal | Sal  | Neutral | Smooth         |
| leo | Leo  | Male    | Authoritative  |

### Prosodic Controls

Grok TTS supports special tags for advanced speech control:

```bash
# Pauses
grok-tts speak "Hello [pause] world" -o pause.mp3

# Laughter
grok-tts speak "That's funny [laugh]" -o laugh.mp3

# Whisper
grok-tts speak "<whisper>This is a secret</whisper>" -o whisper.mp3
```

### Supported Languages

`en`, `es`, `fr`, `de`, `it`, `pt`, `nl`, `pl`, `ru`, `tr`, `zh`, `ja`, `ko`, `ar`, `hi`, `id`, `ms`, `th`, `vi`, `fil`

## CLI Reference

### `grok-tts speak`

Convert text to speech.

```
Usage: grok-tts speak [OPTIONS] [TEXT]

Options:
  -o, --output PATH       Output file path (use '-' for stdout)  [required]
  -v, --voice [eve|ara|rex|sal|leo]
                          Voice ID  [default: eve]
  -l, --lang [en|es|fr|de|it|pt|nl|pl|ru|tr|zh|ja|ko|ar|hi|id|ms|th|vi|fil]
                          Language code  [default: en]
  --api-key TEXT          xAI API key (or set XAI_API_KEY env var)
  --help                  Show this message and exit.
```

### `grok-tts batch`

Convert multiple lines of text to speech.

```
Usage: grok-tts batch [OPTIONS] INPUT_FILE

Options:
  -o, --output-dir PATH   Output directory  [required]
  -v, --voice [eve|ara|rex|sal|leo]
                          Voice ID  [default: eve]
  -l, --lang [en|es|fr|de|it|pt|nl|pl|ru|tr|zh|ja|ko|ar|hi|id|ms|th|vi|fil]
                          Language code  [default: en]
  --api-key TEXT          xAI API key (or set XAI_API_KEY env var)
  --help                  Show this message and exit.
```

### `grok-tts voices`

List available voices.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/unispark-inc/grok-tts-cli.git
cd grok-tts-cli

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=grok_tts_cli

# Run linting
ruff check src/ tests/
```

### Project Structure

```
grok-tts-cli/
├── src/
│   └── grok_tts_cli/
│       ├── __init__.py
│       ├── __main__.py      # python -m support
│       ├── cli.py            # Click commands
│       ├── client.py         # TTS API client
│       └── voices.py         # Voice definitions
├── tests/
│   ├── test_cli.py
│   └── test_client.py
├── .github/
│   └── workflows/
│       └── ci.yml
└── pyproject.toml
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/)
- HTTP client: [httpx](https://www.python-httpx.org/)
- Terminal UI: [Rich](https://rich.readthedocs.io/)
- Powered by [xAI's Grok TTS API](https://docs.x.ai/)

## Links

- [GitHub Repository](https://github.com/unispark-inc/grok-tts-cli)
- [Issue Tracker](https://github.com/unispark-inc/grok-tts-cli/issues)
- [xAI Documentation](https://docs.x.ai/)
