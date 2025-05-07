#!/usr/bin/env python
"""
This script processes notifications for experiments.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the parent directory to sys.path to allow absolute imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.messages.models import EventMessageDB
from app.models import ExperimentBaseDB, NotificationsDB
from app.schemas import EventType
from app.utils import setup_logger

logger = setup_logger(log_level=logging.INFO)


async def check_days_elapsed(
    experiment_id: int,
    notification_id: int,
    milestone_days: int,
    asession: AsyncSession,
) -> bool:
    """
    Check if the number of days elapsed since the experiment was created is greater
    than or equal to the milestone
    """
    experiments_stmt = select(ExperimentBaseDB).where(
        ExperimentBaseDB.experiment_id == experiment_id
    )
    experiment: ExperimentBaseDB | None = (
        (await asession.execute(experiments_stmt)).scalars().first()
    )

    now = datetime.now(timezone.utc)
    if experiment:
        days_elapsed = (now - experiment.created_datetime_utc).days
        if days_elapsed >= milestone_days:
            stmt = select(NotificationsDB).where(
                NotificationsDB.experiment_id == experiment_id,
                NotificationsDB.notification_id == notification_id,
            )
            notification_to_disable = (await asession.execute(stmt)).scalars().first()
            if notification_to_disable:
                notification_to_disable.is_active = False

                await EventMessageDB.create_new_event_message(
                    asession=asession,
                    user_id=experiment.user_id,
                    experiment_id=experiment_id,
                    text=(
                        f"Experiment {experiment_id} has reached {milestone_days} days"
                    ),
                    title=(
                        f"Experiment {experiment_id} has reached {milestone_days} days"
                    ),
                )

                logger.info(
                    f"Creating message for experiment: {experiment_id} for days elapsed"
                )
                await asession.commit()
                return True
            else:
                raise ValueError(
                    (
                        f"Notification with id {notification_id} not "
                        f"found for experiment {experiment_id}"
                    )
                )

        logger.info(
            (
                f"Milestone not reached. Days elapsed for experiment {experiment_id} "
                f"is {days_elapsed}. Milestone is {milestone_days}"
            )
        )
        return False
    else:
        raise ValueError(f"Experiment with id {experiment_id} not found")


async def check_trials_completed(
    experiment_id: int,
    notification_id: int,
    milestone_trials: int,
    asession: AsyncSession,
) -> bool:
    """
    Check if the number of trials completed for the experiment is greater than
    or equal to the milestone.
    """
    # Fetch experiment
    stmt = select(ExperimentBaseDB).where(
        ExperimentBaseDB.experiment_id == experiment_id
    )
    experiment: ExperimentBaseDB | None = (
        (await asession.execute(stmt)).scalars().first()
    )

    if experiment:
        if experiment.n_trials >= milestone_trials:
            # Update notification status
            stmt = select(NotificationsDB).where(
                NotificationsDB.experiment_id == experiment_id,
                NotificationsDB.notification_id == notification_id,
            )
            notification_to_disable = (await asession.execute(stmt)).scalars().first()

            if notification_to_disable:
                notification_to_disable.is_active = False

                # Create an event message asynchronously
                await EventMessageDB.create_new_event_message(
                    asession=asession,
                    user_id=experiment.user_id,
                    experiment_id=experiment_id,
                    text=(
                        f"Experiment {experiment_id} has reached "
                        f"{milestone_trials} trials"
                    ),
                    title=(
                        f"Experiment {experiment_id} has reached "
                        f"{milestone_trials} trials"
                    ),
                )

                logger.info(
                    f"Creating message for experiment: {experiment_id} "
                    "for trials completed"
                )
                await asession.commit()
                return True
            else:
                raise ValueError(
                    f"Notification with id {notification_id} not found "
                    f"for experiment {experiment_id}"
                )

        logger.info(
            f"Milestone not reached. Trials completed for experiment {experiment_id} "
            f"is {experiment.n_trials}. Milestone is {milestone_trials}"
        )
        return False
    else:
        raise ValueError(f"Experiment with id {experiment_id} not found")


async def check_percentage_better(
    experiment_id: int,
    notification_id: int,
    milestone_percentage: int,
    asession: AsyncSession,
) -> bool:
    """
    TBD: Implement this function
    """
    return False


async def process_notifications(asession: AsyncSession) -> int:
    """
    Process all active notifications
    """
    # get all active notifications
    stmt = select(NotificationsDB).where(NotificationsDB.is_active)
    notifications = (await asession.execute(stmt)).scalars().all()
    total_messages_created = 0
    for notification in notifications:
        if notification.notification_type == EventType.DAYS_ELAPSED:
            message_was_created = await check_days_elapsed(
                notification.experiment_id,
                notification.notification_id,
                notification.notification_value,
                asession,
            )
        elif notification.notification_type == EventType.TRIALS_COMPLETED:
            message_was_created = await check_trials_completed(
                notification.experiment_id,
                notification.notification_id,
                notification.notification_value,
                asession,
            )
        elif notification.notification_type == EventType.PERCENTAGE_BETTER:
            message_was_created = await check_percentage_better(
                notification.experiment_id,
                notification.notification_id,
                notification.notification_value,
                asession,
            )
        else:
            raise ValueError(
                f"Unknown notification type: {notification.notification_type}"
            )
        total_messages_created += message_was_created

    logger.info(f"{total_messages_created} notifications processed successfully")

    return total_messages_created


async def main() -> None:
    """
    Main function to process notifications
    """
    async for asession in get_async_session():
        await process_notifications(asession)


if __name__ == "__main__":
    asyncio.run(main())
