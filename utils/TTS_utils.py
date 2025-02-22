import os
from typing import Optional

import httpx


async def stream_to_elevenlabs(text: str, voice_id: Optional[str] = None) -> bytes:
    """
    Stream text to ElevenLabs and get audio response
    """
    # TODO: Implement actual streaming to ElevenLabs
    # This is a placeholder implementation
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    voice_id = voice_id or "default_voice_id"

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

    headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": api_key}

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        return response.content
