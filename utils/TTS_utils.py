import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


async def stream_to_elevenlabs(text: str, voice_id: Optional[str] = None) -> bytes:
    """
    Stream text to ElevenLabs and get audio response
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("ELEVENLABS_API_KEY not found in environment variables")
        raise ValueError("ELEVENLABS_API_KEY not found in environment variables")

    voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"
    logger.info(f"Streaming text to ElevenLabs using voice_id: {voice_id}")
    logger.debug(f"Text content: {text[:100]}...")  # Log first 100 chars of text

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": api_key}
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
    }

    async with httpx.AsyncClient() as client:
        logger.debug("Sending request to ElevenLabs API")
        response = await client.post(url, json=data, headers=headers)
        logger.info(f"ElevenLabs API Response Status: {response.status_code}")

        if response.status_code == 400:
            error_detail = response.json()
            logger.error(f"Bad Request Error: {error_detail}")
            raise ValueError(f"ElevenLabs API Error: {error_detail}")

        response.raise_for_status()
        logger.debug("Successfully received audio response")
        return response.content


if __name__ == "__main__":
    # Set up logging for the test
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    import dotenv

    dotenv.load_dotenv()
    import asyncio

    async def test_tts():
        text = "The quick brown fox jumps over the lazy dog. But the dog wasn't actually lazy - it was plotting world domination while taking a strategic nap."
        logger.info("Starting TTS test")
        try:
            audio_data = await stream_to_elevenlabs(text)
            with open("test_output.mp3", "wb") as f:
                f.write(audio_data)
            logger.info("Test audio saved to 'test_output.mp3'")
        except Exception as e:
            logger.exception("Error during TTS test")
            raise

    # Run the test
    asyncio.run(test_tts())
