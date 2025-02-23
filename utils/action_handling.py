import logging
from utils.action_type import ActionType

from utils.tasks.google_tasks import handle_email_creation, handle_calendar_event
from utils.tasks.linear_tasks import handle_new_linear_task

## PLACEHOLDERS
async def handle_web_search(transcript: str) -> bool:
    return True

async def handle_note_creation(transcript: str) -> bool:
    return True

logger = logging.getLogger(__name__)

class ActionHandler:
    async def process_action(self, action_type: ActionType, transcript: str) -> dict:
        logger.info(f"Processing action of type: {action_type}")
        try:
            if action_type == ActionType.WEB_SEARCH:
                result = await handle_web_search(transcript)
                return {"success": result}

            elif action_type == ActionType.EMAIL_CREATION:
                result = await handle_email_creation(transcript)
                return {"success": result}

            elif action_type == ActionType.CALENDAR_EVENT:
                result = await handle_calendar_event(transcript)
                return {"success": result}

            elif action_type == ActionType.NOTE_CREATION:
                result = await handle_note_creation(transcript)
                return {"success": result}

            elif action_type == ActionType.LINEAR_TASK:
                result = await handle_new_linear_task(transcript)
                return {"success": result}
            
            else:
                logger.warning(f"Received unknown action type: {action_type}")
                return {"success": False}


        except Exception as e:
            logger.exception(f"Error processing action: {e}")
            return {"success": False}
