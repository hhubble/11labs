import io
import logging
import os
from typing import Optional

import httpx
import numpy as np
import sounddevice as sd
from pydub import AudioSegment

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
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5, "speed": 1.2},
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


async def handle_audio_output(
    audio_data: bytes, output_mode: str = "speak", output_file: str = None
):
    """
    Handle audio output either by speaking it or saving to file
    Args:
        audio_data: Raw MP3 bytes from ElevenLabs
        output_mode: Either "speak" or "save"
        output_file: Path to save the file (required if output_mode is "save")
    """
    if output_mode == "speak":
        logger.debug("Converting audio format")
        # Convert MP3 bytes to AudioSegment
        audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))
        # Convert to raw PCM audio data
        samples = audio_segment.get_array_of_samples()
        # Convert to numpy array and ensure correct data type
        audio_array = np.array(samples, dtype=np.float32) / 32768.0  # Normalize to [-1.0, 1.0]

        # Start playing immediately
        logger.info("Playing audio through speakers")
        sd.play(audio_array, samplerate=audio_segment.frame_rate, blocking=False)
        sd.wait()
        logger.info("Finished playing audio")
    elif output_mode == "save":
        if not output_file:
            raise ValueError("output_file must be specified when output_mode is 'save'")
        logger.info(f"Saving audio to {output_file}")
        with open(output_file, "wb") as f:
            f.write(audio_data)
        logger.info("Audio file saved successfully")
    else:
        raise ValueError("output_mode must be either 'speak' or 'save'")


async def handle_audio_to_microphone(audio_data: bytes, device_name: str = "MacBook Pro Microphone") -> None:
    """
    Stream audio to a specific microphone device
    Args:
        audio_data: Raw MP3 bytes from ElevenLabs
        device_name: Name of the virtual microphone device to use. If None, will attempt to auto-detect.
    Raises:
        ValueError: If no suitable microphone device is found
    """
    # list devices:
    devices = sd.query_devices()

    logger.debug("Converting audio format")
    # Convert MP3 bytes to AudioSegment
    audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))
    # Convert to raw PCM audio data
    samples = audio_segment.get_array_of_samples()
    # Convert to numpy array and ensure correct data type
    audio_array = np.array(samples, dtype=np.float32) / 32768.0  # Normalize to [-1.0, 1.0]

    # Find virtual microphone device
    devices = sd.query_devices()
    logger.debug(f"Available audio devices: {devices}")

    # Look for a virtual microphone device
    virtual_mic = None
    if device_name:
        # If device name is specified, look for exact match
        for i, device in enumerate(devices):
            if device_name.lower() in device["name"].lower():
                virtual_mic = i
                break
    else:
        # Auto-detect virtual microphone
        for i, device in enumerate(devices):
            print("DEVICE: ", device)
            if (
                "mic" in device["name"].lower()
                or "virtual" in device["name"].lower()
                or "loopback" in device["name"].lower()
            ):
                virtual_mic = i
                break

    if virtual_mic is None:
        available_devices = "\n".join([f"{i}: {d['name']}" for i, d in enumerate(devices)])
        raise ValueError(
            f"Could not find a suitable microphone device. Available devices:\n{available_devices}"
        )

    logger.info(f"Using audio device: {devices[virtual_mic]['name']}")

    # Start playing to virtual microphone
    logger.info("Streaming audio to virtual microphone")
    try:
        sd.play(
            audio_array, samplerate=audio_segment.frame_rate, device=virtual_mic, blocking=False
        )
        sd.wait()  # Wait until audio is finished playing
        logger.info("Finished streaming audio")
    except sd.PortAudioError as e:
        logger.error(f"Error streaming to audio device: {e}")
        raise


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
            await handle_audio_output(audio_data, output_mode="speak")

        except Exception as e:
            logger.exception("Error during TTS test")
            raise

    # Run the test
