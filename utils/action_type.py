from enum import Enum


class ActionType(Enum):
    NO_ACTION = "no_action"
    REQUEST_INFO = "request_info"
    WEB_SEARCH = "web_search"
    EMAIL_CREATION = "email_creation"
    CALENDAR_EVENT = "calendar_event"
    NOTE_CREATION = "note_creation"
    LINEAR_TASK = "linear_task"
    CATCH_ME_UP = "catch_me_up"
    AMAZON_ORDER = "amazon_order"
