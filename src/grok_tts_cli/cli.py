"""Command-line interface for Grok TTS."""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .client import AuthenticationError, GrokTTSClient, GrokTTSError, RateLimitError
from .voices import SUPPORTED_LANGUAGES, VOICE_IDS, VOICES

console = Console()


@click.group()
@click.version_option()
def cli():
    """Grok TTS CLI - Generate speech from text using xAI's Grok TTS API."""
    pass


@cli.command()
@click.argument("text", required=False)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    required=True,
    help="Output file path (use '-' for stdout)",
)
@click.option(
    "-v",
    "--voice",
    type=click.Choice(VOICE_IDS),
    default="eve",
    help="Voice ID",
)
@click.option(
    "-l",
    "--lang",
    type=click.Choice(SUPPORTED_LANGUAGES),
    default="en",
    help="Language code",
)
@click.option(
    "--api-key",
    envvar="XAI_API_KEY",
    help="xAI API key (or set XAI_API_KEY env var)",
)
def speak(text, output, voice, lang, api_key):
    """
    Convert text to speech.

    TEXT: Text to synthesize. If not provided, reads from stdin.

    Examples:

    \b
    # Basic usage
    grok-tts speak "Hello world" -o hello.mp3

    \b
    # Choose voice and language
    grok-tts speak --voice rex --lang es -o output.mp3 "Hola mundo"

    \b
    # Pipe to audio player
    grok-tts speak "Hello" -o - | ffplay -nodisp -autoexit -

    \b
    # Read from stdin
    echo "Hello from stdin" | grok-tts speak -o output.mp3
    """
    # Get text from argument or stdin
    if text is None:
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            click.echo("Error: No text provided. Provide text as argument or via stdin.", err=True)
            sys.exit(1)

    if not text:
        click.echo("Error: Empty text provided.", err=True)
        sys.exit(1)

    try:
        client = GrokTTSClient(api_key)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Synthesizing with {voice}...", total=None)

            # Run async synthesis
            audio_data = asyncio.run(client.synthesize(text, voice, lang))

            progress.update(task, completed=True)

        # Write output
        if output == "-":
            sys.stdout.buffer.write(audio_data)
        else:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(audio_data)
            console.print(f"[green]✓[/green] Saved to {output}")

    except AuthenticationError as e:
        console.print(f"[red]Authentication error:[/red] {e}", err=True)
        sys.exit(1)
    except RateLimitError as e:
        console.print(f"[red]Rate limit exceeded:[/red] {e}", err=True)
        sys.exit(1)
    except GrokTTSError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(),
    required=True,
    help="Output directory for generated audio files",
)
@click.option(
    "-v",
    "--voice",
    type=click.Choice(VOICE_IDS),
    default="eve",
    help="Voice ID",
)
@click.option(
    "-l",
    "--lang",
    type=click.Choice(SUPPORTED_LANGUAGES),
    default="en",
    help="Language code",
)
@click.option(
    "--api-key",
    envvar="XAI_API_KEY",
    help="xAI API key (or set XAI_API_KEY env var)",
)
def batch(input_file, output_dir, voice, lang, api_key):
    """
    Convert multiple lines of text to speech.

    INPUT_FILE: Text file with one line per audio file.

    Examples:

    \b
    # Process each line in input.txt
    grok-tts batch input.txt -o output_dir/

    \b
    # With custom voice
    grok-tts batch input.txt -o output_dir/ --voice rex
    """
    try:
        # Read input file
        input_path = Path(input_file)
        lines = [line.strip() for line in input_path.read_text().splitlines() if line.strip()]

        if not lines:
            console.print("[yellow]Warning:[/yellow] No text found in input file.", err=True)
            return

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        client = GrokTTSClient(api_key)

        with Progress(console=console) as progress:
            task = progress.add_task(f"Processing {len(lines)} lines...", total=len(lines))

            async def process_batch():
                async for i, audio_data in client.synthesize_batch(lines, voice, lang):
                    output_file = output_path / f"output_{i:04d}.mp3"
                    output_file.write_bytes(audio_data)
                    progress.update(task, advance=1)

            asyncio.run(process_batch())

        console.print(f"[green]✓[/green] Processed {len(lines)} files to {output_dir}")

    except AuthenticationError as e:
        console.print(f"[red]Authentication error:[/red] {e}", err=True)
        sys.exit(1)
    except RateLimitError as e:
        console.print(f"[red]Rate limit exceeded:[/red] {e}", err=True)
        sys.exit(1)
    except GrokTTSError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", err=True)
        sys.exit(1)


@cli.command()
def voices():
    """List available voices."""
    table = Table(title="Available Voices")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Gender", style="green")
    table.add_column("Description", style="yellow")

    for voice in VOICES:
        table.add_row(voice.id, voice.name, voice.gender, voice.description)

    console.print(table)


if __name__ == "__main__":
    cli()
