#!/usr/bin/env python
"""
Script to auto-fail experiments that have not been updated in a certain amount of time.
Run from the backend directory with: python -m jobs.auto_fail
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add the parent directory to sys.path to allow absolute imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.experiments.dependencies import (
    format_rewards_for_arm_update,
    update_arm_based_on_outcome,
)
from app.experiments.models import DrawDB, ExperimentDB
from app.experiments.schemas import ObservationType


async def auto_fail_experiment(asession: AsyncSession) -> int:
    """
    Auto fail experiments draws that have not been updated in a certain amount of time.

    Args:
        asession: SQLAlchemy async session

    Returns:
        int: Number of draws automatically failed
    """
    total_failed = 0
    now = datetime.now(timezone.utc)

    # Fetch all required experiments data in one query
    experiment_query = select(ExperimentDB).where(ExperimentDB.auto_fail.is_(True))
    experiments_result = (await asession.execute(experiment_query)).unique()
    experiments = experiments_result.scalars().all()
    for experiment in experiments:
        hours_threshold = (
            experiment.auto_fail_value * 24
            if experiment.auto_fail_unit == "days"
            else experiment.auto_fail_value
        )

        cutoff_datetime = now - timedelta(hours=hours_threshold)

        draws_query = (
            select(DrawDB)
            .join(
                ExperimentDB,
                DrawDB.experiment_id == ExperimentDB.experiment_id,
            )
            .where(
                DrawDB.experiment_id == experiment.experiment_id,
                DrawDB.observation_type.is_(None),
                DrawDB.draw_datetime_utc <= cutoff_datetime,
            )
            .limit(100)
        )  # Process in smaller batches

        # Paginate through results if there are many draws to avoid memory issues
        offset = 0
        while True:
            batch_query = draws_query.offset(offset)
            draws_result = (await asession.execute(batch_query)).unique()
            draws_batch = draws_result.scalars().all()
            if not draws_batch:
                break

            for draw in draws_batch:
                draw.observation_type = ObservationType.AUTO

                rewards_list, context_list, treatments_list = (
                    await format_rewards_for_arm_update(
                        experiment, draw.arm_id, 0.0, draw.context_val, asession
                    )
                )
                await update_arm_based_on_outcome(
                    experiment=experiment,
                    draw=draw,
                    rewards=rewards_list,
                    contexts=context_list,
                    treatments=treatments_list,
                    observation_type=ObservationType.AUTO,
                    asession=asession,
                )

                total_failed += 1

            await asession.commit()
            offset += len(draws_batch)

    return total_failed


async def main() -> None:
    """
    Main function to process notifications
    """
    async for asession in get_async_session():
        failed_count = await auto_fail_experiment(asession)
        print(f"Auto-failed experiments: {failed_count} draws")
        break


if __name__ == "__main__":
    asyncio.run(main())
