import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

import dotenv
import litellm

from utils.action_handling import ActionHandler
from utils.action_type import ActionType
from utils.api.perplexity import perplexity_search
from utils.logging_config import setup_logging
from utils.TTS_utils import handle_audio_output, stream_to_elevenlabs

setup_logging(log_file=Path("logs/app.log"), log_level="INFO")
logger = logging.getLogger(__name__)

dotenv.load_dotenv()

agent_system_prompt = """
## TASK
You are an executive assistant to busy executives. Your job is to interpret the needs of the team within a meeting, ask for more information if needed, and then perform the necessary actions.

Your name is "ElevenLabs" -- you will know the user is speaking to you if they say "Hey ElevenLabs" or something similar, followed by a query. If they have not said "Hey ElevenLabs", you must take the DO_NOTHING action, even if you have all the information you need. The user must explicitly ask you to do something.

You will be provided with the full meeting transcript for context. The user may have asked multiple questions thoughtout the meeting, so ensure you're responding to the most recent query (at the end of the transcript).

Decide if you have all the information you need to perform the action. If you do, perform the action. If you don't, ask for more information. You can make assumptions for the relevant information based on the meeting transcript. Only ask for more information if you don't have enough information to make an assumption.

If the user asks you to search the web, or if you need to search the web to answer the user's question, simply proceed with the web search. Don't ask for confirmation or for additional information. Use the response field to write the search query.

## RESPONSE
You must respond with a JSON object in the below format. Do not include any other text before or after the JSON object.
{
    "more_info_required": bool,
    "response": string,
    "action": "ACTION"
}

## ACTIONS
You can perform the following actions:
- NO_ACTION: Do nothing
- REQUEST_INFO: Request more information from the user
- WEB_SEARCH: Search the web for information on a specific topic
- EMAIL_CREATION: Create and compose a new email
- CALENDAR_EVENT: Create or modify a calendar event
- NOTE_CREATION: Create a new note or document
- LINEAR_TASK: Create a new task in Linear

## REQUIRED INFORMATION

### WEB_SEARCH
- query: The query to search the web for (you can assume this based on the context) -- you do not need more information from the user if this is the relevant action

### EMAIL_CREATION
- subject: The subject of the email (you can assume this based on the context)
- body: The body of the email (ask for this if it's not clear)
- recipients: A list of recipients for the email (ask for this if it's not clear)

### CALENDAR_EVENT
- title: The title of the event (you can assume this based on the context)
- description: The description of the event (you can assume this based on the context)
- start_time: The start time of the event (ask for this if it's not clear)
- duration: The duration of the event (ask for this if it's not clear)
- attendees: A list of attendees for the event (ask for this if it's not clear)

### NOTE_CREATION
- title: The title of the note (you can assume this based on the context)
- body: The body of the note (ask for this if it's not clear)

### LINEAR_TASK
- title: The title of the task (you can assume this based on the context)
- description: The description of the task (you can assume this based on the context)
- priority: The priority of the task (ask for this if it's not clear)
- due_date: The due date of the task (ask for this if it's not clear)

### NO_ACTION
- If no action is requested or the user hasn't asked ElevenLabs to do anything, return {"no_action": "true"}

## RESPONSE EXAMPLES
If the user hasn't just said "Hey ElevenLabs":
{
    "more_info_required": false,
    "response": null,
    "action": "DO_NOTHING"
}

If more info is required:
{
    "more_info_required": true,
    "response": string, # let them know what you need
    "action": "REQUEST_INFO"
}

If you have all the information you need:
{
    "more_info_required": false,
    "response": string, # let them know what you will do next with as little detail as possible, ie. I created the task, I sent the email, I added the event to the calendar, etc...
    "action": "ACTION"
}

If you need to search the web:
{
    "more_info_required": false,
    "response": string, # the search query
    "action": "WEB_SEARCH"
}
"""


class Agent:
    def __init__(self):
        self.model = "groq/llama-3.3-70b-versatile"
        self.background_tasks = set()  # Keep track of background tasks
        self.action_handler = ActionHandler()  # Initialize the action handler
        logger.info(f"Initialized Agent with model: {self.model}")
        self.is_active = False
        self.more_info_required = False


    async def perform_action(
        self, transcript: str, action: str, participant_emails: list[str]
    ) -> None:
        try:
            # Convert string action to ActionType enum
            action_type = ActionType[action.upper()]
            print(f"Performing action: {action_type}")
            # Process the action using the action handler
            await self.action_handler.process_action(
                action_type=action_type,
                transcript=transcript,
                participant_emails=participant_emails,
            )
        except Exception as e:
            print(f"Error performing action {action}: {e}")
        finally:
            self.is_active = False
            # Remove the task from our set when done
            self.background_tasks.remove(asyncio.current_task())

    async def call_llm(self, transcript: str, participant_emails: list[str]) -> Dict[str, bool]:
        if self.is_active and not self.more_info_required:
            return {"response": None, "taking_action": True}

        self.is_active = True
        self.more_info_required = False
        print("Calling LLM...")
        messages = [
            {
                "role": "system",
                "content": agent_system_prompt,
            },
            {
                "role": "user",
                "content": f"Participant Emails: {participant_emails}\n\nTranscript: {transcript}",
            },
        ]

        response = litellm.completion(
            model=self.model, messages=messages, api_key=os.getenv("GROQ_API_KEY")
        )

        response_content = response.choices[0].message.content

        try:
            response_json = json.loads(response_content)
        except json.JSONDecodeError:
            print(f"Error decoding JSON: {response_content}")
            raise

        print(f"LLM Response: {response_json}")

        more_info_required = response_json.get("more_info_required")
        response = response_json.get("response")
        action = response_json.get("action")

        if action.lower() == ActionType.NO_ACTION.value:
            self.is_active = False
            self.more_info_required = False
            return {"response": None, "taking_action": self.is_active, "more_info_required": self.more_info_required}

        elif more_info_required == True:
            self.is_active = False
            self.more_info_required = True
            return {"response": response, "taking_action": self.is_active, "more_info_required": self.more_info_required}

        # If the action is to search the web, respond directly with perplexity results
        if action.lower() == ActionType.WEB_SEARCH.value:
            audio_data = await stream_to_elevenlabs("searching the web...")
            await handle_audio_output(audio_data, output_mode="speak")
            perplexity_results = perplexity_search(response)
            self.is_active = False
            self.more_info_required = False
            return {"response": perplexity_results, "taking_action": self.is_active, "more_info_required": self.more_info_required}

        else:
            # Create a task and add it to our set
            task = asyncio.create_task(self.perform_action(transcript, action, participant_emails))
            self.background_tasks.add(task)
            self.is_active = True
            self.more_info_required = False
            return {"response": response, "taking_action": self.is_active, "more_info_required": self.more_info_required}

    async def cleanup(self):
        """Wait for all background tasks to complete."""
        if self.background_tasks:
            print(f"Waiting for {len(self.background_tasks)} background tasks to complete...")
            await asyncio.gather(*self.background_tasks)


async def test_agent():
    agent = Agent()
    try:
        participant_emails = ["haz@pally.com", "wylansford@gmail.com", "lisa@pally.com"]
        transcript = open("testing/cal_event.txt", "r").read()
        response = await agent.call_llm(transcript, participant_emails)
        audio_data = await stream_to_elevenlabs(response)
        await handle_audio_output(audio_data, output_mode="speak")
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_agent())
