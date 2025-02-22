import asyncio
import logging
import os

from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

logger = logging.getLogger(__name__)


class AudioTranscriptionHandler:
    def __init__(self, trigger_word="hey steve", buffer_size=5):
        self.deepgram = DeepgramClient(os.environ.get("DEEPGRAM_API_KEY"))
        self.dg_connection = None
        self.is_listening_active = False
        self.current_text = ""
        self.TRIGGER_WORD = trigger_word.lower()
        self.transcription_buffer = []  # Store recent transcriptions
        self.buffer_size = buffer_size  # Number of recent transcriptions to keep
        logger.info("Initialized AudioTranscriptionHandler")

    async def initialize_connection(self):
        try:
            self.dg_connection = self.deepgram.listen.asyncwebsocket.v("1")

            async def on_message(self, result, **kwargs):
                if not hasattr(result, "channel"):
                    return

                # Clean up the transcript: remove punctuation and normalize spaces
                transcript = result.channel.alternatives[0].transcript.lower()
                cleaned_transcript = " ".join(transcript.replace(",", "").replace(".", "").split())
                is_final = result.is_final

                if not cleaned_transcript:
                    return

                logger.debug(f"Received transcript: '{cleaned_transcript}' (is_final: {is_final})")

                if is_final:
                    # Add to buffer and check for trigger
                    self.transcription_buffer.append(cleaned_transcript)
                    # Keep only the last N transcriptions
                    if len(self.transcription_buffer) > self.buffer_size:
                        self.transcription_buffer.pop(0)

                    # Check for trigger word in the combined recent transcriptions
                    buffer_text = " ".join(self.transcription_buffer)
                    print(f"buffer_text: {buffer_text}")
                    if not self.is_listening_active and self.TRIGGER_WORD in buffer_text:
                        logger.info(f"🎯 Trigger word detected in buffer: '{buffer_text}'")
                        print(f"\n🎯 Activated! Heard trigger in: '{buffer_text}'")
                        self.is_listening_active = True
                        self.transcription_buffer.clear()  # Clear buffer after triggering
                    elif self.is_listening_active:
                        logger.info(f"🎤 Final transcription: '{cleaned_transcript}'")
                        print(f"🎤 {cleaned_transcript}")
                        self.current_text = cleaned_transcript

            async def on_open(self, open, **kwargs):
                logger.info("🔌 Deepgram connection opened")
                print("\n🔌 Connected to Deepgram")

            async def on_error(self, error, **kwargs):
                logger.error(f"❌ Deepgram error: {error}")
                print(f"\n❌ Error: {error}")

            # Register all handlers
            self.dg_connection.on(LiveTranscriptionEvents.Open, on_open)
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.dg_connection.on(LiveTranscriptionEvents.Error, on_error)

            options = LiveOptions(
                encoding="linear16",
                sample_rate=16000,
                channels=1,
                model="nova-2",
                language="en",
                smart_format=True,
                interim_results=True,
            )

            if not await self.dg_connection.start(options):
                raise Exception("Failed to start Deepgram connection")

        except Exception as e:
            logger.exception(f"Error initializing Deepgram connection: {e}")
            raise

    async def process_audio_chunk(self, audio_bytes: bytes) -> tuple[bool, str]:
        try:
            if not self.dg_connection:
                await self.initialize_connection()

            await self.dg_connection.send(audio_bytes)

            text = self.current_text
            self.current_text = ""  # Clear the current text
            return self.is_listening_active, text

        except Exception as e:
            logger.exception(f"Error processing audio chunk: {e}")
            return False, ""

    async def close(self):
        if self.dg_connection:
            self.dg_connection.finish()

    def reset_listening_state(self):
        self.is_listening_active = False
        self.current_text = ""
        self.transcription_buffer.clear()  # Clear the buffer when resetting


async def process_audio_to_text(audio_bytes: bytes):
    try:
        deepgram = DeepgramClient(os.environ.get("DEEPGRAM_API_KEY"))
        dg_connection = deepgram.listen.websocket.v("1")
        transcription_result = []

        def on_message(result):  # Fixed function signature
            transcript = (
                result.channel.alternatives[0].transcript if hasattr(result, "channel") else ""
            )
            if transcript:
                logger.debug(f"Received transcription: {transcript}")
                transcription_result.append(transcript)

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        options = LiveOptions(encoding="linear16", sample_rate=16000, channels=1, model="nova-2")

        if not dg_connection.start(options):
            raise Exception("Failed to start Deepgram connection")

        await asyncio.sleep(0.1)  # Ensure connection is ready
        dg_connection.send(audio_bytes)

        dg_connection.finish()

        final_transcript = " ".join(transcription_result)
        return final_transcript

    except Exception as e:
        logger.error(f"Could not process audio: {e}")
        return ""


if __name__ == "__main__":
    URL = "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"

    def stream_bbc_audio():
        try:
            deepgram = DeepgramClient(os.environ.get("DEEPGRAM_API_KEY"))
            dg_connection = deepgram.listen.websocket.v("1")

            def on_message(result):  # Fixed function signature
                if hasattr(result, "channel") and result.channel.alternatives:
                    sentence = result.channel.alternatives[0].transcript
                    if sentence:
                        print(f"Transcript: {sentence}")

            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

            options = LiveOptions(smart_format=True, model="nova-2", language="en-US")
            dg_connection.start(options)

            lock_exit = threading.Lock()
            exit_flag = False  # Renamed to avoid conflict with Python's built-in `exit`

            def myThread():
                with httpx.stream("GET", URL) as r:
                    for data in r.iter_bytes():
                        lock_exit.acquire()
                        if exit_flag:
                            break
                        lock_exit.release()
                        dg_connection.send(data)

            myHttp = threading.Thread(target=myThread)
            myHttp.start()

            input("Press Enter to stop transcription...\n")
            lock_exit.acquire()
            exit_flag = True
            lock_exit.release()

            myHttp.join()
            dg_connection.finish()
            print("Finished")

        except Exception as e:
            print(f"Could not open socket: {e}")

    stream_bbc_audio()
