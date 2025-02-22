import asyncio
import io
import logging
import sys
import wave
from pathlib import Path

import dotenv
import numpy as np
import pyaudio
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment

from utils.action_handling import ActionHandler
from utils.function_calling_utils import FunctionCaller
from utils.logging_config import setup_logging
from utils.STT_utils import AudioTranscriptionHandler

# Initialize logging with DEBUG level
setup_logging(log_file=Path("logs/test_local.log"), log_level="INFO")
logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()


class AudioStreamer:
    def __init__(self):
        self.CHUNK = 4096
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 16000

        try:
            self.p = pyaudio.PyAudio()
            logger.info("PyAudio initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PyAudio: {e}")
            raise

        # Initialize handlers
        self.transcription_handler = AudioTranscriptionHandler()
        self.function_caller = FunctionCaller()
        self.action_handler = ActionHandler()

        logger.info("AudioStreamer initialized")

    def get_input_device(self):
        """Helper function to list and select audio input devices"""
        logger.info("\nAvailable audio input devices:")
        input_device_index = 2

        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if device_info["maxInputChannels"] > 0:  # if it's an input device
                logger.info(f"Index {i}: {device_info['name']}")
                print(f"Index {i}: {device_info['name']}")  # Also print to console for visibility

        #         # On Mac, prefer devices with "Built-in Microphone" or "MacBook Microphone"
        #         if any(
        #             name in device_info["name"]
        #             for name in ["Built-in Microphone", "MacBook Microphone"]
        #         ):
        #             input_device_index = i

        if input_device_index is None:
            input_device_index = 0  # Default to first device if no preferred device found

        selected_device = self.p.get_device_info_by_index(input_device_index)
        logger.info(
            f"Selected input device: {selected_device['name']} (Index: {input_device_index})"
        )
        print(f"\nUsing input device: {selected_device['name']} (Index: {input_device_index})")

        return input_device_index

    async def process_audio(self):
        logger.info("Starting audio processing")

        input_device_index = self.get_input_device()

        try:
            stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=self.CHUNK,
            )
            logger.info("Audio stream opened successfully")
            print("\nListening... (Press Ctrl+C to stop)")

        except Exception as e:
            logger.error(f"Failed to open audio stream: {e}")
            print(f"Error: Failed to open audio stream: {e}")
            return

        try:
            while True:
                try:
                    # Read audio data
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    audio_data_int16 = (audio_data * 32767).astype(np.int16)
                    audio_bytes = audio_data_int16.tobytes()

                    # Process the audio chunk
                    is_active, text, context = await self.transcription_handler.process_audio_chunk(
                        audio_bytes
                    )

                    # If we just became active (trigger word detected)
                    if is_active and "hey steve" in context.lower():
                        # Extract the command part after "hey steve"
                        command = context.lower().split("hey steve")[-1].strip()
                        if command:  # If there's a command after "hey steve"
                            logger.info(f"Processing command from context: {command}")
                            print(f"\n🎤 Processing command: {command}")

                            # Process the command
                            action_type, details = await self.function_caller.determine_action(
                                command, context
                            )
                            logger.info(f"Determined action: {action_type}")
                            logger.info(f"Action details: {details}")
                            print(f"\n🤖 Determined action: {action_type.value}")
                            print(f"Details: {details}")

                            action_response = await self.action_handler.process_action(
                                action_type, command, details
                            )
                            logger.info(f"Action response: {action_response}")
                            print(f"\n💬 Response: {action_response}")

                            if action_response.get("type") == "audio":
                                print("\n🔊 Would play audio response...")
                                self.play_audio_response(action_response["content"])

                            print("\n✨ Action completed. Resetting listening state...")
                            self.transcription_handler.reset_listening_state()

                    # Handle subsequent commands while active
                    elif is_active and text:
                        logger.info(f"Transcribed text: {text}")
                        print(f"\n🎤 Transcribed: {text}")

                        logger.info("\n\n\n\nTrigger word detected, processing action...")
                        logger.info(f"---\nIs active: {is_active}")
                        logger.info(f"Text: {text}")
                        logger.info(f"Full context: {context}\n\n")

                        # Pass both text and context to determine_action
                        action_type, details = await self.function_caller.determine_action(
                            text, context
                        )
                        logger.info(f"Determined action: {action_type}")
                        logger.info(f"Action details: {details}")
                        print(f"\n🤖 Determined action: {action_type.value}")
                        print(f"Details: {details}")

                        action_response = await self.action_handler.process_action(
                            action_type, text, details
                        )
                        logger.info(f"Action response: {action_response}")
                        print(f"\n💬 Response: {action_response}")

                        if action_response.get("type") == "audio":
                            print("\n🔊 Would play audio response...")
                            # self.play_audio_response(action_response["content"])

                        print("\n✨ Action completed. Resetting listening state...")
                        self.transcription_handler.reset_listening_state()

                    await asyncio.sleep(0.01)

                except IOError as e:
                    logger.error(f"IOError during audio processing: {e}")
                    print(f"Audio Error: {e}")
                    break

        except KeyboardInterrupt:
            logger.info("Stopping audio capture...")
            print("\nStopping audio capture...")
        except Exception as e:
            logger.exception(f"Error in audio processing: {e}")
            print(f"Error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            await self.transcription_handler.close()
            self.p.terminate()
            logger.info("Audio capture stopped")
            print("Audio capture stopped")

    def play_audio_response(self, audio_bytes):
        """Play MP3 audio response through speakers"""
        try:
            # Convert MP3 bytes to numpy array using pydub
            audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            samples = np.array(audio.get_array_of_samples())

            # Convert to float32 normalized between -1 and 1
            samples = samples.astype(np.float32) / (2**15)

            # Play the audio
            sd.play(samples, audio.frame_rate)
            sd.wait()  # Wait until audio is finished playing

            logger.info("Played audio response")

        except Exception as e:
            logger.exception(f"Error playing audio response: {e}")

    async def cleanup(self):
        """Cleanup all resources"""
        try:
            # Close the transcription handler first
            await self.transcription_handler.close()

            # Cleanup PyAudio
            if hasattr(self, "p") and self.p:
                self.p.terminate()
                self.p = None

            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.exception(f"Error during cleanup: {e}")


async def main():
    streamer = None
    try:
        streamer = AudioStreamer()
        await streamer.process_audio()
    except Exception as e:
        logger.exception("Failed to start audio streaming")
        print(f"Error: {e}")
    finally:
        if streamer:
            await streamer.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    print("\nStarting local test... Say 'Hey Steve' to activate!")
    print("Press Ctrl+C to stop\n")

    # Run the async main function
    asyncio.run(main())
