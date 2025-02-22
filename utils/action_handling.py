from typing import Any, Dict

from utils.function_calling_utils import ActionType
from utils.TTS_utils import stream_to_elevenlabs


class ActionHandler:
    async def handle_web_search(self, details: dict) -> str:
        # TODO: Implement web search functionality
        return "I'll search the web for that information."

    async def handle_email_creation(self, details: dict) -> str:
        # TODO: Implement email creation
        return "I'll help you create that email."

    async def handle_calendar_event(self, details: dict) -> str:
        # TODO: Implement calendar event creation
        return "I'll schedule that event for you."

    async def handle_note_creation(self, details: dict) -> str:
        # TODO: Implement note creation
        return "I'll create a note with that information."

    async def handle_linear_task(self, details: dict) -> str:
        # TODO: Implement Linear task creation
        return "I'll create that task in Linear."

    async def handle_voice_message(self, text: str, details: dict) -> bytes:
        response = f"{text}"
        return await stream_to_elevenlabs(response)

    async def handle_unknown(self, text: str) -> bytes:
        response = "I'm not sure how to help with that. Could you please rephrase?"
        return await stream_to_elevenlabs(response)

    async def process_action(self, action_type: ActionType, text: str, details: dict) -> dict:
        try:
            if action_type == ActionType.WEB_SEARCH:
                result = await self.handle_web_search(details)
                return {"type": "text", "content": result}

            elif action_type == ActionType.EMAIL_CREATION:
                result = await self.handle_email_creation(details)
                return {"type": "text", "content": result}

            elif action_type == ActionType.CALENDAR_EVENT:
                result = await self.handle_calendar_event(details)
                return {"type": "text", "content": result}

            elif action_type == ActionType.NOTE_CREATION:
                result = await self.handle_note_creation(details)
                return {"type": "text", "content": result}

            elif action_type == ActionType.LINEAR_TASK:
                result = await self.handle_linear_task(details)
                return {"type": "text", "content": result}

            elif action_type == ActionType.VOICE_MESSAGE:
                audio = await self.handle_voice_message(text, details)
                return {"type": "audio", "content": audio}

            else:  # UNKNOWN
                audio = await self.handle_unknown(text)
                return {"type": "audio", "content": audio}

        except Exception as e:
            print(f"Error processing action: {e}")
            return {"type": "error", "content": str(e)}
