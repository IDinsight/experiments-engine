import copy
import os
from datetime import datetime, timedelta, timezone
from typing import Generator, Literal, Type

from fastapi.testclient import TestClient
from pytest import FixtureRequest, MonkeyPatch, fixture, mark
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.bayes_ab import models as bayes_ab_models
from backend.app.contextual_mab import models as cmab_models
from backend.app.mab import models as mab_models
from backend.jobs.auto_fail import auto_fail_bayes_ab, auto_fail_cmab, auto_fail_mab

base_mab_payload = {
    "name": "Test AUTO FAIL",
    "description": "Test AUTO FAIL description",
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
}

base_cmab_payload = {
    "name": "Test",
    "description": "Test description",
    "prior_type": "normal",
    "reward_type": "real-valued",
    "auto_fail": True,
    "auto_fail_value": 3,
    "auto_fail_unit": "hours",
    "arms": [
        {
            "name": "arm 1",
            "description": "arm 1 description",
            "mu_init": 0,
            "sigma_init": 1,
        },
        {
            "name": "arm 2",
            "description": "arm 2 description",
            "mu_init": 0,
            "sigma_init": 1,
        },
    ],
    "contexts": [
        {
            "name": "Context 1",
            "description": "context 1 description",
            "value_type": "binary",
        },
        {
            "name": "Context 2",
            "description": "context 2 description",
            "value_type": "real-valued",
        },
    ],
    "notifications": {
        "onTrialCompletion": True,
        "numberOfTrials": 2,
        "onDaysElapsed": False,
        "daysElapsed": 3,
        "onPercentBetter": False,
        "percentBetterThreshold": 5,
    },
}

base_ab_payload = {
    "name": "Test",
    "description": "Test description",
    "prior_type": "normal",
    "reward_type": "real-valued",
    "auto_fail": True,
    "auto_fail_value": 3,
    "auto_fail_unit": "hours",
    "arms": [
        {
            "name": "arm 1",
            "description": "arm 1 description",
            "mu_init": 0,
            "sigma_init": 1,
            "is_treatment_arm": True,
        },
        {
            "name": "arm 2",
            "description": "arm 2 description",
            "mu_init": 2,
            "sigma_init": 2,
            "is_treatment_arm": False,
        },
    ],
    "notifications": {
        "onTrialCompletion": True,
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
            return datetime.now(timezone.utc) - timedelta(days=days, hours=hours)

    return mydatetime


class TestMABAutoFailJob:
    @fixture
    def create_mab_with_autofail(
        self,
        client: TestClient,
        admin_token: str,
        request: FixtureRequest,
    ) -> Generator:
        auto_fail_value, auto_fail_unit = request.param
        mab_payload = copy.deepcopy(base_mab_payload)
        mab_payload["auto_fail_value"] = auto_fail_value
        mab_payload["auto_fail_unit"] = auto_fail_unit

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            "/mab",
            json=mab_payload,
            headers=headers,
        )
        assert response.status_code == 200
        mab = response.json()
        yield mab
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.delete(f"/mab/{['experiment_id']}", headers=headers)

    @mark.parametrize(
        "create_mab_with_autofail, fail_value, fail_unit, n_observed",
        [
            ((12, "hours"), 12, "hours", 2),
            ((10, "days"), 10, "days", 3),
            ((3, "hours"), 3, "hours", 0),
            ((5, "days"), 5, "days", 0),
        ],
        indirect=["create_mab_with_autofail"],
    )
    async def test_auto_fail_job(
        self,
        client: TestClient,
        admin_token: str,
        monkeypatch: MonkeyPatch,
        create_mab_with_autofail: dict,
        fail_value: int,
        fail_unit: Literal["days", "hours"],
        n_observed: int,
        asession: AsyncSession,
    ) -> None:
        draws = []
        api_key = os.environ.get("ADMIN_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}"}
        for i in range(1, 15):
            monkeypatch.setattr(
                mab_models,
                "datetime",
                fake_datetime(
                    days=i if fail_unit == "days" else 0,
                    hours=i if fail_unit == "hours" else 0,
                ),
            )
            response = client.get(
                f"/mab/{create_mab_with_autofail['experiment_id']}/draw",
                headers=headers,
            )
            assert response.status_code == 200
            draws.append(response.json()["draw_id"])

            if i >= (15 - n_observed):
                response = client.put(
                    f"/mab/{create_mab_with_autofail['experiment_id']}/{draws[-1]}/1",
                    headers=headers,
                )
                assert response.status_code == 200

        n_failed = await auto_fail_mab(asession=asession)

        assert n_failed == (15 - fail_value - n_observed)


class TestBayesABAutoFailJob:
    @fixture
    def create_bayes_ab_with_autofail(
        self,
        client: TestClient,
        admin_token: str,
        request: FixtureRequest,
    ) -> Generator:
        auto_fail_value, auto_fail_unit = request.param
        ab_payload = copy.deepcopy(base_ab_payload)
        ab_payload["auto_fail_value"] = auto_fail_value
        ab_payload["auto_fail_unit"] = auto_fail_unit

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            "/bayes_ab",
            json=ab_payload,
            headers=headers,
        )
        assert response.status_code == 200
        ab = response.json()
        yield ab
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.delete(f"/bayes_ab/{['experiment_id']}", headers=headers)

    @mark.parametrize(
        "create_bayes_ab_with_autofail, fail_value, fail_unit, n_observed",
        [
            ((12, "hours"), 12, "hours", 2),
            ((10, "days"), 10, "days", 3),
            ((3, "hours"), 3, "hours", 0),
            ((5, "days"), 5, "days", 0),
        ],
        indirect=["create_bayes_ab_with_autofail"],
    )
    async def test_auto_fail_job(
        self,
        client: TestClient,
        admin_token: str,
        monkeypatch: MonkeyPatch,
        create_bayes_ab_with_autofail: dict,
        fail_value: int,
        fail_unit: Literal["days", "hours"],
        n_observed: int,
        asession: AsyncSession,
    ) -> None:
        draws = []
        api_key = os.environ.get("ADMIN_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}"}
        for i in range(1, 15):
            monkeypatch.setattr(
                bayes_ab_models,
                "datetime",
                fake_datetime(
                    days=i if fail_unit == "days" else 0,
                    hours=i if fail_unit == "hours" else 0,
                ),
            )
            response = client.get(
                f"/bayes_ab/{create_bayes_ab_with_autofail['experiment_id']}/draw",
                headers=headers,
            )
            assert response.status_code == 200
            draws.append(response.json()["draw_id"])

            if i >= (15 - n_observed):
                response = client.put(
                    f"/bayes_ab/{create_bayes_ab_with_autofail['experiment_id']}/{draws[-1]}/1",
                    headers=headers,
                )
                assert response.status_code == 200

        n_failed = await auto_fail_bayes_ab(asession=asession)

        assert n_failed == (15 - fail_value - n_observed)


