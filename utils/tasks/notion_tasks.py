import litellm
import json
import os
import logging
from utils.api.notion import create_note

logger = logging.getLogger(__name__)

new_note_system_prompt = """
Your task is to create a new notion note based on the provided transcript. Be detailed in your note taking, per the user's request.

You're provided the full meeting transcript, and the user may have asked multiple questions throughout the meeting. Ensure you act on only the most recent request (at the end of the transcript).

## OUTPUT
You must respond JSON format only with no additional text before or after. Use the following format:
{
    "title": string,
    "content": string
}
"""

async def handle_new_notion_note(transcript: str) -> bool:
    try:
        logger.info("Processing new notion note creation request")
        
        print("Calling LLM...")
        messages = [
            {
                "role": "system",
                "content": new_note_system_prompt,
            },
            {"role": "user", "content": transcript},
        ]

        response = litellm.completion(
            model = "groq/llama-3.3-70b-versatile",
            messages=messages,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        response_content = response.choices[0].message.content
        response_json = json.loads(response_content)
        
        title = response_json.get("title", None)
        content = response_json.get("content", None)
        
        if not (title and content):
            logger.error("Missing required fields in response")
            return False
        
        create_note(title, content)
        
        return True
    except Exception as e:
        logger.exception(f"Error processing new linear task creation: {e}")
        return False