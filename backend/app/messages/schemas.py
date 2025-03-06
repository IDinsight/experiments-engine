from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageCreate(BaseModel):
    """
    Pydantic model for creating a message
    """

    title: str
    text: str


class MessageResponse(MessageCreate):
    """
    Pydantic model for a message response
    """

    message_id: int
    is_unread: bool
    created_datetime_utc: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageReadToggle(BaseModel):
    """
    Pydantic model for toggling the read status of a message
    """

    message_ids: list[int]
    is_unread: bool


class EventMessageCreate(MessageCreate):
    """
    Pydantic model for creating an event message
    """

    experiment_id: int
