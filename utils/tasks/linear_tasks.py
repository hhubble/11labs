import litellm
import json
import os
import logging
from utils.api.linear import create_linear_issue
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

new_task_system_prompt = """
Your task is to create a new linear task based on the provided transcript.

You're provided the full meeting transcript, and the user may have asked multiple questions throughout the meeting. Ensure you act on only the most recent request (at the end of the transcript).

## OUTPUT
You must respond JSON format only with no additional text before or after. Use the following format:
{
    "title": string,
    "description": string,
    "priority": int,
    "due_date": string  in ISO 8601 format (e.g., "2024-03-25")
}

Priority options:
- 0: None
- 1: Urgent
- 2: High
- 3: Medium
- 4: Low

Date format:
- ISO 8601 format (e.g., "2024-03-25")
"""

async def handle_new_linear_task(transcript: str) -> bool:
    try:
        logger.info("Processing new linear task creation request")
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        print("Calling LLM...")
        messages = [
            {
                "role": "system",
                "content": new_task_system_prompt,
            },
            {"role": "user", "content": f"The current UTC time is: {current_time}\n\n{transcript}"},
        ]

        response = litellm.completion(
            model = "groq/llama-3.3-70b-versatile",
            messages=messages,
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        response_content = response.choices[0].message.content
        response_json = json.loads(response_content)
        
        title = response_json.get("title", None)
        description = response_json.get("description", None)
        priority = response_json.get("priority", None)
        due_date = response_json.get("due_date", None)
        
        if not (title and description and priority and due_date):
            logger.error("Missing required fields in response")
            return False
        
        create_linear_issue(title, description, priority, due_date)
        
        return True
    except Exception as e:
        logger.exception(f"Error processing new linear task creation: {e}")
        return False