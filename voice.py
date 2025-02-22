import asyncio
import os
from elevenlabs import ElevenLabs

async def generate_voice_message(text: str):
    elevenlabs = ElevenLabs(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
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


