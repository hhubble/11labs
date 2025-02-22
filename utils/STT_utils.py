import os
import threading

import httpx
from deepgram import DeepgramClient, DeepgramClientOptions, LiveOptions, LiveTranscriptionEvents

# URL for the real-time streaming audio you would like to transcribe
URL = "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"


async def process_audio_to_text(audio_bytes: bytes):
    try:
        deepgram = DeepgramClient(os.environ.get("DEEPGRAM_API_KEY"))
        dg_connection = deepgram.listen.live.v("1")
        transcription_result = []

        # Listen for any transcripts received from Deepgram
        def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) > 0:
                transcription_result.append(sentence)

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        # Create a websocket connection to Deepgram
        options = LiveOptions(smart_format=True, model="nova-2", language="en-US")
        dg_connection.start(options)

        # Send the audio bytes
        dg_connection.send(audio_bytes)
        dg_connection.finish()

        # Return the transcription result
        return " ".join(transcription_result)

    except Exception as e:
        print(f"Could not process audio: {e}")
        return ""


def stream_bbc_audio():
    try:
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        dg_connection = deepgram.listen.live.v("1")

        def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) > 0:
                print(f"transcript: {sentence}")

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        options = LiveOptions(smart_format=True, model="nova-2", language="en-US")
        dg_connection.start(options)

        lock_exit = threading.Lock()
        exit = False

        def myThread():
            with httpx.stream("GET", URL) as r:
                for data in r.iter_bytes():
                    lock_exit.acquire()
                    if exit:
                        break
                    lock_exit.release()
                    dg_connection.send(data)

        myHttp = threading.Thread(target=myThread)
        myHttp.start()

        input("Press Enter to stop transcription...\n")
        lock_exit.acquire()
        exit = True
        lock_exit.release()

        myHttp.join()
        dg_connection.finish()
        print("Finished")

    except Exception as e:
        print(f"Could not open socket: {e}")


if __name__ == "__main__":
    stream_bbc_audio()
