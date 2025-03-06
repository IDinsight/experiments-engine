from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    delete,
    select,
    update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from ..models import Base


class MessageDB(Base):
    """
    ORM base class for messages.
    """

    __tablename__ = "messages"

    message_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.user_id"), nullable=False
    )
    text = mapped_column(String, nullable=False)
    title = mapped_column(String, nullable=False)
    is_unread = mapped_column(Boolean, default=True, nullable=False)
    created_datetime_utc = mapped_column(DateTime(timezone=True), nullable=False)
    message_type = mapped_column(String(length=50), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "message",
        "polymorphic_on": "message_type",
    }

    @classmethod
    async def get_messages_by_user_id(
        cls, asession: AsyncSession, user_id: int
    ) -> Sequence["MessageDB"]:
        """
        Get all messages for a user.
        """
        stmt = select(cls).filter(cls.user_id == user_id)
        result = await asession.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def update_messages_read_status_by_message_ids(
        cls,
        asession: AsyncSession,
        message_ids: list[int],
        user_id: int,
        is_unread: bool,
    ) -> Sequence["MessageDB"]:
        """
        Update the read status of messages by message ids.
        """
        stmt = (
            update(cls)
            .filter(cls.message_id.in_(message_ids))
            .filter(cls.user_id == user_id)
            .values(is_unread=is_unread)
        )
        await asession.execute(stmt)
        await asession.commit()
        return await cls.get_messages_by_user_id(asession, user_id)

    @classmethod
    async def delete_messages_by_message_ids(
        cls, asession: AsyncSession, message_ids: list[int], user_id: int
    ) -> Sequence["MessageDB"]:
        """
        Delete messages by message ids.
        """
        stmt = (
            delete(cls)
            .filter(cls.message_id.in_(message_ids))
            .filter(cls.user_id == user_id)
        )
        await asession.execute(stmt)
        await asession.commit()
        return await cls.get_messages_by_user_id(asession, user_id)


class EventMessageDB(MessageDB):
    """
    ORM class for event messages.
    """

    __tablename__ = "event_messages"

    message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("messages.message_id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    experiment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("experiments_base.experiment_id"), nullable=False
    )

    __mapper_args__ = {"polymorphic_identity": "event"}

    @classmethod
    async def create_new_event_message(
        cls,
        asession: AsyncSession,
        user_id: int,
        text: str,
        title: str,
        experiment_id: int,
    ) -> "EventMessageDB":
        """
        Create a new event message.
        """
        new_message = cls(
            user_id=user_id,
            text=text,
            title=title,
            is_unread=True,
            experiment_id=experiment_id,
            created_datetime_utc=datetime.now(timezone.utc),
        )
        asession.add(new_message)
        await asession.commit()
        await asession.refresh(new_message)
        return new_message
