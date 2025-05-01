from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import get_verified_user
from ..database import get_async_session
from ..users.models import UserDB
from .models import EventMessageDB, MessageDB
from .schemas import EventMessageCreate, MessageReadToggle, MessageResponse

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("/", response_model=list[MessageResponse])
async def get_messages(
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[MessageResponse]:
    """
    Get all messages for a user
    """
    messages = await MessageDB.get_messages_by_user_id(asession, user_db.user_id)
    return [MessageResponse.model_validate(message) for message in messages]


@router.post("/", response_model=MessageResponse)
async def create_message(
    message: EventMessageCreate,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> MessageResponse:
    """
    Create a new message
    """
    event_message = await EventMessageDB.create_new_event_message(
        asession=asession,
        user_id=user_db.user_id,
        text=message.text,
        title=message.title,
        experiment_id=message.experiment_id,
    )

    return MessageResponse.model_validate(event_message)


@router.delete("/", response_model=list[MessageResponse])
async def delete_messages(
    message_ids: list[int],
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[MessageResponse]:
    """
    Delete messages by message_ids
    """
    remaining_messages = await MessageDB.delete_messages_by_message_ids(
        asession=asession, message_ids=message_ids, user_id=user_db.user_id
    )

    return [MessageResponse.model_validate(message) for message in remaining_messages]


@router.patch("/", response_model=list[MessageResponse])
async def mark_messages_as_read(
    message_read_toggle: MessageReadToggle,
    user_db: Annotated[UserDB, Depends(get_verified_user)],
    asession: AsyncSession = Depends(get_async_session),
) -> list[MessageResponse]:
    """
    Mark messages as read/unread by message_ids
    """
    messages = await MessageDB.update_messages_read_status_by_message_ids(
        asession=asession,
        message_ids=message_read_toggle.message_ids,
        user_id=user_db.user_id,
        is_unread=message_read_toggle.is_unread,
    )

    return [MessageResponse.model_validate(message) for message in messages]