class TestCMABAutoFailJob:
    @fixture
    def create_cmab_with_autofail(
        self,
        client: TestClient,
        admin_token: str,
        request: FixtureRequest,
    ) -> Generator:
        auto_fail_value, auto_fail_unit = request.param
        cmab_payload = copy.deepcopy(base_cmab_payload)
        cmab_payload["auto_fail_value"] = auto_fail_value
        cmab_payload["auto_fail_unit"] = auto_fail_unit

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.post(
            "/contextual_mab",
            json=cmab_payload,
            headers=headers,
        )
        assert response.status_code == 200
        cmab = response.json()
        yield cmab
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.delete(f"/contextual_mab/{['experiment_id']}", headers=headers)

    @mark.parametrize(
        "create_cmab_with_autofail, fail_value, fail_unit, n_observed",
        [
            ((12, "hours"), 12, "hours", 2),
            ((10, "days"), 10, "days", 3),
            ((3, "hours"), 3, "hours", 0),
            ((5, "days"), 5, "days", 0),
        ],
        indirect=["create_cmab_with_autofail"],
    )
    async def test_auto_fail_job(
        self,
        client: TestClient,
        admin_token: str,
        monkeypatch: MonkeyPatch,
        create_cmab_with_autofail: dict,
        fail_value: int,
        fail_unit: Literal["days", "hours"],
        n_observed: int,
        asession: AsyncSession,
    ) -> None:
        draws = []
        api_key = os.environ.get("ADMIN_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}"}
        for i in range(1, 15):
            monkeypatch.setattr(
                cmab_models,
                "datetime",
                fake_datetime(
                    days=i if fail_unit == "days" else 0,
                    hours=i if fail_unit == "hours" else 0,
                ),
            )
            response = client.post(
                f"/contextual_mab/{create_cmab_with_autofail['experiment_id']}/draw",
                json=[
                    {"context_id": 0, "context_value": 0},
                    {"context_id": 1, "context_value": 0},
                ],
                headers=headers,
            )
            assert response.status_code == 200
            draws.append(response.json()["draw_id"])

            if i >= (15 - n_observed):
                response = client.put(
                    f"/contextual_mab/{create_cmab_with_autofail['experiment_id']}/{draws[-1]}/1",
                    headers=headers,
                )
                assert response.status_code == 200

        n_failed = await auto_fail_cmab(asession=asession)

        assert n_failed == (15 - fail_value - n_observed)
