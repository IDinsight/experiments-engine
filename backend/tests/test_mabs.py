import copy
import os
from typing import Generator

from fastapi.testclient import TestClient
from pytest import FixtureRequest, fixture, mark
from sqlalchemy.orm import Session

from backend.app.mab.models import MABArmDB, MultiArmedBanditDB
from backend.app.models import NotificationsDB

base_beta_binom_payload = {
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
        "onTrialCompletion": True,
        "numberOfTrials": 2,
        "onDaysElapsed": False,
        "daysElapsed": 3,
        "onPercentBetter": False,
        "percentBetterThreshold": 5,
    },
}

base_normal_payload = base_beta_binom_payload.copy()
base_normal_payload["prior_type"] = "normal"
base_normal_payload["reward_type"] = "real-valued"
base_normal_payload["arms"] = [
    {
        "name": "arm 1",
        "description": "arm 1 description",
        "mu_init": 2,
        "sigma_init": 3,
    },
    {
        "name": "arm 2",
        "description": "arm 2 description",
        "mu_init": 3,
        "sigma_init": 7,
    },
]


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


@fixture
def clean_mabs(db_session: Session) -> Generator:
    yield
    db_session.query(NotificationsDB).delete()
    db_session.query(MABArmDB).delete()
    db_session.query(MultiArmedBanditDB).delete()
    db_session.commit()


