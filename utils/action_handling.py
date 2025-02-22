import logging
from typing import Any, Dict

from utils.function_calling_utils import ActionType
from utils.TTS_utils import stream_to_elevenlabs

logger = logging.getLogger(__name__)


class ActionHandler:
    async def handle_web_search(self, details: dict) -> str:
        logger.info("Processing web search request")
        logger.debug(f"Search details: {details}")
        # TODO: Implement web search functionality
        return "I'll search the web for that information."

    async def handle_email_creation(self, details: dict) -> str:
        logger.info("Processing email creation request")
        logger.debug(f"Email details: {details}")
        # TODO: Implement email creation
        return "I'll help you create that email."

    async def handle_calendar_event(self, details: dict) -> str:
        logger.info("Processing calendar event request")
        logger.debug(f"Calendar details: {details}")
        # TODO: Implement calendar event creation
        return "I'll schedule that event for you."

    async def handle_note_creation(self, details: dict) -> str:
        logger.info("Processing note creation request")
        logger.debug(f"Note details: {details}")
        # TODO: Implement note creation
        return "I'll create a note with that information."

    async def handle_linear_task(self, details: dict) -> str:
        logger.info("Processing Linear task creation request")
        logger.debug(f"Task details: {details}")
        # TODO: Implement Linear task creation
        return "I'll create that task in Linear."

    async def handle_voice_message(self, text: str, details: dict) -> bytes:
        logger.info("Processing voice message request")
        logger.debug(f"Voice message text: {text[:100]}...")
        response = f"{text}"
        return await stream_to_elevenlabs(response)

    async def handle_unknown(self, text: str) -> bytes:
        logger.warning(f"Received unknown action request: {text[:100]}...")
        response = "I'm not sure how to help with that. Could you please rephrase?"
        return await stream_to_elevenlabs(response)

    async def process_action(self, action_type: ActionType, text: str, details: dict) -> dict:
        logger.info(f"Processing action of type: {action_type}")
        try:
            if action_type == ActionType.WEB_SEARCH:
                result = await self.handle_web_search(details)
                #TODO 
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
            logger.exception(f"Error processing action: {e}")
            return {"type": "error", "content": str(e)}
