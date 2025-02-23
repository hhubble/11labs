from re import T
import litellm
import json
import os
import logging
from utils.api.google import GoogleAPI
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

email_system_prompt = """
## TASK
Your task is to send the requested email based on the provided transcript.

You're provided the full meeting transcript, and the user may have asked multiple questions throughout the meeting. Ensure you act on only the most recent request (at the end of the transcript).

## OUTPUT
You must respond JSON format only with no additional text before or after. Use the following format:
{
    "to": [string],
    "subject": string,
    "body": string
}
"""

calendar_system_prompt = """
Your task is to create a calendar event based on the provided transcript.

You're provided the full meeting transcript, and the user may have asked multiple questions throughout the meeting. Ensure you act on only the most recent request (at the end of the transcript).

## OUTPUT
You must respond JSON format only with no additional text before or after. Use the following format:
{
    "title": string,
    "location": string,
    "description": string,
    "start_time": string,
    "end_time": string,
    "attendees": [string]
}
"""

async def handle_email_creation(transcript: str) -> bool:
    try:
        logger.info("Processing email creation request")
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        print("Calling LLM...")
        messages = [
            {
                "role": "system",
                "content": email_system_prompt,
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
        
        to = response_json.get("to", [])
        subject = response_json.get("subject", None)
        body = response_json.get("body", None)
        
        if not (to and subject and body):
            logger.error("Missing required fields in response")
            return False
        
        google_api = GoogleAPI()
        authenticated = google_api.authenticate()
        if not authenticated:
            logger.error("Failed to authenticate with Google")
            return False
        
        google_api.send_email(to, subject, body)
        
        return True
    except Exception as e:
        logger.exception(f"Error processing email creation: {e}")
        return False

async def handle_calendar_event(transcript: str) -> bool:
    try:
        logger.info("Processing calendar event creation request")
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        print("Calling LLM...")
        messages = [
            {
                "role": "system",
                "content": calendar_system_prompt,
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
        location = response_json.get("location", None)
        description = response_json.get("description", None)
        start_time = response_json.get("start_time", None)
        end_time = response_json.get("end_time", None)
        attendees = response_json.get("attendees", [])
        
        if not (title and location and description and start_time and end_time and attendees):
            logger.error("Missing required fields in response")
            return False
        
        google_api = GoogleAPI()
        authenticated = google_api.authenticate()
        if not authenticated:
            logger.error("Failed to authenticate with Google")
            return False
        
        google_api.create_event(title, location, description, start_time, end_time, attendees)
        
        return True
    except Exception as e:
        logger.exception(f"Error processing email creation: {e}")
        return False