class TestMab:
    @fixture
    def create_mab_payload(self, request: FixtureRequest) -> dict:
        payload_beta_binom: dict = copy.deepcopy(base_beta_binom_payload)
        payload_beta_binom["arms"] = list(payload_beta_binom["arms"])

        payload_normal: dict = copy.deepcopy(base_normal_payload)
        payload_normal["arms"] = list(payload_normal["arms"])

        if request.param == "base_beta_binom":
            return payload_beta_binom
        if request.param == "base_normal":
            return payload_normal
        if request.param == "one_arm":
            payload_beta_binom["arms"].pop()
            return payload_beta_binom
        if request.param == "no_notifications":
            payload_beta_binom["notifications"]["onTrialCompletion"] = False
            return payload_beta_binom
        if request.param == "invalid_prior":
            payload_beta_binom["prior_type"] = "invalid"
            return payload_beta_binom
        if request.param == "invalid_reward":
            payload_beta_binom["reward_type"] = "invalid"
            return payload_beta_binom
        if request.param == "invalid_alpha":
            payload_beta_binom["arms"][0]["alpha_init"] = -1
            return payload_beta_binom
        if request.param == "invalid_beta":
            payload_beta_binom["arms"][0]["beta_init"] = -1
            return payload_beta_binom
        if request.param == "invalid_combo_1":
            payload_beta_binom["prior_type"] = "normal"
            return payload_beta_binom
        if request.param == "invalid_combo_2":
            payload_beta_binom["reward_type"] = "continuous"
            return payload_beta_binom
        if request.param == "incorrect_params":
            payload_beta_binom["arms"][0].pop("alpha_init")
            return payload_beta_binom
        if request.param == "invalid_sigma":
            payload_normal["arms"][0]["sigma_init"] = 0.0
            return payload_normal
        else:
            raise ValueError("Invalid parameter")

    @mark.parametrize(
        "create_mab_payload, expected_response",
        [
            ("base_beta_binom", 200),
            ("base_normal", 200),
            ("one_arm", 422),
            ("no_notifications", 200),
            ("invalid_prior", 422),
            ("invalid_reward", 422),
            ("invalid_alpha", 422),
            ("invalid_beta", 422),
            ("invalid_combo_1", 422),
            ("invalid_combo_2", 422),
            ("incorrect_params", 422),
            ("invalid_sigma", 422),
        ],
        indirect=["create_mab_payload"],
    )
    def test_create_mab(
        self,
        create_mab_payload: dict,
        client: TestClient,
        expected_response: int,
        admin_token: str,
        clean_mabs: None,
    ) -> None:
        response = client.post(
            "/mab",
            json=create_mab_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == expected_response

    @fixture
    def create_mabs(
        self, client: TestClient, admin_token: str, request: FixtureRequest
    ) -> Generator:
        mabs = []
        n_mabs = request.param if hasattr(request, "param") else 1
        for _ in range(n_mabs):
            response = client.post(
                "/mab",
                json=base_beta_binom_payload,
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
        "create_mabs, n_expected",
        [(0, 0), (2, 2), (5, 5)],
        indirect=["create_mabs"],
    )
    def test_get_all_mabs(
        self, client: TestClient, admin_token: str, n_expected: int, create_mabs: list
    ) -> None:
        response = client.get(
            "/mab", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == n_expected

    @mark.parametrize(
        "create_mabs, expected_response",
        [(0, 404), (2, 200)],
        indirect=["create_mabs"],
    )
    def test_get_mab(
        self,
        client: TestClient,
        admin_token: str,
        create_mabs: list,
        expected_response: int,
    ) -> None:
        id = create_mabs[0]["experiment_id"] if create_mabs else 999

        response = client.get(
            f"/mab/{id}", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == expected_response

    def test_draw_arm_draw_id_provided(
        self, client: TestClient, create_mabs: list
    ) -> None:
        id = create_mabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        response = client.get(
            f"/mab/{id}/draw",
            params={"draw_id": "test_draw"},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200
        assert response.json()["draw_id"] == "test_draw"

    def test_draw_arm_no_draw_id_provided(
        self, client: TestClient, create_mabs: list
    ) -> None:
        id = create_mabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        response = client.get(
            f"/mab/{id}/draw",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200
        assert len(response.json()["draw_id"]) == 36

    def test_one_outcome_per_draw(self, client: TestClient, create_mabs: list) -> None:
        id = create_mabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        response = client.get(
            f"/mab/{id}/draw",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200
        draw_id = response.json()["draw_id"]

        response = client.put(
            f"/mab/{id}/{draw_id}/1",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        assert response.status_code == 200

        response = client.put(
            f"/mab/{id}/{draw_id}/1",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        assert response.status_code == 400

    @mark.parametrize("n_draws", [0, 1, 5])
    def test_get_outcomes(
        self, client: TestClient, create_mabs: list, n_draws: int
    ) -> None:
        id = create_mabs[0]["experiment_id"]
        api_key = os.environ.get("ADMIN_API_KEY", "")
        id = create_mabs[0]["experiment_id"]

        for _ in range(n_draws):
            response = client.get(
                f"/mab/{id}/draw",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            assert response.status_code == 200
            draw_id = response.json()["draw_id"]
            # put outcomes
            response = client.put(
                f"/mab/{id}/{draw_id}/1",
                headers={"Authorization": f"Bearer {api_key}"},
            )

        response = client.get(
            f"/mab/{id}/outcomes",
            headers={"Authorization": f"Bearer {api_key}"},
        )

        assert response.status_code == 200
        assert len(response.json()) == n_draws


class TestNotifications:
    @fixture()
    def create_mab_payload(self, request: FixtureRequest) -> dict:
        payload: dict = copy.deepcopy(base_beta_binom_payload)
        payload["arms"] = list(payload["arms"])

        match request.param:
            case "base":
                pass
            case "daysElapsed_only":
                payload["notifications"]["onTrialCompletion"] = False
                payload["notifications"]["onDaysElapsed"] = True
            case "trialCompletion_only":
                payload["notifications"]["onTrialCompletion"] = True
            case "percentBetter_only":
                payload["notifications"]["onTrialCompletion"] = False
                payload["notifications"]["onPercentBetter"] = True
            case "all_notifications":
                payload["notifications"]["onDaysElapsed"] = True
                payload["notifications"]["onPercentBetter"] = True
            case "no_notifications":
                payload["notifications"]["onTrialCompletion"] = False
            case "daysElapsed_missing":
                payload["notifications"]["daysElapsed"] = 0
                payload["notifications"]["onDaysElapsed"] = True
            case "trialCompletion_missing":
                payload["notifications"]["numberOfTrials"] = 0
                payload["notifications"]["onTrialCompletion"] = True
            case "percentBetter_missing":
                payload["notifications"]["percentBetterThreshold"] = 0
                payload["notifications"]["onPercentBetter"] = True
            case _:
                raise ValueError("Invalid parameter")

        return payload

    @mark.parametrize(
        "create_mab_payload, expected_response",
        [
            ("base", 200),
            ("daysElapsed_only", 200),
            ("trialCompletion_only", 200),
            ("percentBetter_only", 200),
            ("all_notifications", 200),
            ("no_notifications", 200),
            ("daysElapsed_missing", 422),
            ("trialCompletion_missing", 422),
            ("percentBetter_missing", 422),
        ],
        indirect=["create_mab_payload"],
    )
    def test_notifications(
        self,
        client: TestClient,
        admin_token: str,
        create_mab_payload: dict,
        expected_response: int,
        clean_mabs: None,
    ) -> None:
        response = client.post(
            "/mab",
            json=create_mab_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == expected_response
