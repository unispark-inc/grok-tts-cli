"""Voice definitions and metadata for Grok TTS."""

from typing import NamedTuple


class Voice(NamedTuple):
    """Voice definition."""

    id: str
    name: str
    gender: str
    description: str


VOICES = [
    Voice("eve", "Eve", "Female", "Energetic"),
    Voice("ara", "Ara", "Female", "Warm"),
    Voice("rex", "Rex", "Male", "Confident"),
    Voice("sal", "Sal", "Neutral", "Smooth"),
    Voice("leo", "Leo", "Male", "Authoritative"),
]

VOICE_IDS = [v.id for v in VOICES]

SUPPORTED_LANGUAGES = [
    "en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "tr",
    "zh", "ja", "ko", "ar", "hi", "id", "ms", "th", "vi", "fil"
]


def get_voice(voice_id: str) -> Voice | None:
    """Get voice by ID."""
    for voice in VOICES:
        if voice.id == voice_id:
            return voice
    return None
