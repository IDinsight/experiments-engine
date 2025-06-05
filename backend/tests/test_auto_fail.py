import copy
from datetime import datetime, timedelta, timezone
from typing import Generator, Literal, Type

from fastapi.testclient import TestClient
from pytest import FixtureRequest, MonkeyPatch, fixture, mark
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.experiments import models
from backend.jobs.auto_fail import auto_fail_experiment

base_experiment_payload = {
    "name": "Test AUTO FAIL",
    "description": "Test AUTO FAIL description",
    "exp_type": "mab",
    "prior_type": "beta",
    "reward_type": "binary",
    "auto_fail": True,
    "auto_fail_value": 3,
    "auto_fail_unit": "hours",
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
    "contexts": [],
    "clients": [],
}


def fake_datetime(days: int, hours: int) -> Type:
    class mydatetime:
        @classmethod
        def now(cls, *arg: list) -> datetime:
            return datetime.now(timezone.utc) - timedelta(days=days, hours=hours)

    return mydatetime


class TestExperimentAutoFailJob:
    @fixture
    def create_experiment_with_autofail(
        self,
        client: TestClient,
        admin_token: str,
        request: FixtureRequest,
    ) -> Generator:
        auto_fail_value, auto_fail_unit = request.param
        experiment_payload = copy.deepcopy(base_experiment_payload)
        experiment_payload["auto_fail_value"] = auto_fail_value
        experiment_payload["auto_fail_unit"] = auto_fail_unit

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            "/experiment",
            json=experiment_payload,
            headers=headers,
        )
        assert response.status_code == 200
        experiment = response.json()
        yield experiment
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.delete(f"/experiment/id/{experiment['experiment_id']}", headers=headers)

    @mark.parametrize(
        "create_experiment_with_autofail, fail_value, fail_unit, n_observed",
        [
            ((12, "hours"), 12, "hours", 2),
            ((10, "days"), 10, "days", 3),
            ((3, "hours"), 3, "hours", 0),
            ((5, "days"), 5, "days", 0),
        ],
        indirect=["create_experiment_with_autofail"],
    )
    async def test_auto_fail_job(
        self,
        client: TestClient,
        admin_token: str,
        monkeypatch: MonkeyPatch,
        create_experiment_with_autofail: dict,
        fail_value: int,
        fail_unit: Literal["days", "hours"],
        n_observed: int,
        asession: AsyncSession,
        workspace_api_key: str,
    ) -> None:
        draws = []
        headers = {"Authorization": f"Bearer {workspace_api_key}"}
        for i in range(1, 15):
            monkeypatch.setattr(
                models,
                "datetime",
                fake_datetime(
                    days=i if fail_unit == "days" else 0,
                    hours=i if fail_unit == "hours" else 0,
                ),
            )
            response = client.put(
                f"/experiment/{create_experiment_with_autofail['experiment_id']}/draw",
                headers=headers,
            )
            assert response.status_code == 200
            draws.append(response.json()["draw_id"])

            if i >= (15 - n_observed):
                response = client.put(
                    f"/experiment/{create_experiment_with_autofail['experiment_id']}/{draws[-1]}/1",
                    headers=headers,
                )
                print(response.json())
                assert response.status_code == 200

        n_failed = await auto_fail_experiment(asession=asession)

        assert n_failed == (15 - fail_value - n_observed)
