import asyncio
import logging
import os
import httpx
import threading

from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

logger = logging.getLogger(__name__)


class AudioTranscriptionHandler:
    def __init__(
        self,
        trigger_phrases={"hey eleven labs", "hey 11 labs", "hey eleven laps", "hey 11 laps"},
        buffer_size=10,
    ):
        logger.info("Initialized AudioTranscriptionHandler")
        self.deepgram = DeepgramClient(os.environ.get("DEEPGRAM_API_KEY"))
        self.dg_connection = None
        self.trigger_phrases = trigger_phrases
        self.buffer_size = buffer_size
        self._is_listening_active = False
        self._current_text = ""
        self._transcription_buffer = []
        self._full_transcript = []
        self._is_speaking = False
        self._current_utterance = []

    async def initialize_connection(self):
        try:
            self.dg_connection = self.deepgram.listen.asyncwebsocket.v("1")
            parent = self

            async def on_message(msg_self, result, **kwargs):
                if not hasattr(result, "channel"):
                    return

                transcript = result.channel.alternatives[0].transcript
                is_final = result.is_final
                speech_final = result.speech_final

                if transcript:
                    if not parent._is_speaking:
                        parent._is_speaking = True
                        parent._current_utterance = []
                    
                    if is_final:
                        parent._current_utterance.append(transcript)

                if speech_final and parent._is_speaking:
                    complete_utterance = " ".join(parent._current_utterance)
                    parent._full_transcript.append(complete_utterance)
                    parent._current_utterance = []
                    parent._is_speaking = False
                    logger.info(f"New complete utterance: {complete_utterance}")

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
                endpointing=500,
                diarize=True
            )

            if not await self.dg_connection.start(options):
                raise Exception("Failed to start Deepgram connection")

        except Exception as e:
            logger.exception(f"Error initializing Deepgram connection: {e}")
            raise

    async def process_audio_chunk(self, audio_bytes: bytes) -> str:
        try:
            if not self.dg_connection:
                await self.initialize_connection()

            # Send new audio data
            await self.dg_connection.send(audio_bytes)
            
            # If agent is speaking, only return transcript without triggering new commands
            if self._is_speaking:
                return self._full_transcript[-1] if self._full_transcript else ""
            
            # Return only the latest transcript chunk
            transcript = self._full_transcript[-1] if self._full_transcript else ""
            return transcript

        except Exception as e:
            logger.exception(f"Error processing audio chunk: {e}")
            return ""

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
        # self._transcription_buffer.clear()
        # self._full_transcript.clear()

    #
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

        options = LiveOptions(encoding="linear16", sample_rate=16000, channels=1, model="nova-2", idle_timeout=60000)

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

            options = LiveOptions(smart_format=True, model="nova-2", language="en-US", idle_timeout=60000)
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
