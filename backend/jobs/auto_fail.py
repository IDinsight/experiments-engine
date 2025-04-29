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
from app.mab.models import MABDrawDB, MultiArmedBanditDB
from app.mab.observation import update_based_on_outcome
from app.schemas import ObservationType


async def auto_fail(asession: AsyncSession) -> int:
    """
    Auto fail experiments draws that have not been updated in a certain amount of time.

    Args:
        asession: SQLAlchemy async session

    Returns:
        int: Number of draws automatically failed
    """
    total_failed = 0
    now = datetime.now(tz=timezone.utc)

    # Fetch all required experiments data in one query
    experiment_query = select(MultiArmedBanditDB).where(
        MultiArmedBanditDB.auto_fail.is_(True)
    )
    experiments_result = await asession.execute(experiment_query)
    experiments = experiments_result.scalars().all()

    for experiment in experiments:
        hours_threshold = (
            experiment.auto_fail_value * 24
            if experiment.auto_fail_unit == "days"
            else experiment.auto_fail_value
        )

        cutoff_datetime = now.replace(microsecond=0) - timedelta(hours=hours_threshold)

        draws_query = (
            select(MABDrawDB)
            .join(
                MultiArmedBanditDB,
                MABDrawDB.experiment_id == MultiArmedBanditDB.experiment_id,
            )
            .where(
                MABDrawDB.experiment_id == experiment.experiment_id,
                MABDrawDB.observation_type.is_(None),
                MABDrawDB.draw_datetime_utc <= cutoff_datetime,
            )
            .limit(100)
        )  # Process in smaller batches

        # Paginate through results if there are many draws to avoid memory issues
        offset = 0
        while True:
            batch_query = draws_query.offset(offset)
            draws_result = await asession.execute(batch_query)
            draws_batch = draws_result.scalars().all()

            # Break if no more results
            if not draws_batch:
                break

            for draw in draws_batch:
                draw.observation_type = ObservationType.AUTO

                await update_based_on_outcome(
                    experiment,
                    draw,
                    0.0,
                    asession,
                    ObservationType.AUTO,
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
        failed_count = await auto_fail(asession)
        print(f"Auto-failed {failed_count} draws")
        break


if __name__ == "__main__":
    asyncio.run(main())
