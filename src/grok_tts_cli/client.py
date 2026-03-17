"""HTTP client for xAI Grok TTS API."""

import asyncio
import os
from collections.abc import AsyncIterator

import httpx


class GrokTTSError(Exception):
    """Base exception for Grok TTS errors."""
    pass


class AuthenticationError(GrokTTSError):
    """Authentication failed."""
    pass


class RateLimitError(GrokTTSError):
    """Rate limit exceeded."""
    pass


class GrokTTSClient:
    """Async HTTP client for Grok TTS API."""

    API_URL = "https://api.x.ai/v1/tts"
    DEFAULT_VOICE = "eve"
    DEFAULT_LANGUAGE = "en"
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def __init__(self, api_key: str | None = None):
        """Initialize client with API key."""
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "XAI_API_KEY not found. Set it via environment variable or pass to constructor."
            )

    async def synthesize(
        self,
        text: str,
        voice_id: str = DEFAULT_VOICE,
        language: str = DEFAULT_LANGUAGE,
    ) -> bytes:
        """
        Synthesize text to speech.

        Args:
            text: Text to synthesize
            voice_id: Voice ID (eve, ara, rex, sal, leo)
            language: Language code (en, es, fr, etc.)

        Returns:
            MP3 audio data as bytes

        Raises:
            AuthenticationError: Invalid API key
            RateLimitError: Rate limit exceeded
            GrokTTSError: Other API errors
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "text": text,
            "voice_id": voice_id,
            "language": language,
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.API_URL,
                        headers=headers,
                        json=payload,
                    )

                    if response.status_code == 401:
                        raise AuthenticationError("Invalid API key")
                    elif response.status_code == 429:
                        raise RateLimitError("Rate limit exceeded")
                    elif response.status_code >= 400:
                        raise GrokTTSError(
                            f"API error: {response.status_code} - {response.text}"
                        )

                    return response.content

            except httpx.TimeoutException:
                if attempt == self.MAX_RETRIES - 1:
                    raise GrokTTSError("Request timed out after retries") from None
                await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))

            except httpx.NetworkError as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise GrokTTSError(f"Network error: {e}") from None
                await asyncio.sleep(self.RETRY_DELAY * (attempt + 1))

        raise GrokTTSError("Max retries exceeded")

    async def synthesize_batch(
        self,
        texts: list[str],
        voice_id: str = DEFAULT_VOICE,
        language: str = DEFAULT_LANGUAGE,
    ) -> AsyncIterator[tuple[int, bytes]]:
        """
        Synthesize multiple texts to speech.

        Args:
            texts: List of texts to synthesize
            voice_id: Voice ID
            language: Language code

        Yields:
            Tuples of (index, audio_data)
        """
        for i, text in enumerate(texts):
            audio_data = await self.synthesize(text, voice_id, language)
            yield i, audio_data
