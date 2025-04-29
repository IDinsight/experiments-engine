# Create an experiment with auto_fail set to True,
#   auto_fail_value set to 3, auto_fail_unit set to hour
# Create 5 draws with different dates
# Monkeypatch date such that 3 of them expire
# Run auto_fail job
# Check that 3 draws are marked as failed

# Repeat with experiment with auto_fail set to False
# Check that no draws are marked as failed

# Repeat with experiment with auto_fail set to True,
#   auto_fail_value set to 3, auto_fail_unit set to day
# Create 5 draws with different dates
# Monkeypatch date such that 2 of them expire
# Run auto_fail job
# Check that 2 draws are marked as failed

import copy
import os
from datetime import datetime, timedelta, timezone
from typing import Generator, Type

from fastapi.testclient import TestClient
from pytest import FixtureRequest, fixture, mark

base_mab_payload = {
    "name": "Test",
    "description": "Test description",
    "prior_type": "beta",
    "reward_type": "binary",
    "auto_fail": True,
    "auto_fail_value": 3,
    "auto_fail_unit": "hour",
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


def fake_datetime(days: int, hours: int) -> Type:
    class mydatetime:
        @classmethod
        def now(cls, *arg: list) -> datetime:
            return datetime.now(timezone.utc) + timedelta(days=days, hours=hours)

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


class TestAutoFailJob:
    @fixture
    def create_mabs_with_autofail(
        self,
        client: TestClient,
        admin_token: str,
        request: FixtureRequest,
    ) -> Generator:
        mabs = []
        n_mabs, auto_fail_value, auto_fail_unit = request.param
        mab_payload = copy.deepcopy(base_mab_payload)
        mab_payload["auto_fail_value"] = auto_fail_value
        mab_payload["auto_fail_unit"] = auto_fail_unit

        for _ in range(n_mabs):
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = client.post(
                "/mab",
                json=mab_payload,
                headers=headers,
            )
            mabs.append(response.json())
        yield mabs
        for mab in mabs:
            headers = {"Authorization": f"Bearer {admin_token}"}
            client.delete(f"/mab/{mab['experiment_id']}", headers=headers)

    @mark.parametrize(
        "create_mabs_with_autofail",
        [
            (5, 3, "hour"),
            (5, 2, "day"),
            (0, 0, ""),
        ],
        indirect=True,
    )
    def test_auto_fail_job(
        self,
        client: TestClient,
        admin_token: str,
        create_mabs_with_autofail: list,
    ) -> Generator:
        draws = []
        for mab in create_mabs_with_autofail:
            headers = {"Authorization": f"Bearer {admin_token}"}
            for i in range(5):
                draw_payload = {
                    "experiment_id": mab["experiment_id"],
                    "draw_date": (datetime.now(timezone.utc) - timedelta(days=i)),
                }
                response = client.put(
                    "/mab/draw",
                    json=draw_payload,
                    headers=headers,
                )
                draws.append(response.json())
        yield draws
        for draw in draws:
            headers = {"Authorization": f"Bearer {admin_token}"}
            client.delete(f"/mab/draw/{draw['id']}", headers=headers)
