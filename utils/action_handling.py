import logging

from utils.action_type import ActionType
from utils.tasks.amazon_order_tasks import run_amazon_cart_process
from utils.tasks.catch_up_tasks import handle_catch_me_up
from utils.tasks.google_tasks import handle_calendar_event, handle_email_creation
from utils.tasks.linear_tasks import handle_new_linear_task
from utils.tasks.notion_tasks import handle_new_notion_note

logger = logging.getLogger(__name__)


class ActionHandler:
    async def process_action(
        self, action_type: ActionType, transcript: str, participant_emails: list[str]
    ) -> dict:
        logger.info(f"Processing action of type: {action_type}")
        try:
            if action_type == ActionType.EMAIL_CREATION:
                result = await handle_email_creation(transcript)
                return {"success": result}

            elif action_type == ActionType.CALENDAR_EVENT:
                result = await handle_calendar_event(transcript, participant_emails)
                return {"success": result}

            elif action_type == ActionType.NOTE_CREATION:
                result = await handle_new_notion_note(transcript)
                return {"success": result}

            elif action_type == ActionType.LINEAR_TASK:
                result = await handle_new_linear_task(transcript)
                return {"success": result}
            elif action_type == ActionType.CATCH_ME_UP:
                result = await handle_catch_me_up(transcript)
                return {"success": result}
            elif action_type == ActionType.AMAZON_ORDER:
                result = await run_amazon_cart_process(transcript)
                return {"success": result}
            else:
                logger.warning(f"Received unknown action type: {action_type}")
                return {"success": False}

        except Exception as e:
            logger.exception(f"Error processing action: {e}")
            return {"success": False}
