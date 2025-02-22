import io

import dotenv
from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.responses import StreamingResponse

from utils.action_handling import ActionHandler
from utils.function_calling_utils import ActionType, FunctionCaller
from utils.STT_utils import AudioTranscriptionHandler, process_audio_to_text
from utils.TTS_utils import stream_to_elevenlabs  # You'll need to implement this

dotenv.load_dotenv()


app = FastAPI()


async def determine_action(text: str):
    """
    Determine which action to take based on user input using the FunctionCaller.
    Returns the action type and any additional details.
    """
    function_caller = FunctionCaller()
    return await function_caller.determine_action(text)


@app.websocket("/ws-audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    transcription_handler = AudioTranscriptionHandler()
    function_caller = FunctionCaller()
    action_handler = ActionHandler()

    try:
        while True:
            audio_data = await websocket.receive_bytes()

            # Process the audio chunk
            is_active, text = await transcription_handler.process_audio_chunk(audio_data)

            if text:
                print(f"Transcribed text: {text}")

                if is_active:
                    # Determine action when system is actively listening
                    action_type, details = await function_caller.determine_action(text)

                    # Process the action and get response
                    action_response = await action_handler.process_action(
                        action_type, text, details
                    )

                    # Send response back to client
                    response = {
                        "transcription": text,
                        "action": action_type.value,
                        "details": details,
                        "response": action_response,
                    }
                    await websocket.send_json(response)

                    # Reset listening state after processing
                    transcription_handler.reset_listening_state()
                else:
                    # Just send back transcription when not actively listening
                    await websocket.send_json({"transcription": text})

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await transcription_handler.close()
        await websocket.close()


async def create_and_stream_audio(action: str):
    # Stream to ElevenLabs
    # Return response
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
