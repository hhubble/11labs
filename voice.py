import asyncio
import os
from elevenlabs import ElevenLabs

# Set API Keys
ELEVENLABS_API_KEY = "your_elevenlabs_api_key"

async def generate_voice_message(text: str):
    elevenlabs = ElevenLabs(
        api_key=ELEVENLABS_API_KEY,
    )

    voice_id = "21m00Tcm4TlvDq8ikWAM"

    response = elevenlabs.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
    )

    with open("output.mp3", "wb") as f:
        f.write(response)
        
if __name__ == "__main__":
    asyncio.run(generate_voice_message("Hello, world!"))

