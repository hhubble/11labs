import io

from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.responses import StreamingResponse
from utils.STT_utils import process_audio_to_text
import dotenv

dotenv.load_dotenv()


app = FastAPI()


    

async def determine_action(text: str):
    # Do a function call, decide if
    # - Web search
    # - Email creation
    # - Cal event creation
    # - Note creation    
        
    
@app.websocket("/ws-audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive audio data from the client
            audio_data = await websocket.receive_bytes()
            
            # Process the audio
            text = await process_audio_to_text(audio_data)
            
            # Determine the action
            action = await determine_action(text)
            
            # Based on action, do the following:
            # - Web search
            # - Email creation
            # - Cal event creation
            # - Note creation
            
            
            # Send processed text back to the client
            await create_and_stream_audio(action)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()



async def create_and_stream_audio(action: str):
    # Stream to ElevenLabs
    # Return response
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
