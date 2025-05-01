import asyncio
import copy
import os
from datetime import datetime, timedelta, timezone
from typing import Generator, Type

from fastapi.testclient import TestClient
from pytest import FixtureRequest, MonkeyPatch, fixture, mark
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend import create_notifications
from backend.create_notifications import process_notifications

base_mab_payload = {
    "name": "Test",
    "description": "Test description",
    "prior_type": "beta",
    "reward_type": "binary",
    "arms": [
        {
            "name": "arm 1",
            "description": "arm 1 description",
            "alpha_init": 5,
            "beta_init": 1,
        },
        {
            "name": "arm 2",
            "description": "arm 2 description",
            "alpha_init": 1,
            "beta_init": 4,
        },
    ],
    "notifications": {
        "onTrialCompletion": False,
        "numberOfTrials": 2,
        "onDaysElapsed": False,
        "daysElapsed": 3,
        "onPercentBetter": False,
        "percentBetterThreshold": 5,
    },
}


def fake_datetime(days: int) -> Type:
    class mydatetime:
        @classmethod
        def now(cls, *arg: list) -> datetime:
            return datetime.now(timezone.utc) + timedelta(days=days)

    return mydatetime


@fixture
def admin_token(client: TestClient) -> str:
    response = client.post(
        "/login",
        data={
            "username": os.environ.get("ADMIN_USERNAME", ""),
            "password": os.environ.get("ADMIN_PASSWORD", ""),
        },
    )
    token = response.json()["access_token"]
    return token


class TestNotificationsJob:
    @fixture
    def create_mabs_days_elapsed(
        self, client: TestClient, admin_token: str, request: FixtureRequest
    ) -> Generator:
        mabs = []
        n_mabs, days_elapsed = request.param

        payload: dict = copy.deepcopy(base_mab_payload)
        payload["notifications"]["onDaysElapsed"] = True
        payload["notifications"]["daysElapsed"] = days_elapsed

        for _ in range(n_mabs):
            response = client.post(
                "/mab",
                json=payload,
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            mabs.append(response.json())
        yield mabs
        for mab in mabs:
            client.delete(
                f"/mab/{mab['experiment_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

    @fixture
    def create_mabs_trials_run(
        self, client: TestClient, admin_token: str, request: FixtureRequest
    ) -> Generator:
        mabs = []
        n_mabs, n_trials = request.param

        payload: dict = copy.deepcopy(base_mab_payload)
        payload["notifications"]["onTrialCompletion"] = True
        payload["notifications"]["numberOfTrials"] = n_trials

        for _ in range(n_mabs):
            response = client.post(
                "/mab",
                json=payload,
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            mabs.append(response.json())
        yield mabs
        for mab in mabs:
            client.delete(
                f"/mab/{mab['experiment_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

    @mark.parametrize(
        "create_mabs_days_elapsed, days_elapsed",
        [((3, 4), 4), ((4, 62), 64), ((3, 40), 40)],
        indirect=["create_mabs_days_elapsed"],
    )
    async def test_days_elapsed_notification(
        self,
        client: TestClient,
        admin_token: str,
        create_mabs_days_elapsed: list[dict],
        db_session: Session,
        days_elapsed: int,
        monkeypatch: MonkeyPatch,
        asession: AsyncSession,
    ) -> None:
        monkeypatch.setattr(
            create_notifications,
            "datetime",
            fake_datetime(days_elapsed),
        )
        n_processed = await process_notifications(asession)
        assert n_processed == len(create_mabs_days_elapsed)

    @mark.parametrize(
        "create_mabs_days_elapsed, days_elapsed",
        [((3, 4), 3), ((4, 62), 50), ((3, 40), 0)],
        indirect=["create_mabs_days_elapsed"],
    )
    async def test_days_elapsed_notification_not_sent(
        self,
        client: TestClient,
        admin_token: str,
        create_mabs_days_elapsed: list[dict],
        db_session: Session,
        days_elapsed: int,
        monkeypatch: MonkeyPatch,
        asession: AsyncSession,
    ) -> None:
        monkeypatch.setattr(
            create_notifications,
            "datetime",
            fake_datetime(days_elapsed),
        )
        n_processed = await process_notifications(asession)
        assert n_processed == 0

    @mark.parametrize(
        "create_mabs_trials_run, n_trials",
        [((3, 4), 4), ((4, 62), 64), ((3, 40), 40)],
        indirect=["create_mabs_trials_run"],
    )
    async def test_trials_run_notification(
        self,
        client: TestClient,
        admin_token: str,
        n_trials: int,
        create_mabs_trials_run: list[dict],
        db_session: Session,
        asession: AsyncSession,
    ) -> None:
        n_processed = await process_notifications(asession)
        assert n_processed == 0
        api_key = os.environ.get("ADMIN_API_KEY", "")
        for mab in create_mabs_trials_run:
            for i in range(n_trials):
                draw_id = f"draw_{i}_{mab['experiment_id']}"
                response = client.get(
                    f"/mab/{mab['experiment_id']}/draw",
                    params={"draw_id": draw_id},
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                assert response.status_code == 200
                assert response.json()["draw_id"] == draw_id

                response = client.put(
                    f"/mab/{mab['experiment_id']}/{draw_id}/1",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                assert response.status_code == 200
        n_processed = await process_notifications(asession)
        await asyncio.sleep(0.1)
        assert n_processed == len(create_mabs_trials_run)
