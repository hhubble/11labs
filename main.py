import io

from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.responses import StreamingResponse

app = FastAPI()

async def create_calendar_event(text: str):
    # Create a calendar event
    pass

async def send_email(text: str):
    # Send an email
    pass

async def 

async def process_audio_to_text(audio_data: bytes):
    # Convert audio to wav
    # Stream to ElevenLabs
    # Return response
    

async def determine_action(text: str):
    # Do a function call, decide if
    # 1. email
    # create calendar event
    
    
@app.websocket("/ws-audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive audio data from the client
            audio_data = await websocket.receive_bytes()
            # TODO 
            
            # Send processed audio back to the client
            await websocket.send_bytes(audio_data)  # For now, just echoing back

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
