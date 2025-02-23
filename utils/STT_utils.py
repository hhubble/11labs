import asyncio
import logging
import os

from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

logger = logging.getLogger(__name__)


class AudioTranscriptionHandler:
    def __init__(
        self,
        trigger_phrases={"hey eleven labs", "hey 11 labs", "hey eleven laps", "hey 11 laps"},
        buffer_size=10,
    ):
        self.deepgram = DeepgramClient(os.environ.get("DEEPGRAM_API_KEY"))
        self.dg_connection = None
        self.trigger_phrases = trigger_phrases
        self.buffer_size = buffer_size
        logger.info("Initialized AudioTranscriptionHandler")
        self._is_listening_active = False
        self._current_text = ""
        self._transcription_buffer = []
        self._full_transcript = []

    async def initialize_connection(self):
        try:
            self.dg_connection = self.deepgram.listen.asyncwebsocket.v("1")
            parent = self

            async def on_message(msg_self, result, **kwargs):
                if not hasattr(result, "channel"):
                    return

                transcript = result.channel.alternatives[0].transcript.lower()
                cleaned_transcript = transcript.replace(",", "").replace(".", "").replace("!", "")
                is_final = result.is_final

                if not cleaned_transcript:
                    return

                if is_final:
                    # Keep only the last buffer_size transcripts
                    parent._transcription_buffer.append(cleaned_transcript)
                    if len(parent._transcription_buffer) > parent.buffer_size:
                        parent._transcription_buffer.pop(0)

                    logger.info(f"cleaned_transcript: {cleaned_transcript}")
                    logger.info(f"is_listening_active: {parent._is_listening_active}")

                    # Get the last few chunks combined
                    context = " ".join(parent._transcription_buffer)

                    # Check if any trigger phrase is in the combined context
                    if not parent._is_listening_active:
                        for trigger in parent.trigger_phrases:
                            if trigger in context:
                                logger.info(
                                    f"🎯 Trigger phrase detected. Full context: '{context}'"
                                )
                                print(f"\n🎯 Activated! Full context: '{context}'")
                                parent._is_listening_active = True
                                parent._full_transcript.append(cleaned_transcript)
                                break

                    elif parent._is_listening_active:
                        logger.info(f"🎤 Final transcription: '{cleaned_transcript}'")
                        print(f"🎤 {cleaned_transcript}")
                        parent._current_text = cleaned_transcript
                        parent._full_transcript.append(cleaned_transcript)

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

            # Capture and clear text before processing new chunk
            # text = self._current_text
            self._current_text = ""  # Clear before processing new chunk

            # Get context and send new audio data
            context = " ".join(self._transcription_buffer) if self._transcription_buffer else ""
            await self.dg_connection.send(audio_bytes)

            return self._is_listening_active, context

        except Exception as e:
            logger.exception(f"Error processing audio chunk: {e}")
            return False, "", ""

    async def close(self):
        if self.dg_connection:
            try:
                await self.dg_connection.finish()
                self.dg_connection = None  # Clear the connection
            except Exception as e:
                logger.exception(f"Error closing Deepgram connection: {e}")

    def reset_listening_state(self):
        self._is_listening_active = False
        self._current_text = ""
        self._transcription_buffer.clear()
        self._full_transcript.clear()

    def get_full_transcript(self) -> str:
        return " ".join(self._full_transcript)


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
