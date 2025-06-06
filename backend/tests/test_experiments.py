import copy
import os
from typing import Generator

from fastapi.testclient import TestClient
from pytest import FixtureRequest, fixture, mark
from sqlalchemy.orm import Session

from backend.app.experiments.models import ArmDB, ExperimentDB, NotificationsDB

mab_beta_binom_payload = {
    "name": "Test",
    "description": "Test description.",
    "exp_type": "mab",
    "prior_type": "beta",
    "reward_type": "binary",
    "arms": [
        {
            "name": "arm 1",
            "description": "arm 1 description.",
            "alpha_init": 5,
            "beta_init": 1,
        },
        {
            "name": "arm 2",
            "description": "arm 2 description.",
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
    "contexts": [],
    "clients": [],
}


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
def clean_experiments(db_session: Session) -> Generator:
    yield
    db_session.query(NotificationsDB).delete()
    db_session.query(ArmDB).delete()
    db_session.query(ExperimentDB).delete()
    db_session.commit()


class TestExperiment:
    @fixture
    def create_experiment_payload(self, request: FixtureRequest) -> dict:
        payload_mab_beta_binom: dict = copy.deepcopy(mab_beta_binom_payload)
        payload_mab_beta_binom["arms"] = list(payload_mab_beta_binom["arms"])

        payload_mab_normal: dict = copy.deepcopy(mab_beta_binom_payload)
        payload_mab_normal["prior_type"] = "normal"
        payload_mab_normal["reward_type"] = "real-valued"
        payload_mab_normal["arms"] = [
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

        if request.param == "base_beta_binom":
            return payload_mab_beta_binom
        if request.param == "base_normal":
            return payload_mab_normal
        if request.param == "one_arm":
            payload_mab_beta_binom["arms"].pop()
            return payload_mab_beta_binom
        if request.param == "no_notifications":
            payload_mab_beta_binom["notifications"]["onTrialCompletion"] = False
            return payload_mab_beta_binom
        if request.param == "invalid_prior":
            payload_mab_beta_binom["prior_type"] = "invalid"
            return payload_mab_beta_binom
        if request.param == "invalid_reward":
            payload_mab_beta_binom["reward_type"] = "invalid"
            return payload_mab_beta_binom
        if request.param == "invalid_alpha":
            payload_mab_beta_binom["arms"][0]["alpha_init"] = -1
            return payload_mab_beta_binom
        if request.param == "invalid_beta":
            payload_mab_beta_binom["arms"][0]["beta_init"] = -1
            return payload_mab_beta_binom
        if request.param == "invalid_combo":
            payload_mab_beta_binom["reward_type"] = "real-valued"
            return payload_mab_beta_binom
        if request.param == "incorrect_params":
            payload_mab_beta_binom["arms"][0].pop("alpha_init")
            return payload_mab_beta_binom
        if request.param == "invalid_sigma":
            payload_mab_normal["arms"][0]["sigma_init"] = 0.0
            return payload_mab_normal
        if request.param == "invalid_context_input":
            payload_mab_beta_binom["contexts"] = [
                {
                    "name": "context 1",
                    "description": "context 1 description",
                    "value_type": "binary",
                }
            ]
            return payload_mab_beta_binom
        else:
            raise ValueError("Invalid parameter")

    @mark.parametrize(
        "create_experiment_payload, expected_response",
        [
            ("base_beta_binom", 200),
            ("base_normal", 200),
            ("one_arm", 422),
            ("no_notifications", 200),
            ("invalid_prior", 422),
            ("invalid_reward", 422),
            ("invalid_alpha", 422),
            ("invalid_beta", 422),
            ("invalid_sigma", 422),
            ("invalid_combo", 422),
            ("incorrect_params", 422),
            ("invalid_context_input", 422),
        ],
        indirect=["create_experiment_payload"],
    )
    def test_create_experiment(
        self,
        create_experiment_payload: dict,
        client: TestClient,
        expected_response: int,
        admin_token: str,
        clean_experiments: None,
    ) -> None:
        response = client.post(
            "/experiment",
            json=create_experiment_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == expected_response

    @fixture
    def create_experiments(
        self,
        client: TestClient,
        admin_token: str,
        request: FixtureRequest,
        create_experiment_payload: dict,
    ) -> Generator:
        experiments = []
        n_experiments = request.param if hasattr(request, "param") else 1
        for _ in range(n_experiments):
            response = client.post(
                "/experiment",
                json=create_experiment_payload,
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            experiments.append(response.json())
        yield experiments
        for experiment in experiments:
            client.delete(
                f"/experiment/id/{experiment['experiment_id']}",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

    @mark.parametrize(
        "create_experiments, create_experiment_payload, n_expected",
        [
            (0, "base_beta_binom", 0),
            (2, "base_beta_binom", 2),
            (5, "base_beta_binom", 5),
        ],
        indirect=["create_experiments", "create_experiment_payload"],
    )
    def test_get_all_experiments(
        self,
        client: TestClient,
        admin_token: str,
        n_expected: int,
        create_experiments: list,
        create_experiment_payload: dict,
    ) -> None:
        response = client.get(
            "/experiment", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()) == n_expected

    @mark.parametrize(
        "create_experiments, create_experiment_payload, expected_response",
        [(0, "base_beta_binom", 404), (2, "base_beta_binom", 200)],
        indirect=["create_experiments", "create_experiment_payload"],
    )
    def test_get_experiment(
        self,
        client: TestClient,
        admin_token: str,
        create_experiments: list,
        create_experiment_payload: dict,
        expected_response: int,
    ) -> None:
        id = create_experiments[0]["experiment_id"] if create_experiments else 999

        response = client.get(
            f"/experiment/id/{id}/", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == expected_response

    @mark.parametrize("create_experiment_payload", ["base_beta_binom"], indirect=True)
    def test_draw_arm_draw_id_provided(
        self,
        client: TestClient,
        create_experiments: list,
        create_experiment_payload: dict,
        workspace_api_key: str,
    ) -> None:
        id = create_experiments[0]["experiment_id"]
        response = client.put(
            f"/experiment/{id}/draw",
            params={"draw_id": "test_draw"},
            headers={"Authorization": f"Bearer {workspace_api_key}"},
        )
        assert response.status_code == 200
        assert response.json()["draw_id"] == "test_draw"

    @mark.parametrize("create_experiment_payload", ["base_beta_binom"], indirect=True)
    def test_draw_arm_no_draw_id_provided(
        self,
        client: TestClient,
        create_experiments: list,
        create_experiment_payload: dict,
        workspace_api_key: str,
    ) -> None:
        id = create_experiments[0]["experiment_id"]
        response = client.put(
            f"/experiment/{id}/draw",
            headers={"Authorization": f"Bearer {workspace_api_key}"},
        )
        assert response.status_code == 200
        assert len(response.json()["draw_id"]) == 36

    @mark.parametrize("create_experiment_payload", ["base_beta_binom"], indirect=True)
    def test_one_outcome_per_draw(
        self,
        client: TestClient,
        create_experiments: list,
        create_experiment_payload: dict,
        workspace_api_key: str,
    ) -> None:
        id = create_experiments[0]["experiment_id"]
        response = client.put(
            f"/experiment/{id}/draw",
            headers={"Authorization": f"Bearer {workspace_api_key}"},
        )
        assert response.status_code == 200
        draw_id = response.json()["draw_id"]

        response = client.put(
            f"/experiment/{id}/{draw_id}/1",
            headers={"Authorization": f"Bearer {workspace_api_key}"},
        )

        assert response.status_code == 200

        response = client.put(
            f"/experiment/{id}/{draw_id}/1",
            headers={"Authorization": f"Bearer {workspace_api_key}"},
        )

        assert response.status_code == 400

    @mark.parametrize(
        "n_draws, create_experiment_payload",
        [(0, "base_beta_binom"), (1, "base_beta_binom"), (5, "base_beta_binom")],
        indirect=["create_experiment_payload"],
    )
    def test_get_rewards(
        self,
        client: TestClient,
        create_experiments: list,
        n_draws: int,
        create_experiment_payload: dict,
        workspace_api_key: str,
    ) -> None:
        id = create_experiments[0]["experiment_id"]

        for _ in range(n_draws):
            response = client.put(
                f"/experiment/{id}/draw",
                headers={"Authorization": f"Bearer {workspace_api_key}"},
            )
            assert response.status_code == 200
            draw_id = response.json()["draw_id"]
            # put outcomes
            response = client.put(
                f"/experiment/{id}/{draw_id}/1",
                headers={"Authorization": f"Bearer {workspace_api_key}"},
            )

        response = client.get(
            f"/experiment/{id}/rewards",
            headers={"Authorization": f"Bearer {workspace_api_key}"},
        )

        assert response.status_code == 200
        assert len(response.json()) == n_draws


class TestNotifications:
    @fixture()
    def create_experiment_payload(self, request: FixtureRequest) -> dict:
        payload: dict = copy.deepcopy(mab_beta_binom_payload)
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
        "create_experiment_payload, expected_response",
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
        indirect=["create_experiment_payload"],
    )
    def test_notifications(
        self,
        client: TestClient,
        admin_token: str,
        create_experiment_payload: dict,
        expected_response: int,
        clean_experiments: None,
    ) -> None:
        response = client.post(
            "/experiment",
            json=create_experiment_payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == expected_response
