import json
import logging
import os
from enum import Enum
from typing import Any, Dict

import dotenv
import litellm

logger = logging.getLogger(__name__)

dotenv.load_dotenv()

# Add this line to verify the API key is loaded


class ActionType(Enum):
    WEB_SEARCH = "web_search"
    EMAIL_CREATION = "email_creation"
    CALENDAR_EVENT = "calendar_event"
    NOTE_CREATION = "note_creation"
    LINEAR_TASK = "linear_task"
    VOICE_MESSAGE = "voice_message"
    UNKNOWN = "unknown"


# Function calling schema for the LLM
FUNCTION_SCHEMA = {
    "type": "function",
    "function": {
        "name": "determine_action",
        "description": "Determine which action to take based on user input",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [action.value for action in ActionType],
                    "description": "The type of action to perform",
                    "enumDescriptions": {
                        "web_search": "Search the web for information on a specific topic",
                        "email_creation": "Create and compose a new email",
                        "calendar_event": "Create or modify a calendar event",
                        "note_creation": "Create a new note or document",
                        "linear_task": "Create a new task in Linear",
                    },
                },
                "details": {
                    "type": "object",
                    "description": "Additional details for the action",
                    "properties": {
                        "query": {"type": "string"},
                        "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                        "summary": {"type": "string"},
                    },
                },
            },
            "required": ["action"],
        },
    },
}


class FunctionCaller:
    def __init__(self):
        self.model = "groq/llama-3.1-8b-instant"
        logger.info(f"Initialized FunctionCaller with model: {self.model}")

    async def determine_action(self, text: str, full_context) -> tuple[ActionType, Dict[str, Any]]:
        try:
            logger.info("Determining action from user input")
            logger.debug(f"Input text: {text[:100]}...")

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that determines appropriate actions based on user input.",
                },
                {"role": "user", "content": text},
            ]

            logger.debug("Making API call to LLM")
            response = litellm.completion(
                model=self.model,
                messages=messages,
                tools=[FUNCTION_SCHEMA],
                tool_choice="auto",
                api_key=os.getenv("GROQ_API_KEY"),
            )

            logger.debug(f"Received response: {response}")
            tool_calls = response.choices[0].message.tool_calls

            if tool_calls:
                function_args = json.loads(tool_calls[0].function.arguments)
                action = ActionType(function_args.get("action"))
                details = function_args.get("details", {})

                logger.info(f"Determined action: {action}")
                logger.debug(f"Action details: {details}")
                return action, details

            logger.warning("No action could be determined, returning UNKNOWN")
            return ActionType.UNKNOWN, {}

        except Exception as e:
            logger.exception(f"Error in function calling: {e}")
            return ActionType.UNKNOWN, {}


if __name__ == "__main__":
    import asyncio

    async def test_function_caller():
        caller = FunctionCaller()

        # Test cases with expected outputs
        test_inputs = [
            # "Can you search the web for information about climate change?",
            # "Schedule a meeting with John tomorrow at 2pm about the project review",
            "Create a new task in Linear to implement user authentication with high priority",
            "Send an email to sarah@example.com about the upcoming team event",
            "Make a note about the key points from today's meeting",
            "Tell me a joke",  # Should return UNKNOWN
        ]

        print("Testing Function Caller with various inputs:\n")

        for input_text in test_inputs:
            import time

            print(f"Input: {input_text}")
            action, details = await caller.determine_action(input_text, "test context")
            print(f"Action Type: {action}")
            print(f"Details: {details}\n")

    # Run the tests
    asyncio.run(test_function_caller())
